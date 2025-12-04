import uuid
import argparse
import atexit
from explainability_agent.graph import app
from explainability_agent.state import AnalysisState
from explainability_agent.config import MODE
from typing import Optional

# Conditionally import the Snowflake connector utilities
try:
    from explainability_agent.snowflake_connector import get_connector, close_all_connections
    # Register the close_all_connections function to run at exit
    atexit.register(close_all_connections)
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    # This will happen if snowflake-connector-python is not installed
    SNOWFLAKE_AVAILABLE = False


def run_analysis(
    prompt: str, 
    merchant_id: str, 
    target_month: str,
    mode: str = "mock",
    verbose: bool = False
):
    """
    Main function to run the chargeback analysis agent.
    
    Args:
        prompt: The user's question about the merchant's recovery rate
        merchant_id: The ID of the merchant to analyze
        target_month: The month to focus the analysis on (e.g., "June 2025")
        mode: The mode to run in ("mock" or "prod")
        verbose: Whether to print verbose output during execution
    """
    # Target month is now required, so no need to extract it from the prompt
    
    print(f"🚀 Starting Analysis for {merchant_id}, Month: {target_month}...")
    print(f"🔧 Running in {mode.upper()} mode")

    # Initialize Snowflake connector if in prod mode
    if mode == "prod":
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError("snowflake-connector-python package is required for prod mode. "
                             "Please install it with: pip install 'snowflake-connector-python[pandas]'")
        
        print(f"🔌 Initializing Snowflake connection for merchant: {merchant_id}")
        # This will create the connector in the registry if it doesn't exist
        get_connector(merchant_id=merchant_id)

    # Define the initial state of the investigation
    initial_state: AnalysisState = {
        "initial_prompt": prompt,
        "merchant_id": merchant_id,
        "target_month": target_month,
        "potential_dimensions": [
            "CARD_SCHEME", "PSP", "INTEGRATION_NAME", 
            "PAYMENT_METHOD", "REASON_GROUP"
        ],
        "query_plan": {
            "dimensions": ["CARD_SCHEME"],  # Start with the broadest dimension
            "filters": {}
        },
        "investigation_log": [f"Initial Task: Find the root cause for low recovery rate for {merchant_id} in {target_month}."],
        "final_report": None,
        "mode": mode,
        "verbose": verbose
    }
    
    # A unique identifier for the conversation
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # Stream the events from the graph execution
    final_state = None
    for event in app.stream(initial_state, config=config):
        if "__end__" not in event:
            # Print each step's output if verbose logging is enabled
            if verbose:
                print(event)
                print("---")
    
    # The final state is the output of the last node that ran
    final_state = app.get_state(config)
    
    print("\n" + "="*50)
    print("✅ Analysis Complete.")
    print("="*50 + "\n")
    print(final_state.values['final_report'])


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Chargeback Recovery Rate Explainability Agent")
    
    parser.add_argument(
        "--merchant-id", 
        type=str, 
        required=True,
        help="The merchant ID to analyze (e.g., 'doordash', 'klarna')"
    )
    
    parser.add_argument(
        "--prompt", 
        type=str, 
        default="Why did the recovery rate drop recently?",
        help="The question to analyze (e.g., 'Why did the recovery rate drop in June 2023?')"
    )
    
    parser.add_argument(
        "--target-month", 
        type=str, 
        required=True,
        help="The specific month to analyze (e.g., 'June 2023')."
    )
    
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["mock", "prod"], 
        default=MODE,
        help="The mode to run in ('mock' for simulated data, 'prod' for real Snowflake queries)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output during execution"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_analysis(
        prompt=args.prompt,
        merchant_id=args.merchant_id,
        target_month=args.target_month,
        mode=args.mode,
        verbose=args.verbose
    )