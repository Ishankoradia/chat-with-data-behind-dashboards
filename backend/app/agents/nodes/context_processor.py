"""
Dashboard context processing node
"""
import logging
from typing import Dict, Any
from app.agents.types import AgentState
from app.core.config import settings
from app.agents.utils import create_node_logger

# Configure logger for this node
logger = create_node_logger("context_processor")


def process_dashboard_context(state: AgentState) -> Dict[str, Any]:
    """
    Process dashboard context and retrieve relevant information
    
    In the new session-based system, the dashboard context is already
    loaded and passed in the state by the orchestrator.
    """
    logger.debug("Context processor executing")
    try:
        # Dashboard context is already provided by the orchestrator
        dashboard_context = state.get("dashboard_context")
        
        # Skip DBT calls for now to test sync vs async issue
        dbt_metrics = None
        dbt_dimensions = None
        
        logger.debug("Context processor completed successfully")
        logger.debug(f"Context processor returning state keys: {list({'dashboard_context': dashboard_context, 'dbt_metrics': dbt_metrics, 'dbt_dimensions': dbt_dimensions}.keys())}")
        return {
            "dashboard_context": dashboard_context,
            "dbt_metrics": dbt_metrics,
            "dbt_dimensions": dbt_dimensions,
        }
        
    except Exception as e:
        # Log error and continue with minimal context
        print(f"Error processing dashboard context: {e}")
        return {
            "dashboard_context": state.get("dashboard_context"),
            "dbt_metrics": None,
            "dbt_dimensions": None,
        }