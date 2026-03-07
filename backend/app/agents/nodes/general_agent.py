"""
General Agent - handles general dashboard questions and explanations
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.types import AgentState
from app.core.config import settings
from app.agents.utils import create_node_logger

# Configure logger for this node
logger = create_node_logger("general_agent")


def handle_general_query(state: AgentState) -> Dict[str, Any]:
    """
    Handle general questions about dashboards and explanatory queries
    """
    logger.debug("General agent executing")
    user_query = state["user_query"]
    dashboard_context = state.get("dashboard_context")
    
    try:
        # Generate contextual response using LLM
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Build context information
        context_info = ""
        if dashboard_context:
            datasource = dashboard_context.get("datasource")
            datasets = dashboard_context.get("datasets", [])
            text_context = dashboard_context.get("text_context")
            json_context = dashboard_context.get("json_context")
            additional_instructions = dashboard_context.get("additional_instructions")
            
            # Database information
            if datasource:
                context_info += f"Database: {datasource.name} ({datasource.database})\n"
                context_info += f"Database type: {datasource.type}\n"
                context_info += f"Host: {datasource.host}:{datasource.port}\n\n"
            
            # Tables information
            if datasets:
                context_info += f"Selected Tables ({len(datasets)} total):\n"
                for dataset in datasets:
                    # Handle both object and dict formats
                    if hasattr(dataset, 'table_name'):
                        table_name = f"{dataset.table_schema}.{dataset.table_name}"
                        display_name = getattr(dataset, 'alias', None) or dataset.table_name
                    else:
                        table_name = f"{dataset.get('table_schema', 'unknown')}.{dataset.get('table_name', 'unknown')}"
                        display_name = dataset.get('alias') or dataset.get('table_name', 'unknown')
                    
                    context_info += f"  - {display_name} ({table_name})\n"
                context_info += "\n"
            else:
                context_info += "No tables selected yet.\n\n"
            
            # Business context
            if text_context:
                context_info += f"Business Context:\n{text_context}\n\n"
            
            # Structured context
            if json_context:
                context_info += f"Structured Metadata:\n{json_context}\n\n"
            
            # Additional instructions
            if additional_instructions:
                context_info += f"Additional Instructions:\n{additional_instructions}\n\n"
        
        system_prompt = f"""
        You are a helpful data analyst assistant for dashboard conversations.
        
        When users ask about the dashboard, provide a comprehensive summary of what's available.
        Answer their questions in a clear, informative way and help them understand their data setup.
        
        CURRENT DASHBOARD CONTEXT:
        {context_info}
        
        Guidelines:
        - For dashboard overview questions, summarize the database connection, available tables, and context
        - Explain what kind of analysis they can do with their current setup
        - Suggest specific queries they might want to try based on their tables
        - Be conversational and helpful
        - Explain technical concepts in simple terms
        - If they ask about the dashboard generally, give them a complete picture of their current setup
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Question: {user_query}")
        ]
        
        response = llm.invoke(messages)
        
        return {
            "final_response": response.content,
            "query_result": None,  # General queries don't execute database queries
            "sql_query": None,
        }
        
    except Exception as e:
        logger.error(f"Error in general agent: {e}")
        return {
            "final_response": f"I encountered an error while processing your question: {str(e)}",
            "query_result": None,
            "sql_query": None,
        }