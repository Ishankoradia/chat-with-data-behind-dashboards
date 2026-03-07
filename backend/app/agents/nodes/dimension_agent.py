"""
Dimension Agent - handles dimension and breakdown queries
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.types import AgentState
from app.core.config import settings
from app.tools.database_tool import DatabaseTool
from app.tools.dbt_tool import DBTTool


async def handle_dimension_query(state: AgentState) -> Dict[str, Any]:
    """
    Handle queries about dimensions, breakdowns, and categorical data
    """
    user_query = state["user_query"]
    dashboard_context = state.get("dashboard_context")
    needs_db_query = state.get("needs_database_query", False)
    
    response = ""
    query_result = None
    sql_query = None
    
    try:
        if needs_db_query:
            # Use DBT semantic layer if available
            if state.get("dbt_dimensions"):
                dbt_tool = DBTTool()
                semantic_result = await dbt_tool.query_dimensions(
                    query=user_query,
                    available_dimensions=state["dbt_dimensions"],
                    dashboard_context=dashboard_context,
                )
                if semantic_result:
                    query_result = semantic_result
                    sql_query = semantic_result.get("sql", "")
            
            # Fallback to direct database query
            if not query_result:
                db_tool = DatabaseTool()
                query_result = await db_tool.execute_dimension_query(
                    query=user_query,
                    dashboard_context=dashboard_context,
                )
                sql_query = query_result.get("sql", "") if query_result else ""
        
        # Generate natural language response
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        system_prompt = """
        You are a data analyst assistant specializing in dimensional analysis and breakdowns.
        
        Respond to the user's dimension-related query in a clear, analytical way.
        If query results are provided, interpret the categorical data and identify patterns.
        Focus on breakdowns, distributions, and segment insights.
        
        Keep responses concise but informative.
        """
        
        context = f"User Query: {user_query}\n"
        if query_result:
            context += f"Query Result: {query_result}\n"
        if dashboard_context:
            datasource = dashboard_context.get("datasource")
            datasets = dashboard_context.get("datasets", [])
            text_context = dashboard_context.get("text_context")
            
            context += f"Database: {datasource.name if datasource else 'Unknown'}\n"
            context += f"Available tables: {', '.join([d.display_name for d in datasets])}\n"
            if text_context:
                context += f"Business Context: {text_context}\n"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await llm.ainvoke(messages)
        
        return {
            "final_response": response.content,
            "query_result": query_result,
            "sql_query": sql_query,
        }
        
    except Exception as e:
        print(f"Error in dimension agent: {e}")
        return {
            "final_response": f"I encountered an error while processing your dimension query: {str(e)}",
            "query_result": None,
            "sql_query": None,
        }