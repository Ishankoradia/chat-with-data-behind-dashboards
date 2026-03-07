"""
Chat models for dashboard interactions
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    chat_session_id: str
    stream: bool = False


class QueryResult(BaseModel):
    """Result of a database query"""
    sql: str
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    query_result: Optional[QueryResult] = None
    chat_session_id: str
    message_id: str
    reasoning: Optional[str] = None  # For debugging/transparency