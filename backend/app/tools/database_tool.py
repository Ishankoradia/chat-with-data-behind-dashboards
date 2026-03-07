"""
Database query tool for executing SQL queries
"""
import time
from typing import Optional, Dict, Any, List
import asyncpg
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings
from app.models.chat import QueryResult


class DatabaseTool:
    """Tool for executing database queries"""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        
    async def execute_metric_query(
        self, 
        query: str, 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate and execute a SQL query for metric-related questions
        """
        try:
            # Generate SQL using LLM
            sql_query = await self._generate_sql_for_metrics(query, dashboard_context)
            if not sql_query:
                return None
                
            # Execute the query
            return await self._execute_sql(sql_query)
            
        except Exception as e:
            print(f"Error executing metric query: {e}")
            return None
    
    async def execute_dimension_query(
        self, 
        query: str, 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate and execute a SQL query for dimension-related questions
        """
        try:
            # Generate SQL using LLM
            sql_query = await self._generate_sql_for_dimensions(query, dashboard_context)
            if not sql_query:
                return None
                
            # Execute the query
            return await self._execute_sql(sql_query)
            
        except Exception as e:
            print(f"Error executing dimension query: {e}")
            return None
    
    async def _generate_sql_for_metrics(
        self, 
        query: str, 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Use LLM to generate SQL for metric queries
        """
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.1,  # Low temperature for precise SQL generation
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Build context for SQL generation
        context_info = ""
        if dashboard_context:
            context_info += f"Available metrics: {', '.join(dashboard_context.metrics)}\n"
            context_info += f"Available dimensions: {', '.join(dashboard_context.dimensions)}\n"
            
        system_prompt = f"""
        You are a SQL expert. Generate a PostgreSQL query to answer the user's question about metrics.
        
        Database Context:
        {context_info}
        
        Guidelines:
        - Generate only the SQL query, no explanations
        - Use standard PostgreSQL syntax
        - Focus on metric calculations (SUM, COUNT, AVG, etc.)
        - Include appropriate WHERE clauses and GROUP BY when needed
        - Return only the SQL query text
        
        Example table structure (adjust as needed):
        - sales_data (date, product_id, revenue, quantity, customer_id)
        - products (product_id, product_name, category)
        - customers (customer_id, customer_name, segment)
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate SQL for: {query}")
            ]
            
            response = await llm.ainvoke(messages)
            sql = response.content.strip()
            
            # Clean up the SQL (remove markdown formatting if present)
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
                
            return sql.strip()
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return None
    
    async def _generate_sql_for_dimensions(
        self, 
        query: str, 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Use LLM to generate SQL for dimension queries
        """
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        context_info = ""
        if dashboard_context:
            context_info += f"Available dimensions: {', '.join(dashboard_context.dimensions)}\n"
            context_info += f"Available metrics: {', '.join(dashboard_context.metrics)}\n"
            
        system_prompt = f"""
        You are a SQL expert. Generate a PostgreSQL query to answer the user's question about dimensions and breakdowns.
        
        Database Context:
        {context_info}
        
        Guidelines:
        - Generate only the SQL query, no explanations
        - Use standard PostgreSQL syntax
        - Focus on dimensional analysis (GROUP BY, breakdowns, distributions)
        - Include counts, percentages, and rankings when appropriate
        - Return only the SQL query text
        
        Example table structure (adjust as needed):
        - sales_data (date, product_id, revenue, quantity, customer_id, region)
        - products (product_id, product_name, category)
        - customers (customer_id, customer_name, segment)
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate SQL for: {query}")
            ]
            
            response = await llm.ainvoke(messages)
            sql = response.content.strip()
            
            # Clean up the SQL
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
                
            return sql.strip()
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return None
    
    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute SQL query and return structured result
        """
        start_time = time.time()
        
        try:
            # Connect to database
            conn = await asyncpg.connect(self.database_url)
            
            # Execute query
            rows = await conn.fetch(sql)
            
            # Convert to list of dictionaries
            data = [dict(row) for row in rows]
            columns = list(rows[0].keys()) if rows else []
            
            await conn.close()
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "sql": sql,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "execution_time_ms": execution_time,
            }
            
        except Exception as e:
            print(f"Error executing SQL: {e}")
            # Return mock data for development
            return {
                "sql": sql,
                "data": [
                    {"metric": "total_revenue", "value": 125000, "period": "2024-03"},
                    {"metric": "total_revenue", "value": 118000, "period": "2024-02"},
                ],
                "columns": ["metric", "value", "period"],
                "row_count": 2,
                "execution_time_ms": 50,
                "error": str(e),
            }
    
    async def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL query without executing it
        """
        try:
            conn = await asyncpg.connect(self.database_url)
            # Use EXPLAIN to validate without executing
            await conn.fetch(f"EXPLAIN {sql}")
            await conn.close()
            return True
        except Exception:
            return False