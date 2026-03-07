"""
SQL execution tool with connection pooling, limits, and error handling
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
import asyncpg
from langchain_core.tools import tool

from app.models.enhanced_query import SqlQueryResult
from app.services.datasource_service import DatasourceService


class SqlExecutionError(Exception):
    """Custom exception for SQL execution errors"""
    pass


class SqlExecutor:
    """Enhanced SQL executor with connection pooling and smart limits"""
    
    def __init__(self):
        self.datasource_service = DatasourceService()
        self._connection_pools = {}  # Cache connection pools per datasource
    
    async def get_connection_pool(self, datasource_id: str, user_id: str):
        """Get or create connection pool for a datasource"""
        if datasource_id in self._connection_pools:
            return self._connection_pools[datasource_id]
        
        datasource = await self.datasource_service.get_datasource(datasource_id, user_id)
        if not datasource:
            raise SqlExecutionError(f"Datasource {datasource_id} not found")
        
        try:
            # Create connection pool
            pool = await asyncpg.create_pool(
                datasource.get_connection_string(),
                min_size=1,
                max_size=5,
                command_timeout=30,
                server_settings={'jit': 'off'}  # Disable JIT for faster simple queries
            )
            self._connection_pools[datasource_id] = pool
            return pool
        except Exception as e:
            raise SqlExecutionError(f"Failed to create connection pool: {str(e)}")
    
    async def execute_with_limits(
        self,
        sql_query: str,
        datasource_id: str,
        user_id: str,
        llm_limit: int = 100,
        max_total_rows: int = 10000,
        timeout_seconds: int = 30
    ) -> SqlQueryResult:
        """
        Execute SQL with smart limits and comprehensive error handling
        """
        start_time = time.time()
        
        try:
            pool = await self.get_connection_pool(datasource_id, user_id)
            
            # Add LIMIT to query if not already present
            limited_sql = self._add_limit_to_query(sql_query, max_total_rows)
            
            async with pool.acquire() as connection:
                # Execute query with timeout
                rows = await asyncio.wait_for(
                    connection.fetch(limited_sql),
                    timeout=timeout_seconds
                )
                
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Convert rows to list of dicts
                full_results = [dict(row) for row in rows]
                
                # Create truncated results for LLM processing
                llm_results = full_results[:llm_limit]
                truncated = len(full_results) > llm_limit
                
                return SqlQueryResult(
                    original_query="",  # Will be set by caller
                    generated_sql=limited_sql,
                    execution_success=True,
                    llm_results=llm_results,
                    full_results=full_results,
                    row_count=len(full_results),
                    execution_time_ms=execution_time,
                    truncated=truncated
                )
                
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            return SqlQueryResult(
                original_query="",
                generated_sql=sql_query,
                execution_success=False,
                error=f"Query timeout after {timeout_seconds} seconds",
                error_type="timeout",
                execution_time_ms=execution_time
            )
        except asyncpg.PostgresError as e:
            execution_time = (time.time() - start_time) * 1000
            error_type = "syntax_error" if "syntax error" in str(e).lower() else "postgres_error"
            return SqlQueryResult(
                original_query="",
                generated_sql=sql_query,
                execution_success=False,
                error=str(e),
                error_type=error_type,
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SqlQueryResult(
                original_query="",
                generated_sql=sql_query,
                execution_success=False,
                error=str(e),
                error_type="unknown_error",
                execution_time_ms=execution_time
            )
    
    def _add_limit_to_query(self, sql_query: str, max_rows: int) -> str:
        """Add LIMIT clause to query if not already present"""
        sql_lower = sql_query.lower().strip()
        
        # Check if LIMIT already exists
        if 'limit' in sql_lower:
            return sql_query
        
        # Add LIMIT clause
        if sql_query.rstrip().endswith(';'):
            return sql_query.rstrip()[:-1] + f' LIMIT {max_rows};'
        else:
            return sql_query.rstrip() + f' LIMIT {max_rows}'
    
    async def validate_query_syntax(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL syntax without executing"""
        try:
            # Basic SQL validation - check for forbidden operations
            sql_lower = sql_query.lower()
            
            # Forbidden operations
            forbidden = ['drop', 'delete', 'truncate', 'insert', 'update', 'create', 'alter']
            for word in forbidden:
                if f' {word} ' in sql_lower or sql_lower.startswith(f'{word} '):
                    return {
                        "valid": False,
                        "error": f"Forbidden operation: {word.upper()}"
                    }
            
            # Must start with SELECT
            if not sql_lower.strip().startswith('select'):
                return {
                    "valid": False,
                    "error": "Query must start with SELECT"
                }
            
            return {"valid": True, "error": None}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


# LangChain tool wrapper
@tool
async def execute_sql_query(
    sql_query: str,
    datasource_id: str,
    user_id: str,
    original_query: str = "",
    llm_limit: int = 100,
    max_total_rows: int = 10000
) -> SqlQueryResult:
    """
    Execute SQL query with proper limits and error handling
    
    Args:
        sql_query: The SQL query to execute
        datasource_id: ID of the datasource to query
        user_id: ID of the user making the request
        original_query: Original user question (for tracking)
        llm_limit: Maximum rows to return for LLM processing
        max_total_rows: Maximum total rows to fetch
    
    Returns:
        SqlQueryResult with execution details and results
    """
    executor = SqlExecutor()
    
    # Validate query first
    validation = await executor.validate_query_syntax(sql_query)
    if not validation["valid"]:
        return SqlQueryResult(
            original_query=original_query,
            generated_sql=sql_query,
            execution_success=False,
            error=validation["error"],
            error_type="validation_error"
        )
    
    # Execute query
    result = await executor.execute_with_limits(
        sql_query=sql_query,
        datasource_id=datasource_id,
        user_id=user_id,
        llm_limit=llm_limit,
        max_total_rows=max_total_rows
    )
    
    # Set original query
    result.original_query = original_query
    
    return result


@tool
async def get_table_schema_info(
    datasource_id: str,
    user_id: str,
    table_names: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get detailed schema information for tables
    
    Args:
        datasource_id: ID of the datasource
        user_id: ID of the user
        table_names: Specific tables to get info for (None = all tables)
    
    Returns:
        List of table schema information
    """
    datasource_service = DatasourceService()
    
    try:
        # Get table information
        all_tables = await datasource_service.discover_tables(datasource_id, user_id)
        
        if table_names:
            # Filter to requested tables
            all_tables = [t for t in all_tables if t.name in table_names or t.full_name in table_names]
        
        # Convert to schema info format
        schema_info = []
        for table in all_tables:
            schema_info.append({
                "table_name": table.name,
                "schema_name": table.schema,
                "full_name": table.full_name,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "nullable": col.is_nullable,
                        "sample_values": col.sample_values[:5] if col.sample_values else []
                    }
                    for col in table.columns
                ],
                "row_count": table.row_count,
                "description": table.description
            })
        
        return schema_info
        
    except Exception as e:
        raise SqlExecutionError(f"Failed to get schema info: {str(e)}")