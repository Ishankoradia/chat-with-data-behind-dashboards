"""
Supervisor node - routes queries to appropriate specialized agents
"""
from typing import Dict, Any
from app.agents.types import AgentState


def supervisor_routing(state: AgentState) -> Dict[str, Any]:
    """
    Route query to appropriate agent based on analysis
    
    Returns updated state (LangGraph nodes must return dicts)
    """
    query_type = state.get("query_type", "general")
    
    # Log routing decision
    print(f"Supervisor routing query to: {query_type}_agent")
    print(f"Reasoning: {state.get('reasoning', 'No reasoning provided')}")
    
    # Return state dict (LangGraph requirement)
    return {
        "routing_decision": f"Routed to {query_type}_agent",
    }