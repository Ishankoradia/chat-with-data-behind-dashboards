"""
Datasource models for database connections and table management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DatasourceType(str, Enum):
    POSTGRESQL = "postgresql"
    # Future: MYSQL = "mysql", SNOWFLAKE = "snowflake", etc.


class DatasourceConnection(BaseModel):
    """Database connection configuration"""
    id: Optional[str] = None
    name: str = Field(description="User-friendly name for the datasource")
    type: DatasourceType = DatasourceType.POSTGRESQL
    host: str
    port: int = 5432
    database: str
    username: str
    password: str = Field(..., description="Will be encrypted in storage")
    ssl_mode: str = "prefer"
    
    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"


class TableColumn(BaseModel):
    """Database table column information"""
    name: str
    data_type: str
    is_nullable: bool
    description: Optional[str] = None
    sample_values: Optional[List[str]] = None


class TableInfo(BaseModel):
    """Database table metadata"""
    name: str
    schema: str = Field(default="public", description="Database schema name")
    description: Optional[str] = None
    row_count: Optional[int] = None
    columns: List[TableColumn] = Field(default_factory=list)
    full_name: Optional[str] = None  # Computed field for frontend
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.full_name is None:
            self.full_name = f"{self.schema}.{self.name}"
    
    model_config = {"arbitrary_types_allowed": True}


class Dataset(BaseModel):
    """Selected dataset (table) for dashboard context"""
    dashboard_context_id: str
    table_name: str
    table_schema: str = "public" 
    alias: Optional[str] = None  # User-friendly name
    description: Optional[str] = None
    is_enabled: bool = True
    columns: Optional[List[TableColumn]] = Field(default_factory=list, description="Table column metadata")
    
    @property
    def full_table_name(self) -> str:
        return f"{self.table_schema}.{self.table_name}"
    
    @property
    def display_name(self) -> str:
        return self.alias or self.table_name


class DashboardContext(BaseModel):
    """Dashboard context configuration - reusable across multiple chat sessions"""
    id: Optional[str] = None
    user_id: str
    name: str = Field(description="User-friendly name for the dashboard context")
    description: Optional[str] = Field(None, description="Description of what this context is for")
    datasource_id: str = Field(description="ID of the connected datasource")
    
    # Dashboard context data
    text_context: Optional[str] = Field(None, description="Business context and descriptions")
    json_context: Optional[str] = Field(None, description="Structured metadata as JSON string")
    additional_instructions: Optional[str] = Field(None, description="AI-specific instructions")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatSession(BaseModel):
    """Individual chat conversation tied to a dashboard context"""
    id: Optional[str] = None
    dashboard_context_id: str = Field(description="ID of the dashboard context")
    user_id: str
    name: str = Field(description="User-friendly name for the chat session")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    """Individual message in a chat session"""
    id: Optional[str] = None
    chat_session_id: str = Field(description="ID of the chat session")
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Message content")
    
    # Assistant message metadata
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    query_result: Optional[str] = Field(None, description="JSON string of query results")
    reasoning: Optional[str] = Field(None, description="AI reasoning process")
    
    # Timestamp
    created_at: Optional[datetime] = None


