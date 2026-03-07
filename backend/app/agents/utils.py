"""
Utility functions for LangGraph agents including state logging
"""
import json
import logging
from typing import Dict, Any, Optional
from app.agents.types import AgentState


def log_agent_state(
    logger: logging.Logger,
    node_name: str,
    state: AgentState,
    phase: str = "input",
    result: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None
):
    """
    Standardized state logging for all agent nodes
    
    Args:
        logger: Logger instance for the node
        node_name: Name of the agent node (e.g., "ENHANCED_QUERY_ANALYZER")
        state: Current AgentState
        phase: "input", "output", or "error"
        result: Result dictionary for output phase
        error: Exception for error phase
    """
    
    if phase == "input":
        emoji = "📥"
        status = "Starting"
        data = {
            'user_query': state.get('user_query', 'N/A'),
            'user_id': state.get('user_id', 'N/A'),
            'datasource_id': state.get('datasource_id', 'N/A'),
            'has_dashboard_context': bool(state.get('dashboard_context')),
            'has_enhanced_analysis': bool(state.get('enhanced_analysis')),
            'current_step': state.get('current_step'),
            'execution_plan': str(state.get('execution_plan', 'N/A')),
            'messages_count': len(state.get('messages', [])),
            'thinking_process_steps': len(getattr(state.get('thinking_process'), 'reasoning_steps', [])) if state.get('thinking_process') else 0,
            'has_generated_sql': bool(state.get('generated_sql')),
            'generated_sql_preview': state.get('generated_sql', 'N/A')[:100] + ('...' if len(state.get('generated_sql', '')) > 100 else ''),
            'has_sql_result': bool(state.get('sql_query_result')),
            'has_insights': bool(state.get('generated_insights')),
            'retry_count': state.get('retry_count', 0),
            'error': state.get('error'),
            'execution_success': state.get('execution_success'),
            'results_valid': state.get('results_valid')
        }
        
    elif phase == "output":
        emoji = "📤"
        status = "Completed successfully"
        data = {}
        if result:
            # Extract key changes from result
            data.update({
                'updated_fields': list(result.keys()),
                'current_step': result.get('current_step'),
                'execution_success': result.get('execution_success'),
                'error': result.get('error')
            })
            
            # Add specific fields based on node type
            if 'enhanced_analysis' in result:
                analysis = result['enhanced_analysis']
                # Handle QueryType enum properly
                query_type = getattr(analysis, 'query_type', None)
                if query_type:
                    data['query_type'] = query_type.value if hasattr(query_type, 'value') else str(query_type)
                else:
                    data['query_type'] = 'N/A'
                data['confidence_score'] = getattr(analysis, 'confidence_score', 'N/A')
                data['needs_sql'] = getattr(analysis, 'needs_sql', 'N/A')
                
            if 'generated_sql' in result:
                sql_query = result['generated_sql']
                data['sql_length'] = len(sql_query) if sql_query else 0
                data['has_sql'] = bool(sql_query)
                data['generated_sql'] = sql_query if sql_query else 'None'
                
            if 'sql_query_result' in result:
                sql_result = result['sql_query_result']
                if sql_result:
                    data['query_success'] = getattr(sql_result, 'success', 'N/A')
                    data['row_count'] = getattr(sql_result, 'row_count', 'N/A')
                    data['execution_time'] = getattr(sql_result, 'execution_time_ms', 'N/A')
                
            if 'generated_insights' in result:
                insights = result['generated_insights']
                if insights:
                    data['insights_count'] = len(getattr(insights, 'key_insights', []))
                    data['has_recommendations'] = bool(getattr(insights, 'recommendations', []))
    
    elif phase == "error":
        emoji = "💥"
        status = "Failed with error"
        data = {
            'error': str(error) if error else state.get('error', 'Unknown error'),
            'error_type': type(error).__name__ if error else 'Unknown',
            'current_step': state.get('current_step'),
            'retry_count': state.get('retry_count', 0),
            'thinking_process_steps': len(getattr(state.get('thinking_process'), 'reasoning_steps', [])) if state.get('thinking_process') else 0
        }
    
    # Create log message
    log_level = logging.ERROR if phase == "error" else logging.INFO
    icon = "🧠" if "QUERY_ANALYZER" in node_name else "⚡" if "SQL" in node_name else "📊" if "INSIGHTS" in node_name else "🔄"
    
    logger.log(log_level, f"{icon} {node_name} - {status}")
    logger.log(log_level, f"{emoji} {phase.upper()} STATE: {json.dumps(data, indent=2, default=str)}")


def create_node_logger(node_name: str) -> logging.Logger:
    """
    Create a standardized logger for a node
    
    Args:
        node_name: Name of the node (e.g., "enhanced_query_analyzer")
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"agents.nodes.{node_name}")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate logs if logger already has handlers
    if not logger.handlers:
        # Create console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger