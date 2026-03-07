"""
Result Formatter - final response formatting and cleanup
"""
from typing import Dict, Any
from app.agents.types import AgentState


def format_final_response(state: AgentState) -> Dict[str, Any]:
    """
    Format the final response and ensure all required fields are present
    """
    final_response = state.get("final_response", "I'm sorry, I couldn't process your request.")
    query_result = state.get("query_result")
    sql_query = state.get("sql_query")
    
    # Add query execution info if available
    if sql_query and query_result:
        execution_info = f"\n\n*Query executed: {sql_query[:100]}{'...' if len(sql_query) > 100 else ''}*"
        final_response += execution_info
    
    return {
        "final_response": final_response,
        "query_result": query_result,
        "sql_query": sql_query,
    }