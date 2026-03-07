"""
Datasource service for managing database connections and table discovery
"""
import asyncio
from typing import List, Optional, Dict, Any
import asyncpg

from app.models.datasource import (
    DatasourceConnection, 
    TableInfo, 
    TableColumn,
    Dataset
)
from app.services.postgres_database_service import get_postgres_db_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


class DatasourceService:
    """Service for managing datasources and table discovery"""
    
    def __init__(self, db_session: AsyncSession = None):
        self.db_session = db_session
    
    async def test_connection(self, connection: DatasourceConnection) -> Dict[str, Any]:
        """Test database connection with timeout"""
        try:
            # Quick connection test with timeout
            conn = await asyncio.wait_for(
                asyncpg.connect(connection.get_connection_string()),
                timeout=5  # 5 second timeout
            )
            
            # Simple test query
            current_db = await asyncio.wait_for(
                conn.fetchval("SELECT current_database()"),
                timeout=5
            )
            
            await conn.close()
            
            return {
                "success": True,
                "message": "Connection successful",
                "database_info": {
                    "current_database": current_db,
                }
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "Connection timeout. Check your network and database details.",
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def save_datasource(self, connection: DatasourceConnection, user_id: str) -> str:
        """Save datasource connection"""
        import uuid
        
        datasource_id = connection.id or str(uuid.uuid4())
        connection.id = datasource_id
        
        db_service = await get_postgres_db_service(self.db_session)
        await db_service.save_datasource(connection, user_id)
        
        return datasource_id
    
    async def get_datasource(self, datasource_id: str, user_id: str) -> Optional[DatasourceConnection]:
        """Get datasource by ID"""
        db_service = await get_postgres_db_service(self.db_session)
        return await db_service.get_datasource(datasource_id, user_id)
    
    async def list_user_datasources(self, user_id: str) -> List[DatasourceConnection]:
        """List all datasources for a user"""
        db_service = await get_postgres_db_service(self.db_session)
        return await db_service.list_datasources(user_id)
    
    async def discover_tables(self, datasource_id: str, user_id: str) -> List[TableInfo]:
        """Discover tables and schemas - simple and fast"""
        datasource = await self.get_datasource(datasource_id, user_id)
        if not datasource:
            raise ValueError("Datasource not found")
        
        try:
            # Simple connection with timeout
            conn = await asyncio.wait_for(
                asyncpg.connect(datasource.get_connection_string()),
                timeout=5  # 5 second connection timeout
            )
            
            # Simple query - just get schema and table names
            query = """
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schemaname, tablename
            """
            
            rows = await asyncio.wait_for(conn.fetch(query), timeout=10)
            tables = []
            
            for row in rows:
                table_info = TableInfo(
                    name=row['tablename'],
                    schema=row['schemaname'],
                    description=None,
                    row_count=None,
                    columns=[]  # Empty - we don't need column details for selection
                )
                tables.append(table_info)
            
            await conn.close()
            return tables
            
        except asyncio.TimeoutError:
            raise Exception("Connection timeout. Check your network and database details.")
        except Exception as e:
            raise Exception(f"Failed to discover tables: {str(e)}")
    
    async def _get_table_columns(
        self, conn, schema: str, table: str
    ) -> List[TableColumn]:
        """Get detailed column information for a table"""
        columns_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable = 'YES' as is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        
        column_rows = await conn.fetch(columns_query, schema, table)
        columns = []
        
        for row in column_rows:
            # Get sample values for this column
            sample_values = await self._get_sample_values(
                conn, schema, table, row['column_name']
            )
            
            column = TableColumn(
                name=row['column_name'],
                data_type=row['data_type'],
                is_nullable=row['is_nullable'],
                sample_values=sample_values
            )
            columns.append(column)
        
        return columns
    
    async def _get_sample_values(
        self, conn, schema: str, table: str, column: str, limit: int = 5
    ) -> List[str]:
        """Get sample values from a column"""
        try:
            query = f"""
                SELECT DISTINCT "{column}" 
                FROM "{schema}"."{table}" 
                WHERE "{column}" IS NOT NULL 
                ORDER BY "{column}" 
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)
            return [str(row[0]) for row in rows]
        except Exception:
            return []
    
    async def _get_table_row_count(
        self, conn, schema: str, table: str
    ) -> Optional[int]:
        """Get estimated row count for a table"""
        try:
            # Use pg_stat for fast estimate
            query = """
                SELECT n_tup_ins - n_tup_del AS estimated_rows
                FROM pg_stat_user_tables 
                WHERE schemaname = $1 AND relname = $2
            """
            result = await conn.fetchval(query, schema, table)
            
            if result is None:
                # Fallback to exact count for small tables
                count_query = f'SELECT COUNT(*) FROM "{schema}"."{table}"'
                result = await conn.fetchval(count_query)
            
            return result
        except Exception:
            return None
    
    async def get_table_columns(self, datasource_id: str, user_id: str, schema: str, table: str) -> List[TableColumn]:
        """Get column information for a specific table"""
        datasource = await self.get_datasource(datasource_id, user_id)
        if not datasource:
            raise Exception(f"Datasource {datasource_id} not found")
        
        conn = None
        try:
            conn = await asyncpg.connect(datasource.get_connection_string())
            columns = await self._get_table_columns(conn, schema, table)
            return columns
        except Exception as e:
            raise Exception(f"Failed to get columns for {schema}.{table}: {str(e)}")
        finally:
            if conn:
                await conn.close()
    
    
