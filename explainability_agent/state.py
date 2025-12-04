from typing import TypedDict, List, Dict, Any, Optional, Union

class AnalysisState(TypedDict):
    """
    Represents the state of our analysis graph.
    """
    initial_prompt: str
    merchant_id: str
    target_month: str
    
    # The dimensions we can potentially investigate
    potential_dimensions: List[str]
    
    # The dimensions and filters for the *next* query
    # Example: dimensions=['CARD_SCHEME'], filters={'PSP': 'stripe'}
    query_plan: Dict[str, Any]

    # A log of all actions taken and insights gained
    investigation_log: List[str]

    # The final, user-facing report
    final_report: Optional[str]
    
    # Mode of operation (mock or prod)
    mode: str
    
    # Verbose logging flag
    verbose: bool
