"""
Dashboard Chat Server - Main FastAPI Application

A lightweight multi-agent chat server for dashboard conversations.
"""

import time
import logging
import sys
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.agents.orchestrator import DashboardChatOrchestrator
from app.api.v1.routers import datasources, dashboard_contexts, chat_sessions

# Configure logging for agent state debugging
def setup_agent_logging():
    """Setup detailed logging for LangGraph agent states"""
    
    # Determine log level based on development/production mode
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    if settings.DEVELOPMENT:
        log_level = logging.DEBUG
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Configure agent-specific loggers
    agent_logger = logging.getLogger('agents.nodes')
    agent_logger.setLevel(logging.DEBUG if settings.DEVELOPMENT else logging.INFO)
    
    # Configure orchestrator logger
    orchestrator_logger = logging.getLogger('app.agents.orchestrator')
    orchestrator_logger.setLevel(logging.DEBUG if settings.DEVELOPMENT else logging.INFO)
    
    # Create console handler for agents if it doesn't exist
    if not agent_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(log_level)
        agent_logger.addHandler(console_handler)
        agent_logger.propagate = False  # Prevent duplicate logs
    
    logging.info(f"🔧 Agent logging configured - Level: {logging.getLevelName(log_level)} | Development: {settings.DEVELOPMENT}")

# Setup logging on startup
setup_agent_logging()

app = FastAPI(
    title="Dashboard Chat Server",
    description="Multi-agent chat system for dashboard interactions",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Performance timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dashboard-chat-server"}


# Include routers
app.include_router(datasources.router, prefix="/api/v1", tags=["datasources"])
app.include_router(dashboard_contexts.router, prefix="/api/v1", tags=["dashboard-contexts"])
app.include_router(chat_sessions.router, prefix="/api/v1", tags=["chat-sessions"])


def start():
    """Start the server"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=11000,
        reload=False,
        log_level="debug",
    )


if __name__ == "__main__":
    start()
