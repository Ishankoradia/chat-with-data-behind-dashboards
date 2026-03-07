"""
Enhanced agent state types for LangGraph orchestration
"""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from app.models.enhanced_query import (
    EnhancedQueryAnalysis, 
    SqlQueryResult, 
    ThinkingProcess,
    DataInsights,
    ExecutionPlan
)


class AgentState(TypedDict):
    """Enhanced shared state across all agents"""
    
    # Chat context
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    user_id: str
    datasource_id: str
    dashboard_context: Optional[Dict[str, Any]]
    
    # Enhanced query analysis
    enhanced_analysis: Optional[EnhancedQueryAnalysis]
    execution_plan: Optional[ExecutionPlan]
    
    # SQL execution
    generated_sql: Optional[str]
    sql_query_result: Optional[SqlQueryResult]
    
    # Insights generation
    generated_insights: Optional[DataInsights]
    
    # Reasoning and transparency
    thinking_process: Optional[ThinkingProcess]
    current_step: Optional[str]
    step_details: Optional[Dict[str, Any]]
    
    # Results
    final_response: Optional[str]
    
    # Error handling and retry
    error: Optional[str]
    retry_count: Optional[int]
    should_retry: Optional[bool]
    execution_success: Optional[bool]
    results_valid: Optional[bool]