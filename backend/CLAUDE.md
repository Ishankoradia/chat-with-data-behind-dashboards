# CLAUDE.md - Dashboard Chat Backend

This file provides guidance to Claude Code when working with the Dashboard Chat backend (Python FastAPI + LangGraph).

## Backend Overview

The backend is a FastAPI application with a multi-agent LangGraph system that enables users to chat with their databases using AI. It handles database connections, table discovery, and chat orchestration.

## Quick Start

```bash
cd /Users/ishankoradia/Tech4dev/Dalgo/dashboard-chat/backend

# Setup environment
cp .env.example .env
# Edit .env with OPENAI_API_KEY and database settings

# Install dependencies and start server
uv sync
uv run python -m app.main  # Runs on http://localhost:11000
```

## Development Commands

```bash
# Dependencies
uv sync                  # Install Python dependencies
uv add <package>         # Add new package

# Development
uv run python -m app.main  # Start FastAPI server on port 11000
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 11000  # Alternative

# Testing & Quality
uv run pytest           # Run tests
uv run pytest -m unit   # Unit tests only
uv run pytest -m integration  # Integration tests only
uv run black .          # Format code
uv run mypy .           # Type checking
uv run ruff .           # Linting
```

## Project Structure

```
backend/
├── app/
│   ├── agents/              # Enhanced LangGraph multi-agent system
│   │   ├── graph.py         # Main orchestration graph (8-node pipeline)
│   │   ├── orchestrator.py  # Chat orchestration with streaming SSE
│   │   ├── nodes/           # Individual agent nodes (all sync functions)
│   │   │   ├── context_processor.py         # Dashboard context processing
│   │   │   ├── enhanced_query_analyzer.py   # Query intent analysis & classification
│   │   │   ├── data_planner.py              # Execution strategy planning
│   │   │   ├── sql_generation_agent.py      # Schema-aware SQL generation with PostgreSQL optimization
│   │   │   ├── sql_execution_agent.py       # Real database execution with asyncpg
│   │   │   ├── insights_generation_agent.py # LLM-powered result analysis & insights
│   │   │   └── general_agent.py             # Non-SQL question handling
│   │   └── types.py         # Enhanced agent state definitions
│   ├── api/v1/routers/      # FastAPI routes
│   │   └── datasources.py   # Datasource management endpoints
│   ├── models/              # Pydantic models
│   │   ├── chat.py          # Chat message models
│   │   ├── datasource.py    # Database connection models
│   │   └── enhanced_query.py # Enhanced models for reasoning, results, and insights
│   ├── services/            # Business logic
│   │   ├── datasource_service.py  # DB discovery & management
│   │   ├── database_service.py    # SQLite persistence layer
│   │   ├── dashboard_service.py   # Dashboard context (legacy)
│   │   └── dbt_service.py         # DBT integration
│   ├── tools/               # LangChain tools
│   │   ├── database_tool.py # SQL generation & execution
│   │   └── dbt_tool.py      # DBT semantic layer
│   ├── core/                # Configuration
│   │   └── config.py        # Settings and env vars
│   └── main.py              # FastAPI app entry point
├── data/                    # SQLite database storage
│   └── dashboard_chat.db    # SQLite database (auto-created)
├── tests/                   # Test files
├── pyproject.toml          # UV project configuration
├── .env.example            # Environment variables template
└── LICENSE                 # MIT License
```

## Key Components

### 1. Enhanced Agent System (LangGraph)
The enhanced multi-agent system uses LangGraph for orchestration with transparent reasoning:

```
User Query → Context Processor → Query Analyzer → Data Planner → SQL Generator → SQL Executor → Insights Generator → Response Formatter
                                                        ↓
                                               General Agent (for non-SQL queries)
```

**Enhanced Agent Nodes** (All sync functions calling async operations internally):
- **Context Processor** (`process_dashboard_context`): Processes dashboard context including datasource, selected tables, and business context
- **Query Analyzer** (`enhanced_query_analyzer`): Analyzes query intent, complexity, and classification with detailed reasoning
- **Data Planner** (`plan_data_retrieval`): Creates execution strategy - routes between SQL execution vs general responses  
- **SQL Generator** (`generate_sql_query`): Schema-aware SQL generation with full PostgreSQL table schema discovery and proper column quoting
- **SQL Executor** (`execute_sql_with_reasoning`): Real PostgreSQL database execution using asyncpg with retry logic and performance tracking
- **Insights Generator** (`generate_data_insights`): LLM-powered analysis of query results generating actionable insights and recommendations
- **Response Formatter** (`format_enhanced_response`): Formats final response with insights, key metrics, trends, and follow-up questions
- **General Agent** (`handle_general_query`): Handles explanatory and dashboard-related questions that don't require SQL execution

**Key Features:**
- **Transparent Reasoning**: Step-by-step process tracking with `ReasoningStep` model streamed to frontend
- **Real-time Streaming**: Server-Sent Events (SSE) for live progress updates during execution
- **Schema Discovery**: Full PostgreSQL table introspection with columns, data types, and descriptions
- **No Mock Data**: All results come from actual database execution using asyncpg
- **PostgreSQL Optimization**: Proper double-quote column quoting and database-specific syntax
- **Performance Tracking**: Detailed timing for each step and SQL execution metrics

### 2. Enhanced Models and Types

**Core Enhanced Models** (`models/enhanced_query.py`):
- **ReasoningStep**: Tracks individual steps in the reasoning process with status, duration, and details
- **ThinkingProcess**: Contains all reasoning steps and execution summary for transparency
- **SqlQueryResult**: Complete query execution results with timing and metadata
- **DataInsights**: LLM-generated insights with key metrics, trends, recommendations, and follow-up questions
- **QueryClassification**: Enhanced query analysis with type, complexity, and confidence
- **ExecutionPlan**: Strategy for handling different query types (SIMPLE_SQL, COMPLEX_SQL, GENERAL_RESPONSE)

**Agent State** (`agents/types.py`):
Enhanced state management for the LangGraph pipeline including all intermediate results, reasoning steps, and context information.

### 3. Database Service
- **SQLite persistence** for datasources and datasets using `aiosqlite`
- **Async operations** with connection pooling via context managers
- **Schema management** with auto-migration
- **Full table schema discovery** with PostgreSQL introspection

### 4. Datasource Service
- **Connection testing and validation** for PostgreSQL databases
- **Advanced table discovery** with full schema introspection including:
  - Column names, data types, nullability
  - Table descriptions and row counts
  - Schema and full table name resolution
- **User dataset management** via database service integration
- **Connection string generation** with SSL support and error handling

## API Endpoints

### Datasource Management
```python
POST /api/v1/test-connection     # Test database connection
POST /api/v1/datasources         # Save new datasource  
GET  /api/v1/datasources         # List user datasources
GET  /api/v1/datasources/{id}/tables    # Discover tables
POST /api/v1/datasources/{id}/datasets  # Save selected tables
GET  /api/v1/datasources/{id}/datasets  # Get selected tables
```

### Chat
```python
POST /chat  # Enhanced chat with streaming SSE support
# Features:
# - Real-time reasoning step tracking
# - SQL generation and execution
# - LLM-powered insights generation
# - Streaming progress updates
# - Complete query result display
```

## Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/db  # Default connection

# Optional
DBT_SEMANTIC_LAYER_URL=https://semantic-layer.cloud.getdbt.com
DBT_API_KEY=your_dbt_api_key  
DBT_ENVIRONMENT_ID=your_environment_id

# Configuration
DEFAULT_LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
CORS_ORIGINS=["http://localhost:4000"]  # Updated for new frontend port
```

## Data Models

### Core Models
```python
# Datasource Connection
class DatasourceConnection(BaseModel):
    name: str
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"

# Table Information
class TableInfo(BaseModel):
    name: str
    schema: str
    description: Optional[str]
    row_count: Optional[int]
    columns: List[TableColumn]
    full_name: str

# Dataset Selection
class Dataset(BaseModel):
    datasource_id: str
    table_name: str
    table_schema: str
    is_enabled: bool
    full_table_name: str
```

## Development Patterns

### Adding New Agent Node
1. Create node function in `app/agents/nodes/`
2. Add to graph in `app/agents/graph.py`
3. Update routing logic in supervisor
4. Add corresponding query type to analyzer

### Adding New API Endpoint
1. Add route to `app/api/v1/routers/`
2. Create request/response models in `app/models/`
3. Implement business logic in `app/services/`
4. Update tests

### Customizing SQL Generation
1. Modify prompts in `tools/database_tool.py`
2. Update `_generate_sql_for_metrics()` or `_generate_sql_for_dimensions()`
3. Test with different query types
4. Add error handling for DB-specific syntax

## Testing

```bash
# Run all tests
uv run pytest

# Specific test types
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only

# With coverage
uv run pytest --cov=app --cov-report=html
```

## Common Issues

### Database Connection
- Verify connection string format: `postgresql://user:pass@host:port/db`
- Check firewall/network access
- Ensure PostgreSQL version compatibility

### Agent Errors
- Check LangGraph node dependencies
- Verify agent state flow in `types.py`
- Review error logs for specific node failures

### Import Errors
- Ensure all `__init__.py` files exist
- Check Python path configuration
- Verify package structure

## Performance Optimization

- Use async operations throughout
- Implement connection pooling for databases
- Cache table schema discoveries
- Add query result pagination
- Optimize LLM prompts for faster responses

## Security Considerations

- Database passwords should be encrypted before storage
- Validate all SQL queries before execution
- Add rate limiting for API endpoints
- Sanitize user inputs in chat messages
- Use environment variables for sensitive data

## Deployment

### Local Development
- Use `uv` for dependency management
- Set development environment variables
- Use `--reload` for auto-restart during development

### Production
- Set production environment variables
- Configure database connection pooling
- Add proper logging and monitoring
- Use process managers like systemd or Docker
- Enable HTTPS and security headers

This backend architecture enables rapid development of AI-powered database chat interfaces with strong type safety, async performance, and scalable agent orchestration.

## Code Quality Policy

**IMPORTANT: NO LEGACY OR DEPRECATED CODE**

This project follows a strict no-legacy-code policy:

- **Remove, don't deprecate**: When refactoring or changing architecture, completely remove old code rather than deprecating it
- **No backward compatibility layers**: Don't maintain compatibility with old systems - implement clean breaks
- **Clean slate approach**: When implementing new features, remove related old implementations entirely
- **No dead code**: Regularly audit and remove unused imports, methods, and files
- **Documentation updates**: When removing old systems, update all documentation immediately

**Examples of what to avoid:**
- Deprecated endpoints marked with `@deprecated` 
- Legacy service methods kept "for compatibility"
- Unused imports or model fields
- Old database schemas or migration paths
- Commented-out code blocks

**Rationale:**
- Reduces cognitive load for developers
- Eliminates maintenance burden of multiple code paths
- Prevents confusion about which systems to use
- Keeps the codebase clean and focused
- Forces proper planning of breaking changes