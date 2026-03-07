"""
API routes for chat session management
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.datasource import ChatSession, ChatMessage
from app.models.chat import ChatRequest, ChatResponse
from app.services.postgres_database_service import PostgresDatabaseService, get_postgres_db_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.orchestrator import DashboardChatOrchestrator

router = APIRouter(prefix="/chat-sessions", tags=["chat-sessions"])

# Request/Response models
class CreateChatSessionRequest(BaseModel):
    dashboard_context_id: str
    name: str

class UpdateChatSessionRequest(BaseModel):
    name: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    dashboard_context_id: str
    user_id: str
    name: str
    created_at: Optional[str]
    updated_at: Optional[str]

class ChatMessageResponse(BaseModel):
    id: str
    chat_session_id: str
    role: str
    content: str
    sql_query: Optional[str]
    query_result: Optional[str]
    reasoning: Optional[str]
    created_at: Optional[str]

# Mock user ID function (replace with proper auth)
async def get_current_user_id() -> str:
    return "user_123"  # Temporary hardcoded user ID

@router.post("/", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateChatSessionRequest,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    session = ChatSession(
        id=session_id,
        dashboard_context_id=request.dashboard_context_id,
        user_id=user_id,
        name=request.name
    )
    
    db_service = await get_postgres_db_service(db_session)
    
    # Verify dashboard context exists and belongs to user
    context = await db_service.get_dashboard_context(request.dashboard_context_id, user_id)
    if not context:
        raise HTTPException(status_code=404, detail="Dashboard context not found")
    
    saved_id = await db_service.save_chat_session(session, user_id)
    saved_session = await db_service.get_chat_session(saved_id, user_id)
    
    return ChatSessionResponse(
        id=saved_session.id,
        dashboard_context_id=saved_session.dashboard_context_id,
        user_id=saved_session.user_id,
        name=saved_session.name,
        created_at=str(saved_session.created_at) if saved_session.created_at else None,
        updated_at=str(saved_session.updated_at) if saved_session.updated_at else None
    )

@router.get("/", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    dashboard_context_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the current user, optionally filtered by dashboard context"""
    db_service = await get_postgres_db_service(db_session)
    
    if dashboard_context_id:
        # Verify dashboard context exists and belongs to user
        context = await db_service.get_dashboard_context(dashboard_context_id, user_id)
        if not context:
            raise HTTPException(status_code=404, detail="Dashboard context not found")
        
        sessions = await db_service.list_chat_sessions(dashboard_context_id, user_id)
    else:
        # For now, we'll return empty list since we need a context ID
        # TODO: Implement cross-context session listing if needed
        sessions = []
    
    return [
        ChatSessionResponse(
            id=session.id,
            dashboard_context_id=session.dashboard_context_id,
            user_id=session.user_id,
            name=session.name,
            created_at=str(session.created_at) if session.created_at else None,
            updated_at=str(session.updated_at) if session.updated_at else None
        )
        for session in sessions
    ]

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Get a specific chat session"""
    db_service = await get_postgres_db_service(db_session)
    session = await db_service.get_chat_session(session_id, user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return ChatSessionResponse(
        id=session.id,
        dashboard_context_id=session.dashboard_context_id,
        user_id=session.user_id,
        name=session.name,
        created_at=str(session.created_at) if session.created_at else None,
        updated_at=str(session.updated_at) if session.updated_at else None
    )

@router.put("/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: str,
    request: UpdateChatSessionRequest,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Update an existing chat session"""
    db_service = await get_postgres_db_service(db_session)
    
    # Get existing session
    existing_session = await db_service.get_chat_session(session_id, user_id)
    if not existing_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Update fields
    updated_session = ChatSession(
        id=session_id,
        dashboard_context_id=existing_session.dashboard_context_id,
        user_id=user_id,
        name=request.name if request.name is not None else existing_session.name
    )
    
    await db_service.save_chat_session(updated_session, user_id)
    saved_session = await db_service.get_chat_session(session_id, user_id)
    
    return ChatSessionResponse(
        id=saved_session.id,
        dashboard_context_id=saved_session.dashboard_context_id,
        user_id=saved_session.user_id,
        name=saved_session.name,
        created_at=str(saved_session.created_at) if saved_session.created_at else None,
        updated_at=str(saved_session.updated_at) if saved_session.updated_at else None
    )

@router.delete("/{session_id}")
async def delete_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all messages"""
    db_service = await get_postgres_db_service(db_session)
    
    deleted = await db_service.delete_chat_session(session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return {"message": "Chat session deleted successfully"}

@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = 100,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Get messages for a chat session"""
    db_service = await get_postgres_db_service(db_session)
    
    # Verify session exists and belongs to user
    session = await db_service.get_chat_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = await db_service.get_chat_messages(session_id, limit)
    
    return [
        ChatMessageResponse(
            id=message.id,
            chat_session_id=message.chat_session_id,
            role=message.role,
            content=message.content,
            sql_query=message.sql_query,
            query_result=message.query_result,
            reasoning=message.reasoning,
            created_at=str(message.created_at) if message.created_at else None
        )
        for message in messages
    ]

@router.post("/{session_id}/chat")
async def chat_with_session(
    session_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Send a chat message in a session context"""
    print(f"DEBUG: Chat endpoint reached with session_id={session_id}, message='{request.message}', stream={request.stream}")
    db_service = await get_postgres_db_service(db_session)
    
    # Verify session exists and belongs to user
    session = await db_service.get_chat_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Override session_id from request with URL parameter
    request.chat_session_id = session_id
    
    # Pass database service to orchestrator
    orchestrator = DashboardChatOrchestrator(db_service=db_service)
    
    if request.stream:
        return StreamingResponse(
            orchestrator.stream_session_response(
                message=request.message,
                chat_session_id=session_id,
                user_id=user_id,
            ),
            media_type="text/event-stream",
        )
    
    response = await orchestrator.process_session_message(
        message=request.message,
        chat_session_id=session_id,
        user_id=user_id,
    )
    
    return response