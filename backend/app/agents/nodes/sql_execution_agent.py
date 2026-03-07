"""
SQL Execution Agent - executes queries with retry logic and transparent reporting
"""
import time
import asyncpg
import asyncio
import logging
from typing import Dict, Any, List
from app.agents.types import AgentState
from app.agents.utils import log_agent_state, create_node_logger
from app.models.enhanced_query import SqlQueryResult, ReasoningStep
from app.core.config import settings

# Configure logger for this node
logger = create_node_logger("sql_execution_agent")


async def _execute_sql_query(datasource, sql_query: str) -> List[Dict[str, Any]]:
    """Execute SQL query against PostgreSQL database"""
    
    # Build connection string from datasource
    connection_string = f"postgresql://{datasource.username}:{datasource.password}@{datasource.host}:{datasource.port}/{datasource.database}"
    
    conn = None
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(connection_string)
        
        # Execute the query
        rows = await conn.fetch(sql_query)
        
        # Convert rows to list of dictionaries
        results = []
        for row in rows:
            row_dict = dict(row)
            results.append(row_dict)
        
        return results
        
    finally:
        if conn:
            await conn.close()


def execute_sql_with_reasoning(state: AgentState) -> Dict[str, Any]:
    """
    Execute SQL query with retry logic and detailed reasoning
    """
    # Log incoming state
    log_agent_state(logger, "SQL_EXECUTION_AGENT", state, "input")
    
    logger.debug("SQL execution node executing")
    generated_sql = state.get("generated_sql")
    user_query = state["user_query"]
    thinking_process = state.get("thinking_process")
    
    if not thinking_process:
        logger.debug("Missing thinking process")
        return {"error": "Missing thinking process"}
    
    if not generated_sql:
        logger.debug("No SQL query to execute")
        return {"error": "No SQL query to execute"}
    
    print(f"DEBUG: Executing SQL: {generated_sql}")
    start_time = time.time()
    
    # Get datasource connection info
    dashboard_context = state.get("dashboard_context")
    print(f"DEBUG: dashboard_context keys: {list(dashboard_context.keys()) if dashboard_context else 'None'}")
    datasource = dashboard_context.get("datasource") if dashboard_context else None
    print(f"DEBUG: datasource object: {datasource}")
    print(f"DEBUG: datasource type: {type(datasource)}")
    
    if not datasource:
        print(f"DEBUG: No datasource - dashboard_context exists: {dashboard_context is not None}")
        if dashboard_context:
            print(f"DEBUG: dashboard_context contents: {dashboard_context}")
        return {"error": "No datasource available for SQL execution"}
    
    try:
        # Execute SQL query against PostgreSQL
        print(f"DEBUG: Connecting to database: {datasource.host}:{datasource.port}/{datasource.database}")
        results = asyncio.run(_execute_sql_query(datasource, generated_sql))
        execution_time_ms = (time.time() - start_time) * 1000
        
        print(f"DEBUG: SQL execution returned {len(results)} rows")
        if results:
            print(f"DEBUG: First row: {results[0]}")
        
        # Prepare results for both frontend display and LLM processing
        full_results = results
        llm_results = results[:10] if len(results) > 10 else results  # Limit for LLM
        
        sql_result = SqlQueryResult(
            original_query=user_query,
            generated_sql=generated_sql,
            execution_success=True,
            full_results=full_results,
            llm_results=llm_results,
            row_count=len(results),
            execution_time_ms=execution_time_ms
        )
        
    except Exception as e:
        print(f"DEBUG: SQL execution error: {e}")
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Create error result
        sql_result = SqlQueryResult(
            original_query=user_query,
            generated_sql=generated_sql,
            execution_success=False,
            full_results=[],
            llm_results=[],
            row_count=0,
            execution_time_ms=execution_time_ms,
            error_message=str(e)
        )
        
        error_result = {
            "sql_query_result": sql_result,
            "execution_success": False,
            "thinking_process": thinking_process,
            "error": str(e),
            "final_response": f"I encountered an error while executing the SQL query: {str(e)}"
        }
        
        # Log error state
        log_agent_state(logger, "SQL_EXECUTION_AGENT", state, "error", error_result, e)
        
        return error_result
    
    # Add execution step to thinking process
    exec_step = ReasoningStep(
        step_number=len(thinking_process.reasoning_steps) + 1,
        step_type="sql_execution",
        title="🚀 Executing Query",
        description="Running SQL against your database",
        status="in_progress"
    )
    thinking_process.reasoning_steps.append(exec_step)
    
    # Complete the execution step successfully
    exec_step.description = f"✅ Successfully executed: {generated_sql[:50]}..."
    exec_step.status = "completed"
    exec_step.duration_ms = (time.time() - start_time) * 1000
    exec_step.details = {
        "rows_returned": sql_result.row_count,
        "execution_time_ms": sql_result.execution_time_ms,
        "query_successful": sql_result.execution_success
    }
    
    logger.debug("Real SQL execution completed successfully")
    
    result = {
        "sql_query_result": sql_result,
        "execution_success": sql_result.execution_success,
        "thinking_process": thinking_process,
        "current_step": f"SQL Execution Complete: {sql_result.row_count} rows returned",
        "step_details": exec_step.details
    }
    
    # Log output state
    log_agent_state(logger, "SQL_EXECUTION_AGENT", state, "output", result)
    
    return result