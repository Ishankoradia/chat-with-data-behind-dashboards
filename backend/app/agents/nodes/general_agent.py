"""
General Agent - handles general dashboard questions and explanations
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.types import AgentState
from app.core.config import settings


def handle_general_query(state: AgentState) -> Dict[str, Any]:
    """
    Handle general questions about dashboards and explanatory queries
    """
    print("DEBUG: General agent executing")
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
            
            context_info += f"Database: {datasource.name if datasource else 'Unknown'}\n"
            context_info += f"Available tables: {', '.join([d.display_name for d in datasets])}\n"
            
            if text_context:
                context_info += f"Business Context: {text_context}\n"
        
        system_prompt = f"""
        You are a helpful data analyst assistant for dashboard conversations.
        
        Answer the user's question about the dashboard in a clear, informative way.
        Provide explanations about dashboard features, data insights, or guidance on how to explore the data.
        
        Dashboard Context:
        {context_info}
        
        Guidelines:
        - Be conversational and helpful
        - Explain technical concepts in simple terms
        - Suggest actionable next steps when appropriate
        - If you don't have specific information, be honest about limitations
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
        print(f"Error in general agent: {e}")
        return {
            "final_response": f"I encountered an error while processing your question: {str(e)}",
            "query_result": None,
            "sql_query": None,
        }