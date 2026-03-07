"""
PostgreSQL database service for persisting datasources and datasets
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.datasource import DatasourceConnection, Dataset, DashboardContext, ChatSession, ChatMessage
from app.core.config import settings
from app.core.database import get_db


class PostgresDatabaseService:
    """Service for managing PostgreSQL database persistence"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_sql(self, query: str, params=None):
        """Execute SQL query using SQLAlchemy session"""
        result = await self.session.execute(text(query), params or {})
        return result
    
    async def fetch_one(self, query: str, params=None):
        """Fetch one row using SQLAlchemy session"""
        result = await self.session.execute(text(query), params or {})
        return result.fetchone()
    
    async def fetch_all(self, query: str, params=None):
        """Fetch all rows using SQLAlchemy session"""
        result = await self.session.execute(text(query), params or {})
        return result.fetchall()

    async def init_database(self):
        """Initialize database tables"""
        # Create datasources table
        await self.execute_sql('''
            CREATE TABLE IF NOT EXISTS chat_datasources (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                database_name TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                ssl_mode TEXT DEFAULT 'prefer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, id)
            )
        ''')
        
        # Create dashboard contexts table
        await self.execute_sql('''
            CREATE TABLE IF NOT EXISTS chat_dashboard_contexts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                datasource_id TEXT NOT NULL,
                text_context TEXT,
                json_context TEXT,
                additional_instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (datasource_id) REFERENCES chat_datasources (id)
            )
        ''')
        
        # Create chat sessions table
        await self.execute_sql('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                dashboard_context_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dashboard_context_id) REFERENCES chat_dashboard_contexts (id)
            )
        ''')
        
        # Create chat messages table
        await self.execute_sql('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                chat_session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sql_query TEXT,
                query_result TEXT,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_session_id) REFERENCES chat_sessions (id)
            )
        ''')
        
        # Create datasets table (linked to dashboard contexts)
        await self.execute_sql('''
            CREATE TABLE IF NOT EXISTS chat_datasets (
                id SERIAL PRIMARY KEY,
                dashboard_context_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                table_schema TEXT NOT NULL,
                alias TEXT,
                is_enabled BOOLEAN DEFAULT true,
                column_metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dashboard_context_id) REFERENCES chat_dashboard_contexts (id)
            )
        ''')
        
        # Add column_metadata column if it doesn't exist (for existing databases)
        await self.execute_sql('''
            ALTER TABLE chat_datasets 
            ADD COLUMN IF NOT EXISTS column_metadata TEXT
        ''')
        
        await self.session.commit()
        print("PostgreSQL database tables initialized successfully")
    
    # Datasource operations
    async def save_datasource(self, datasource: DatasourceConnection, user_id: str) -> str:
        """Save datasource connection"""
        result = await self.session.execute(text('''
            INSERT INTO chat_datasources 
            (id, user_id, name, type, host, port, database_name, username, password, ssl_mode)
            VALUES (:id, :user_id, :name, :type, :host, :port, :database_name, :username, :password, :ssl_mode)
            ON CONFLICT (user_id, id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                host = EXCLUDED.host,
                port = EXCLUDED.port,
                database_name = EXCLUDED.database_name,
                username = EXCLUDED.username,
                password = EXCLUDED.password,
                ssl_mode = EXCLUDED.ssl_mode
        '''), {
            'id': datasource.id,
            'user_id': user_id,
            'name': datasource.name,
            'type': datasource.type.value,
            'host': datasource.host,
            'port': datasource.port,
            'database_name': datasource.database,
            'username': datasource.username,
            'password': datasource.password,
            'ssl_mode': datasource.ssl_mode
        })
        await self.session.commit()
        return datasource.id
    
    async def get_datasource(self, datasource_id: str, user_id: str) -> Optional[DatasourceConnection]:
        """Get datasource by ID and user"""
        row = await self.fetch_one('''
            SELECT id, name, type, host, port, database_name, username, password, ssl_mode
            FROM chat_datasources 
            WHERE id = :datasource_id AND user_id = :user_id
        ''', {'datasource_id': datasource_id, 'user_id': user_id})
        
        if not row:
            return None
        
        from app.models.datasource import DatasourceType
        return DatasourceConnection(
            id=row[0],
            name=row[1],
            type=DatasourceType(row[2]),
            host=row[3],
            port=row[4],
            database=row[5],
            username=row[6],
            password=row[7],
            ssl_mode=row[8]
        )
    
    async def list_datasources(self, user_id: str) -> List[DatasourceConnection]:
        """List all datasources for user"""
        rows = await self.fetch_all('''
            SELECT id, name, type, host, port, database_name, username, password, ssl_mode
            FROM chat_datasources 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        ''', {'user_id': user_id})
        
        datasources = []
        for row in rows:
            from app.models.datasource import DatasourceType
            datasources.append(DatasourceConnection(
                id=row[0],
                name=row[1],
                type=DatasourceType(row[2]),
                host=row[3],
                port=row[4],
                database=row[5],
                username=row[6],
                password=row[7],
                ssl_mode=row[8]
            ))
        
        return datasources
    
    # Dashboard context operations
    async def save_dashboard_context(self, context: DashboardContext, user_id: str) -> str:
        """Save dashboard context"""
        await self.session.execute(text('''
            INSERT INTO chat_dashboard_contexts 
            (id, user_id, name, description, datasource_id, text_context, json_context, additional_instructions, updated_at)
            VALUES (:id, :user_id, :name, :description, :datasource_id, :text_context, :json_context, :additional_instructions, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                datasource_id = EXCLUDED.datasource_id,
                text_context = EXCLUDED.text_context,
                json_context = EXCLUDED.json_context,
                additional_instructions = EXCLUDED.additional_instructions,
                updated_at = CURRENT_TIMESTAMP
        '''), {
            'id': context.id,
            'user_id': user_id,
            'name': context.name,
            'description': context.description,
            'datasource_id': context.datasource_id,
            'text_context': context.text_context,
            'json_context': context.json_context,
            'additional_instructions': context.additional_instructions
        })
        await self.session.commit()
        return context.id
    
    async def get_dashboard_context(self, context_id: str, user_id: str) -> Optional[DashboardContext]:
        """Get dashboard context by ID and user"""
        row = await self.fetch_one('''
            SELECT id, user_id, name, description, datasource_id, text_context, json_context, additional_instructions, created_at, updated_at
            FROM chat_dashboard_contexts 
            WHERE id = :context_id AND user_id = :user_id
        ''', {'context_id': context_id, 'user_id': user_id})
        
        if not row:
            return None
        
        return DashboardContext(
            id=row[0],
            user_id=row[1],
            name=row[2],
            description=row[3],
            datasource_id=row[4],
            text_context=row[5],
            json_context=row[6],
            additional_instructions=row[7],
            created_at=row[8],
            updated_at=row[9]
        )
    
    async def list_dashboard_contexts(self, user_id: str) -> List[DashboardContext]:
        """List all dashboard contexts for user"""
        rows = await self.fetch_all('''
            SELECT id, user_id, name, description, datasource_id, text_context, json_context, additional_instructions, created_at, updated_at
            FROM chat_dashboard_contexts 
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
        ''', {'user_id': user_id})
        
        contexts = []
        for row in rows:
            contexts.append(DashboardContext(
                id=row[0],
                user_id=row[1], 
                name=row[2],
                description=row[3],
                datasource_id=row[4],
                text_context=row[5],
                json_context=row[6],
                additional_instructions=row[7],
                created_at=row[8],
                updated_at=row[9]
            ))
        
        return contexts
    
    async def delete_dashboard_context(self, context_id: str, user_id: str) -> bool:
        """Delete dashboard context and related data"""
        async with self.session.begin():
            # Delete datasets first
            await self.session.execute(text('''
                DELETE FROM chat_datasets WHERE dashboard_context_id = :context_id
            '''), {'context_id': context_id})
            
            # Delete chat messages for sessions related to this context
            await self.session.execute(text('''
                DELETE FROM chat_messages 
                WHERE chat_session_id IN (
                    SELECT id FROM chat_sessions WHERE dashboard_context_id = :context_id
                )
            '''), {'context_id': context_id})
            
            # Delete chat sessions
            await self.session.execute(text('''
                DELETE FROM chat_sessions WHERE dashboard_context_id = :context_id
            '''), {'context_id': context_id})
            
            # Delete the context
            result = await self.session.execute(text('''
                DELETE FROM chat_dashboard_contexts 
                WHERE id = :context_id AND user_id = :user_id
            '''), {'context_id': context_id, 'user_id': user_id})
            
            return result.rowcount > 0
    
    # Chat session operations
    async def save_chat_session(self, session: ChatSession, user_id: str) -> str:
        """Save chat session"""
        await self.session.execute(text('''
            INSERT INTO chat_sessions 
            (id, dashboard_context_id, user_id, name, updated_at)
            VALUES (:id, :dashboard_context_id, :user_id, :name, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = CURRENT_TIMESTAMP
        '''), {
            'id': session.id,
            'dashboard_context_id': session.dashboard_context_id,
            'user_id': user_id,
            'name': session.name
        })
        await self.session.commit()
        return session.id
    
    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get chat session by ID and user"""
        row = await self.fetch_one('''
            SELECT id, dashboard_context_id, user_id, name, created_at, updated_at
            FROM chat_sessions 
            WHERE id = :session_id AND user_id = :user_id
        ''', {'session_id': session_id, 'user_id': user_id})
        
        if not row:
            return None
        
        return ChatSession(
            id=row[0],
            dashboard_context_id=row[1],
            user_id=row[2],
            name=row[3],
            created_at=row[4],
            updated_at=row[5]
        )
    
    async def list_chat_sessions(self, dashboard_context_id: str, user_id: str) -> List[ChatSession]:
        """List chat sessions for dashboard context"""
        rows = await self.fetch_all('''
            SELECT id, dashboard_context_id, user_id, name, created_at, updated_at
            FROM chat_sessions 
            WHERE dashboard_context_id = :dashboard_context_id AND user_id = :user_id
            ORDER BY updated_at DESC
        ''', {'dashboard_context_id': dashboard_context_id, 'user_id': user_id})
        
        sessions = []
        for row in rows:
            sessions.append(ChatSession(
                id=row[0],
                dashboard_context_id=row[1],
                user_id=row[2],
                name=row[3],
                created_at=row[4],
                updated_at=row[5]
            ))
        
        return sessions
    
    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete chat session and messages"""
        async with self.session.begin():
            # Delete messages first
            await self.session.execute(text('''
                DELETE FROM chat_messages 
                WHERE chat_session_id = :session_id
            '''), {'session_id': session_id})
            
            # Delete session
            result = await self.session.execute(text('''
                DELETE FROM chat_sessions 
                WHERE id = :session_id AND user_id = :user_id
            '''), {'session_id': session_id, 'user_id': user_id})
            
            return result.rowcount > 0
    
    # Chat message operations
    async def save_chat_message(self, message: ChatMessage):
        """Save chat message"""
        await self.session.execute(text('''
            INSERT INTO chat_messages 
            (id, chat_session_id, role, content, sql_query, query_result, reasoning)
            VALUES (:id, :chat_session_id, :role, :content, :sql_query, :query_result, :reasoning)
        '''), {
            'id': message.id,
            'chat_session_id': message.chat_session_id,
            'role': message.role,
            'content': message.content,
            'sql_query': message.sql_query,
            'query_result': message.query_result,
            'reasoning': message.reasoning
        })
        await self.session.commit()
    
    async def get_chat_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get chat messages for session"""
        rows = await self.fetch_all('''
            SELECT id, chat_session_id, role, content, sql_query, query_result, reasoning, created_at
            FROM chat_messages 
            WHERE chat_session_id = :session_id
            ORDER BY created_at ASC
            LIMIT :limit
        ''', {'session_id': session_id, 'limit': limit})
        
        messages = []
        for row in rows:
            messages.append(ChatMessage(
                id=row[0],
                chat_session_id=row[1],
                role=row[2],
                content=row[3],
                sql_query=row[4],
                query_result=row[5],
                reasoning=row[6],
                created_at=row[7]
            ))
        
        return messages
    
    # Dataset operations
    async def save_datasets_for_context(self, context_id: str, datasets: List[Dataset]):
        """Save datasets for dashboard context"""
        print(f"DEBUG: Saving {len(datasets)} datasets for context {context_id}")
        for i, dataset in enumerate(datasets):
            print(f"DEBUG: Dataset {i}: {dataset.table_schema}.{dataset.table_name} with {len(dataset.columns)} columns")
        
        # Delete existing datasets for context
        await self.session.execute(text('''
            DELETE FROM chat_datasets WHERE dashboard_context_id = :context_id
        '''), {'context_id': context_id})
        
        # Insert new datasets
        for dataset in datasets:
            # Serialize column metadata to JSON
            column_metadata_json = None
            if dataset.columns:
                column_metadata_json = json.dumps([
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "is_nullable": col.is_nullable,
                        "description": col.description
                    }
                    for col in dataset.columns
                ])
            
            await self.session.execute(text('''
                INSERT INTO chat_datasets 
                (dashboard_context_id, table_name, table_schema, alias, is_enabled, column_metadata)
                VALUES (:context_id, :table_name, :table_schema, :alias, :is_enabled, :column_metadata)
            '''), {
                'context_id': context_id,
                'table_name': dataset.table_name,
                'table_schema': dataset.table_schema,
                'alias': dataset.alias,
                'is_enabled': dataset.is_enabled,
                'column_metadata': column_metadata_json
            })
        
        await self.session.commit()
    
    async def get_datasets_for_context(self, context_id: str) -> List[Dataset]:
        """Get datasets for dashboard context"""
        print(f"DEBUG: Getting datasets for context {context_id}")
        rows = await self.fetch_all('''
            SELECT dashboard_context_id, table_name, table_schema, alias, is_enabled, column_metadata
            FROM chat_datasets 
            WHERE dashboard_context_id = :context_id AND is_enabled = true
            ORDER BY table_name
        ''', {'context_id': context_id})
        
        from app.models.datasource import TableColumn
        
        datasets = []
        for row in rows:
            # Deserialize column metadata from JSON
            columns = []
            if row[5]:  # column_metadata
                try:
                    column_data = json.loads(row[5])
                    columns = [
                        TableColumn(
                            name=col["name"],
                            data_type=col["data_type"],
                            is_nullable=col["is_nullable"],
                            description=col.get("description")
                        )
                        for col in column_data
                    ]
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Failed to parse column metadata for {row[2]}.{row[1]}: {e}")
                    columns = []
            
            datasets.append(Dataset(
                dashboard_context_id=context_id,
                table_name=row[1],
                table_schema=row[2],
                alias=row[3],
                is_enabled=row[4],
                columns=columns
            ))
        
        print(f"DEBUG: Found {len(datasets)} datasets for context {context_id}")
        return datasets


# FastAPI dependency function
async def get_postgres_db_service(session: AsyncSession) -> PostgresDatabaseService:
    """FastAPI dependency for database service"""
    service = PostgresDatabaseService(session)
    try:
        await service.init_database()
    except Exception as e:
        print(f"Failed to initialize PostgreSQL database: {e}")
        raise
    return service