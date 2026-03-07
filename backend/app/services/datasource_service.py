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
        """Test database connection"""
        try:
            conn = await asyncpg.connect(connection.get_connection_string())
            
            # Get basic database info
            version = await conn.fetchval("SELECT version()")
            current_db = await conn.fetchval("SELECT current_database()")
            
            await conn.close()
            
            return {
                "success": True,
                "message": "Connection successful",
                "database_info": {
                    "version": version,
                    "current_database": current_db,
                }
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
        """Discover all tables in the datasource"""
        datasource = await self.get_datasource(datasource_id, user_id)
        if not datasource:
            raise ValueError("Datasource not found")
        
        try:
            conn = await asyncpg.connect(datasource.get_connection_string())
            
            # Get all tables with basic info
            tables_query = """
                SELECT 
                    schemaname as schema_name,
                    tablename as table_name,
                    obj_description(c.oid) as description
                FROM pg_tables pt
                LEFT JOIN pg_class c ON c.relname = pt.tablename
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schemaname, tablename
            """
            
            table_rows = await conn.fetch(tables_query)
            tables = []
            
            for row in table_rows:
                # Get column information for each table
                columns = await self._get_table_columns(
                    conn, row['schema_name'], row['table_name']
                )
                
                # Get row count estimate
                row_count = await self._get_table_row_count(
                    conn, row['schema_name'], row['table_name']
                )
                
                table_info = TableInfo(
                    name=row['table_name'],
                    schema=row['schema_name'],
                    description=row['description'],
                    row_count=row_count,
                    columns=columns
                )
                tables.append(table_info)
            
            await conn.close()
            return tables
            
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
    
    
