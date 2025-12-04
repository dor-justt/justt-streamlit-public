import pandas as pd
import snowflake.connector
import base64
import pandas as pd
from snowflake import connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import List, Dict, Any, Optional, Dict
from explainability_agent.config import (
    SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT
)

def _to_pkcs8_der(pem_or_b64: str, passphrase: str) -> bytes:
    """
    Convert PEM (multi-line or with literal '\\n') or base64 string into PKCS#8 DER bytes.
    Snowflake expects PKCS#8 DER and not an encrypted PEM.
    """
    if not pem_or_b64:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY is missing")
    if not passphrase:
        raise ValueError("SNOWFLAKE_PASSPHRASE is missing")

    # Normalize: if it looks like PEM, ensure real newlines; else try base64
    if "BEGIN" in pem_or_b64:
        raw_pem = pem_or_b64.replace("\\n", "\n").encode()
    else:
        try:
            raw_pem = base64.b64decode(pem_or_b64)
        except Exception:
            raw_pem = pem_or_b64.replace("\\n", "\n").encode()

    private_key = serialization.load_pem_private_key(
        raw_pem, password=passphrase.encode(), backend=default_backend()
    )

    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

# Global registry to store connector instances
# This keeps the connector outside of the serialized state
_connector_registry: Dict[str, 'SnowflakeConnector'] = {}

def get_connector(merchant_id: str) -> 'SnowflakeConnector':
    """
    Get or create a connector for the specified merchant_id.
    This function provides access to the connector without storing it in the state.
    """
    if merchant_id not in _connector_registry:
        _connector_registry[merchant_id] = SnowflakeConnector(merchant_id)
    return _connector_registry[merchant_id]

def close_all_connections():
    """
    Close all open Snowflake connections.
    """
    for connector in _connector_registry.values():
        connector.close()
    _connector_registry.clear()

class SnowflakeConnector:
    """
    A class to manage Snowflake connection and query execution.
    """
    def __init__(self, merchant_id: str):
        """
        Initialize the Snowflake connection.
        """
        self.merchant_id = merchant_id
        
        # Connect to Snowflake
        self.conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT
        )
        private_key_bytes = _to_pkcs8_der(
            pem_or_b64=self._config.SNOWFLAKE_PRIVATE_KEY,
            passphrase=self._config.SNOWFLAKE_PASSPHRASE,
        )
        self.connection: connector.connection.SnowflakeConnection = connector.connect(
            user=self._config.SNOWFLAKE_USER,
            account=self._config.SNOWFLAKE_ACCT,
            private_key=private_key_bytes,
        )
        print(f"✅ Connected to Snowflake as {SNOWFLAKE_USER}")
    
    def close(self):
        """
        Close the Snowflake connection.
        """
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print(f"✅ Snowflake connection closed for merchant {self.merchant_id}")
    
    def __del__(self):
        """
        Close the connection when the object is destroyed.
        """
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("✅ Snowflake connection closed")
    
    def build_and_run_query(self, dimensions: List[str], filters: Dict[str, Any] = None, verbose: bool = False) -> pd.DataFrame:
        """
        Builds and executes a Snowflake query with the specified dimensions and filters.
        Always enforces a filter on merchant_id to ensure data isolation.
        
        Args:
            dimensions: List of dimensions to group by
            filters: Additional filters to apply
            verbose: Whether to print the query and results
            
        Returns:
            DataFrame with the query results
        """
        dimensions_str = '' if len(dimensions) == 0 else ','+', '.join(dimensions)
        
        # Build filter conditions
        filter_conditions = []
        if filters:
            for key, value in filters.items():
                # Handle string values with quotes, others without
                if isinstance(value, str):
                    filter_conditions.append(f"AND {key}='{value}'")
                else:
                    filter_conditions.append(f"AND {key}={value}")
        
        filters_str = '\n                '.join(filter_conditions)
        
        query = f"""
        WITH monthly_aggregates AS (
            SELECT 
                POSTING_MONTH_TRUNC {dimensions_str},
                SUM(CASE WHEN PSP_STATUS in ('lost', 'won') THEN 1 ELSE 0 END) AS FINALIZED_CNT,
                SUM(CASE WHEN PSP_STATUS in ('won') THEN AMOUNT_WON ELSE 0 END) AS WON_AMOUNT,
                SUM(AMOUNT_NOT_PENDING) AS FINALIZED_TOTAL_AMOUNT
            FROM conformed.conformed_chargebacks_main_dataset
            WHERE POSTING_DATE_TRUNC >= DATEADD(MONTH, -12, DATE_TRUNC('MONTH', CURRENT_DATE())) 
                AND HANDLED = 1 
                AND merchant_id='{self.merchant_id}'
                {filters_str}
            GROUP BY POSTING_MONTH_TRUNC {dimensions_str}
        )
        SELECT 
            POSTING_MONTH_TRUNC {dimensions_str},
            FINALIZED_CNT,
            WON_AMOUNT,
            FINALIZED_TOTAL_AMOUNT,
            WON_AMOUNT / (CASE WHEN FINALIZED_TOTAL_AMOUNT > 0 THEN FINALIZED_TOTAL_AMOUNT ELSE 1 END) AS RECOVERY_RATE,
            FINALIZED_TOTAL_AMOUNT / SUM(FINALIZED_TOTAL_AMOUNT) OVER (PARTITION BY POSTING_MONTH_TRUNC) AS PERCENTAGE_FROM_THAT_MONTH
        FROM monthly_aggregates
        HAVING FINALIZED_CNT >= 30 
        QUALIFY PERCENTAGE_FROM_THAT_MONTH >= 0.05
        ORDER BY 1
        """
        
        # Print query if verbose
        if verbose:
            print("\n" + "="*80)
            print("🔍 SNOWFLAKE QUERY:")
            print("="*80)
            print(query)
            print("="*80)
        
        # Execute the query
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            
            # Get column names from cursor description
            columns = [col[0] for col in cursor.description]
            
            # Fetch all results and convert to DataFrame
            data = cursor.fetchall()
            cursor.close()
            
            df = pd.DataFrame(data, columns=columns)
            
            # Print results if verbose
            if verbose:
                print(f"\n📊 QUERY RESULTS ({len(df)} rows):")
                print("="*80)
                if not df.empty:
                    print(df.to_string(index=False))
                else:
                    print("No results returned")
                print("="*80)
            
            return df
            
        except Exception as e:
            print(f"❌ Error executing Snowflake query: {e}")
            if verbose:
                print(f"Query that failed: {query}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['POSTING_MONTH_TRUNC', 'FINALIZED_CNT', 'WON_AMOUNT', 'FINALIZED_TOTAL_AMOUNT', 'RECOVERY_RATE', 'PERCENTAGE_FROM_THAT_MONTH'])
