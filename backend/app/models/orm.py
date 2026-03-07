"""
SQLAlchemy ORM models for database entities
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey, 
    func, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DatasourceORM(Base):
    """SQLAlchemy ORM model for datasource connections"""
    __tablename__ = 'chat_datasources'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    ssl_mode = Column(String, default='prefer')
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    dashboard_contexts = relationship("DashboardContextORM", back_populates="datasource")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'id', name='unique_user_datasource'),
    )


class DashboardContextORM(Base):
    """SQLAlchemy ORM model for dashboard contexts"""
    __tablename__ = 'chat_dashboard_contexts'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    datasource_id = Column(String, ForeignKey('chat_datasources.id'), nullable=False)
    text_context = Column(Text)
    json_context = Column(Text)
    additional_instructions = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    datasource = relationship("DatasourceORM", back_populates="dashboard_contexts")
    chat_sessions = relationship("ChatSessionORM", back_populates="dashboard_context")
    datasets = relationship("DatasetORM", back_populates="dashboard_context")


class ChatSessionORM(Base):
    """SQLAlchemy ORM model for chat sessions"""
    __tablename__ = 'chat_sessions'
    
    id = Column(String, primary_key=True)
    dashboard_context_id = Column(String, ForeignKey('chat_dashboard_contexts.id'), nullable=False)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    dashboard_context = relationship("DashboardContextORM", back_populates="chat_sessions")
    messages = relationship("ChatMessageORM", back_populates="chat_session")


class ChatMessageORM(Base):
    """SQLAlchemy ORM model for chat messages"""
    __tablename__ = 'chat_messages'
    
    id = Column(String, primary_key=True)
    chat_session_id = Column(String, ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sql_query = Column(Text)
    query_result = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    chat_session = relationship("ChatSessionORM", back_populates="messages")


class DatasetORM(Base):
    """SQLAlchemy ORM model for datasets (selected tables for dashboard contexts)"""
    __tablename__ = 'chat_datasets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_context_id = Column(String, ForeignKey('chat_dashboard_contexts.id'), nullable=False)
    table_name = Column(String, nullable=False)
    table_schema = Column(String, nullable=False)
    alias = Column(String)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    dashboard_context = relationship("DashboardContextORM", back_populates="datasets")


def get_table_full_name(table_schema: str, table_name: str) -> str:
    """Helper function to get full table name"""
    if table_schema and table_schema.lower() != 'public':
        return f"{table_schema}.{table_name}"
    return table_name