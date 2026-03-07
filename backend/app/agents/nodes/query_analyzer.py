"""
Query analysis node - determines query type and intent
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents.types import AgentState
from app.core.config import settings


class QueryAnalysis(BaseModel):
    """Structured output for query analysis"""
    query_type: str = Field(description="Type of query: 'metric', 'dimension', 'filter', or 'general'")
    needs_database_query: bool = Field(description="Whether this query requires database access")
    reasoning: str = Field(description="Explanation of the analysis decision")


async def analyze_query(state: AgentState) -> Dict[str, Any]:
    """
    Analyze user query to determine intent and routing
    """
    user_query = state["user_query"]
    dashboard_context = state.get("dashboard_context")
    dbt_metrics = state.get("dbt_metrics", [])
    dbt_dimensions = state.get("dbt_dimensions", [])
    
    # Prepare context for LLM
    context_info = ""
    if dashboard_context:
        datasource = dashboard_context.get("datasource")
        datasets = dashboard_context.get("datasets", [])
        text_context = dashboard_context.get("text_context")
        
        context_info += f"Database: {datasource.name if datasource else 'Unknown'}\n"
        context_info += f"Available tables: {', '.join([d.display_name for d in datasets])}\n"
        if text_context:
            context_info += f"Business Context: {text_context}\n"
    
    if dbt_metrics:
        metric_names = [m.get("name", "") for m in dbt_metrics]
        context_info += f"DBT Metrics: {', '.join(metric_names)}\n"
    
    if dbt_dimensions:
        dimension_names = [d.get("name", "") for d in dbt_dimensions]
        context_info += f"DBT Dimensions: {', '.join(dimension_names)}\n"
    
    system_prompt = f"""
    You are a query analyzer for dashboard conversations. Analyze the user's query and determine:

    1. Query Type:
       - "metric": User is asking about specific metrics, KPIs, or numerical measures
       - "dimension": User is asking about breakdowns, categories, or groupings
       - "filter": User wants to filter or slice existing dashboard data
       - "general": General questions about the dashboard or explanatory queries

    2. Whether the query requires database access (needs_database_query):
       - True: Query needs fresh data from database
       - False: Can be answered from existing dashboard context

    Context:
    {context_info}
    
    Analyze the query and provide structured output.
    """
    
    llm = ChatOpenAI(
        model=settings.DEFAULT_LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        openai_api_key=settings.OPENAI_API_KEY,
    ).with_structured_output(QueryAnalysis)
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {user_query}")
        ]
        
        analysis = await llm.ainvoke(messages)
        
        return {
            "query_type": analysis.query_type,
            "needs_database_query": analysis.needs_database_query,
            "reasoning": analysis.reasoning,
        }
        
    except Exception as e:
        print(f"Error in query analysis: {e}")
        # Default fallback
        return {
            "query_type": "general",
            "needs_database_query": False,
            "reasoning": f"Error in analysis: {str(e)}",
        }