import pandas as pd
from typing import List, Dict, Any, Optional
import inspect
from explainability_agent.config import MODE
from explainability_agent.snowflake_connector import get_connector

def _mock_snowflake_query(dimensions: List[str], filters: Dict[str, Any] = None, verbose: bool = False) -> pd.DataFrame:
    """
    Mocks a Snowflake query to return realistic-looking chargeback data.
    """
    if verbose:
        print("\n" + "="*80)
        print("🔍 MOCK QUERY:")
        print("="*80)
        print(f"Dimensions: {dimensions}")
        print(f"Filters: {filters}")
        print("="*80)
    # Base data representing all chargebacks for a month
    data = {
        'INTEGRATION_NAME': ['stripe_us', 'stripe_us', 'stripe_us', 'stripe_eu', 'adyen_us', 'adyen_us'],
        'CARD_SCHEME': ['visa', 'mastercard', 'amex', 'visa', 'visa', 'mastercard'],
        'PSP': ['stripe', 'stripe', 'stripe', 'adyen', 'adyen', 'adyen'],
        'PAYMENT_METHOD': ['credit', 'credit', 'credit', 'debit', 'credit', 'debit'],
        'REASON_GROUP': ['fraud', 'service', 'product', 'fraud', 'service', 'product'],
        'PSP_STATUS': ['won', 'lost', 'lost', 'won', 'lost', 'won'],
        'AMOUNT_WON': [100, 0, 0, 150, 0, 50],
        'AMOUNT_NOT_PENDING': [100, 200, 50, 150, 300, 50],
        'POSTING_MONTH_TRUNC': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01']
    }
    # Multiply the data to get more volume
    df = pd.DataFrame(data)
    df = pd.concat([df] * 50, ignore_index=True)

    # Apply filters if any (for drill-downs)
    if filters:
        for key, value in filters.items():
            df = df[df[key] == value]

    if not dimensions:
        return df # Should not happen in our flow

    # Perform the aggregation logic from the original SQL query
    def agg_logic(x):
        finalized_cnt = x[x['PSP_STATUS'].isin(['won', 'lost'])].shape[0]
        won_amount = x[x['PSP_STATUS'] == 'won']['AMOUNT_WON'].sum()
        finalized_total_amount = x['AMOUNT_NOT_PENDING'].sum()
        
        # Avoid division by zero
        recovery_rate = won_amount / finalized_total_amount if finalized_total_amount > 0 else 0

        names = {
            'FINALIZED_CNT': finalized_cnt,
            'WON_AMOUNT': won_amount,
            'FINALIZED_TOTAL_AMOUNT': finalized_total_amount,
            'RECOVERY_RATE': recovery_rate
        }
        return pd.Series(names)

    # Make sure POSTING_MONTH_TRUNC is always included in dimensions
    if 'POSTING_MONTH_TRUNC' not in dimensions:
        all_dimensions = ['POSTING_MONTH_TRUNC'] + dimensions
    else:
        all_dimensions = dimensions.copy()
        
    grouped = df.groupby(all_dimensions).apply(agg_logic).reset_index()

    # Calculate percentage from total for that month
    total_month_amount = grouped.groupby('POSTING_MONTH_TRUNC')['FINALIZED_TOTAL_AMOUNT'].transform('sum')
    grouped['PERCENTAGE_FROM_THAT_MONTH'] = grouped['FINALIZED_TOTAL_AMOUNT'] / total_month_amount

    # Filter for significant segments as per the HAVING clause
    result = grouped[
        (grouped['FINALIZED_CNT'] >= 30) & 
        (grouped['PERCENTAGE_FROM_THAT_MONTH'] >= 0.05)
    ].sort_values(by=['POSTING_MONTH_TRUNC', 'PERCENTAGE_FROM_THAT_MONTH'], ascending=[True, False])
    
    if verbose:
        print(f"\n📊 MOCK QUERY RESULTS ({len(result)} rows):")
        print("="*80)
        if not result.empty:
            print(result.to_string(index=False))
        else:
            print("No results returned")
        print("="*80)
    
    return result.round(2)


def run_chargeback_analysis_query(dimensions: List[str], filters: Dict[str, Any] = None, state: Optional[dict] = None) -> str:
    """
    The tool that the agent can call.
    It runs a query (either mocked or real) and returns the results as a formatted string.
    
    Args:
        dimensions: List of dimensions to group by
        filters: Additional filters to apply
        state: The current state of the agent (passed automatically by LangGraph)
    
    Returns:
        Formatted string with query results
    """
    print(f"--- ⚙️ Executing Tool: Querying with Dimensions={dimensions}, Filters={filters} ---")
    
    # Determine if we're in mock or prod mode
    mode = MODE
    if state is not None and 'mode' in state:
        mode = state['mode']
    

    
    # Determine if verbose mode is enabled
    verbose = False
    if state is not None and 'verbose' in state:
        verbose = state['verbose']
    
    try:
        # Execute the appropriate query based on mode
        if mode == "mock":
            print("📊 Running mock query...")
            results_df = _mock_snowflake_query(dimensions, filters, verbose)
        else:  # prod mode
            print("🔌 Running Snowflake query...")
            # Get the merchant_id from the state
            if state is None or 'merchant_id' not in state:
                raise ValueError("merchant_id not found in state. Make sure to initialize it in prod mode.")
            
            # Get the connector from the registry using the merchant_id
            merchant_id = state['merchant_id']
            connector = get_connector(merchant_id)
            results_df = connector.build_and_run_query(dimensions, filters, verbose)
        
        # Format and return results
        if results_df.empty:
            return "Query returned no results for a segment with significant volume. This might be the end of the drill-down path."
        return results_df.to_markdown(index=False)
    except Exception as e:
        return f"An error occurred during query execution: {e}"