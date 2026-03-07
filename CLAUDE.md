# CLAUDE.md - Dashboard Chat Monorepo

This file provides guidance to Claude Code when working with the Dashboard Chat monorepo.

## Project Overview

Dashboard Chat is a full-stack application that enables users to chat with their databases using AI agents. The system follows a datasource-first approach where users connect their PostgreSQL databases, select tables, and then chat with their data.

## Quick Start

```bash
cd /Users/ishankoradia/Tech4dev/Dalgo/dashboard-chat

# Install all dependencies
npm install
npm run install:all

# Configure backend
cd backend && cp .env.example .env
# Edit .env with OPENAI_API_KEY and other settings

# Start both servers
npm run dev
```

## Development Commands

```bash
# Install dependencies
npm install              # Root dependencies (concurrently)
npm run install:all      # Backend (uv) + Frontend (npm)

# Development
npm run dev              # Start both servers (backend :11000, frontend :4000)
npm run dev:backend      # Python server only
npm run dev:frontend     # Next.js only

# Backend specific (from backend/)
uv sync                  # Install Python dependencies
uv add aiosqlite         # SQLite async support
uv run python -m app.main  # Start FastAPI server (creates data/dashboard_chat.db)
uv run pytest           # Run tests
uv run black .           # Format code
uv run mypy .            # Type checking

# Frontend specific (from frontend/)
npm install              # Install Node dependencies
npm run dev              # Start Next.js dev server
npm run build            # Build for production
npm run lint             # ESLint
```

## Project Structure

```
dashboard-chat/
├── backend/              # Python FastAPI + LangGraph
│   ├── app/
│   │   ├── agents/       # LangGraph multi-agent system
│   │   │   ├── graph.py  # Main orchestration graph
│   │   │   ├── nodes/    # Individual agent nodes
│   │   │   └── types.py  # Agent state definitions
│   │   ├── api/v1/routers/  # FastAPI routes
│   │   │   └── datasources.py  # Datasource management
│   │   ├── models/       # Pydantic models
│   │   │   ├── chat.py   # Chat message models
│   │   │   └── datasource.py  # Database connection models
│   │   ├── services/     # Business logic
│   │   │   ├── datasource_service.py  # DB discovery & management
│   │   │   ├── dashboard_service.py   # Dashboard context (legacy)
│   │   │   └── dbt_service.py         # DBT integration
│   │   ├── tools/        # LangChain tools
│   │   │   ├── database_tool.py  # SQL generation & execution
│   │   │   └── dbt_tool.py       # DBT semantic layer
│   │   ├── core/         # Configuration
│   │   │   └── config.py # Settings and env vars
│   │   └── main.py       # FastAPI app entry point
│   ├── pyproject.toml    # UV project config
│   ├── .env.example      # Environment variables template
│   └── README.md         # Backend docs
├── frontend/             # Next.js React app
│   ├── app/              # Next.js app router
│   │   ├── page.tsx      # Main 3-step workflow page
│   │   ├── layout.tsx    # Root layout
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── ChatInterface.tsx      # Chat UI with query results
│   │   ├── DatasourceSetup.tsx    # Database connection form
│   │   └── DatasetSelection.tsx   # Dashboard context configuration UI
│   ├── types/            # TypeScript definitions
│   │   └── index.ts      # All interfaces and types
│   ├── lib/              # Utilities
│   │   └── utils.ts      # Helper functions
│   ├── package.json      # Frontend dependencies
│   └── next.config.js    # Next.js configuration with API proxy
├── package.json          # Root package.json with dev scripts
└── README.md             # Project documentation
```

## Architecture Overview

### User Workflow
1. **Connect Database** → User enters PostgreSQL connection details and tests connection
2. **Configure Dashboard Context** → Select tables, add business context, structured metadata (JSON), and AI instructions
3. **Chat with Data** → AI agents answer questions using the configured dashboard context with full table schemas and business knowledge

### Data Flow
1. **Datasource** → Saved PostgreSQL connection details
2. **Dashboard Context** → Reusable configuration containing selected tables + context information
3. **Chat Session** → Individual conversation tied to a specific dashboard context
4. **Chat Messages** → User questions and AI responses with SQL queries and results

### Enhanced Agent System (Backend)
The system uses **LangGraph** for multi-agent orchestration with transparent reasoning:

```
User Query → Context Processor → Query Analyzer → Data Planner → SQL Generator → SQL Executor → Insights Generator → Response Formatter
                                                        ↓
                                               General Agent (for non-SQL queries)
```

**Enhanced Agent Pipeline**:
- **Context Processor** (`process_dashboard_context`): Processes dashboard context including datasource info, selected tables, and business context
- **Query Analyzer** (`enhanced_query_analyzer`): Analyzes query intent, complexity, and classification with detailed reasoning
- **Data Planner** (`plan_data_retrieval`): Creates execution strategy - routes between SQL execution vs general responses
- **SQL Generator** (`generate_sql_query`): Schema-aware SQL generation with full table schema discovery and PostgreSQL optimization
- **SQL Executor** (`execute_sql_with_reasoning`): Real PostgreSQL database execution with retry logic and performance tracking
- **Insights Generator** (`generate_data_insights`): LLM-powered analysis of query results with actionable insights and recommendations
- **Response Formatter** (`format_enhanced_response`): Formats final response with insights, data, key metrics, and follow-up questions
- **General Agent** (`handle_general_query`): Handles explanatory and dashboard-related questions that don't require SQL execution

**Key Features**:
- **Transparent Reasoning**: Real-time step-by-step process tracking with `ReasoningStep` model visible in chat
- **Schema-Aware SQL**: Full table schema discovery including column names, data types, and descriptions from PostgreSQL
- **PostgreSQL Optimization**: Proper double-quote column quoting and database-specific syntax handling
- **Streaming Responses**: Server-Sent Events (SSE) for real-time progress updates during execution
- **Real Data Execution**: No mock data - actual PostgreSQL query execution using asyncpg
- **Actionable Insights**: LLM analysis of results with business context, recommendations, and follow-up questions
- **Error Handling**: Comprehensive error handling with retry logic and user-friendly messages
- **Performance Tracking**: Detailed timing for each step including SQL execution time and result row counts

### Frontend Flow
- **Step-based UI** with progress indicators (Connect DB → Dashboard Context → Chat)
- **LocalStorage** persistence for user selections and dashboard context
- **Dashboard Context** includes table selection + business context + structured metadata + AI instructions
- **Real-time chat** with SQL query results display
- **Responsive design** using Tailwind CSS

### Database Storage
- **SQLite database** for persistent storage of datasources and datasets
- **File location**: `/backend/data/dashboard_chat.db`
- **Tables**: `datasources` (connection info), `datasets` (selected tables)
- **Async operations** using `aiosqlite` for performance

## Key Files to Understand

### Backend Core
- `app/agents/graph.py` - Enhanced LangGraph orchestration with complete 8-node pipeline
- `app/agents/orchestrator.py` - Main chat orchestration with streaming SSE support
- `app/agents/nodes/` - Individual agent node implementations:
  - `context_processor.py` - Dashboard context processing
  - `enhanced_query_analyzer.py` - Query intent analysis and classification
  - `data_planner.py` - Execution strategy planning
  - `sql_generation_agent.py` - Schema-aware SQL generation with PostgreSQL optimization
  - `sql_execution_agent.py` - Real database execution with asyncpg
  - `insights_generation_agent.py` - LLM-powered result analysis and insights
  - `general_agent.py` - Non-SQL question handling
- `app/services/datasource_service.py` - Database discovery & table management with full schema introspection
- `app/services/database_service.py` - SQLite persistence layer for datasources/datasets
- `app/models/enhanced_query.py` - Enhanced models for reasoning steps, query results, and insights
- `app/models/datasource.py` - Database connection and table models
- `app/api/v1/routers/datasources.py` - API endpoints for datasource management

### Frontend Core  
- `app/page.tsx` - Main 3-step workflow component with progress indicators and localStorage persistence
- `components/ChatInterface.tsx` - Enhanced chat UI with:
  - ReactMarkdown rendering for proper formatting
  - SQL query result display with expandable details
  - Streaming response support via SSE
  - Query execution timing and row count display
  - Real-time reasoning step tracking
- `components/DatasourceSetup.tsx` - Database connection form with test/save functionality
- `components/DatasetSelection.tsx` - Dashboard context configuration with table selection and business context
- `types/index.ts` - Complete TypeScript interfaces including enhanced models
- `next.config.js` - API proxy configuration to backend (port 11000)

## API Endpoints

### Datasource Management
- `POST /api/v1/test-connection` - Test database connection
- `POST /api/v1/datasources` - Save new datasource  
- `GET /api/v1/datasources` - List user datasources
- `GET /api/v1/datasources/{id}/tables` - Discover tables in datasource

### Dashboard Context Management
- `POST /api/v1/dashboard-contexts/` - Create new dashboard context with tables and additional context
- `GET /api/v1/dashboard-contexts/` - List user dashboard contexts
- `GET /api/v1/dashboard-contexts/{id}` - Get specific dashboard context
- `PUT /api/v1/dashboard-contexts/{id}` - Update dashboard context
- `DELETE /api/v1/dashboard-contexts/{id}` - Delete dashboard context

### Chat Session Management
- `POST /api/v1/chat-sessions/` - Create new chat session for a dashboard context
- `GET /api/v1/chat-sessions/{context_id}` - List chat sessions for dashboard context
- `GET /api/v1/chat-sessions/{session_id}/messages` - Get messages for chat session
- `POST /api/v1/chat-sessions/{session_id}/messages` - Send chat message (supports streaming)
- `DELETE /api/v1/chat-sessions/{session_id}` - Delete chat session

## Key Data Models

### Backend Models (Python/Pydantic)
```python
class DatasourceConnection(BaseModel):
    id: str
    name: str
    type: DatasourceType = DatasourceType.POSTGRESQL
    host: str
    port: int = 5432
    database: str
    username: str
    password: str

class DashboardContext(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    datasource_id: str
    text_context: Optional[str]          # Business context
    json_context: Optional[str]          # Structured metadata
    additional_instructions: Optional[str] # AI instructions

class ChatSession(BaseModel):
    id: str
    dashboard_context_id: str
    user_id: str
    name: str

class ChatMessage(BaseModel):
    id: str
    chat_session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    sql_query: Optional[str]
    query_result: Optional[str]
    reasoning: Optional[str]
```

### Frontend Models (TypeScript)
```typescript
interface DashboardContext {
  id?: string;
  selectedTables: string[];
  textContext?: string;
  jsonContext?: string;
  additionalInstructions?: string;
}

interface ChatRequest {
  message: string;
  dashboardContextId: string;
  stream?: boolean;
  conversation_id?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;
  reasoning?: string;
}
```

## Environment Variables

### Backend (.env)
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

# Storage (auto-created)
# SQLite database: backend/data/dashboard_chat.db
```

## Development Patterns

### Adding New Agent Node
1. Create node function in `backend/app/agents/nodes/`
2. Add to graph in `app/agents/graph.py`
3. Update routing logic in supervisor
4. Add corresponding query type to analyzer

### Adding New API Endpoint
1. Add route to `app/api/v1/routers/`
2. Create request/response models in `app/models/`
3. Implement business logic in `app/services/`
4. Update frontend types in `frontend/types/index.ts`

### Adding New Frontend Component
1. Create component in `frontend/components/`
2. Add TypeScript interfaces in `types/index.ts`
3. Update parent components to use new component
4. Add Tailwind CSS styling

## Testing

### Backend Testing
```bash
cd backend
uv run pytest                    # All tests
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
```

### Frontend Testing  
```bash
cd frontend
npm run test                    # Jest tests
npm run lint                    # ESLint
```

## Common Development Tasks

### Connecting to New Database Type
1. Add new enum to `DatasourceType` in `models/datasource.py`
2. Update connection string generation in `DatasourceConnection`
3. Modify `DatasourceService.test_connection()` for new DB type
4. Add frontend UI support in `DatasourceSetup.tsx`

### Customizing SQL Generation
1. Modify prompts in `tools/database_tool.py`
2. Update `_generate_sql_for_metrics()` or `_generate_sql_for_dimensions()`
3. Test with different query types
4. Add error handling for DB-specific syntax

### Adding New Chat Features
1. Extend `ChatRequest`/`ChatResponse` models
2. Update agent state in `agents/types.py`
3. Modify orchestrator in `agents/orchestrator.py`
4. Update frontend `ChatInterface.tsx`

## Troubleshooting

### Backend Issues
- **Import errors**: Check if all `__init__.py` files exist
- **Database connection**: Verify connection string format and credentials
- **Agent errors**: Check LangGraph node dependencies and state flow
- **404 errors on tables/datasets**: Database persistence now handles this automatically
- **Database locked**: Ensure only one instance running, restart if needed

### Frontend Issues
- **API calls failing**: Check Next.js proxy configuration in `next.config.js`
- **TypeScript errors**: Ensure all interfaces match backend models
- **Styling issues**: Verify Tailwind CSS configuration

### Common Errors
- **"Module not found"**: Run `uv sync` or `npm install`
- **"Connection refused"**: Check if backend server is running on port 11000
- **"Invalid API response"**: Verify request/response model compatibility
- **"Datasource not found"**: Connection persists in database, recreate if needed

## Performance Considerations

### Backend Optimization
- Use async operations throughout
- Implement connection pooling for databases
- Cache table schema discoveries
- Add query result pagination

### Frontend Optimization  
- Implement React.memo for expensive components
- Use Next.js dynamic imports for code splitting
- Add loading states for better UX
- Optimize API call batching

## Security Notes

- Database passwords should be encrypted before storage
- Implement user authentication for multi-tenancy
- Validate all SQL queries before execution
- Add rate limiting for API endpoints
- Sanitize user inputs in chat messages

## Deployment

### Backend Deployment
- Use `uv` for dependency management
- Set production environment variables
- Configure database connection pooling
- Add proper logging and monitoring

### Frontend Deployment
- Build with `npm run build`
- Deploy static files to CDN
- Configure API proxy for production backend
- Add error boundary components

This architecture enables rapid development of AI-powered database chat interfaces with strong type safety, modern tooling, and scalable agent orchestration.

## Code Quality Policy

**IMPORTANT: NO LEGACY OR DEPRECATED CODE**

This project follows a strict no-legacy-code policy across both frontend and backend:

### Backend Policy
- **Remove, don't deprecate**: When refactoring, completely remove old code rather than deprecating it
- **No backward compatibility layers**: Don't maintain compatibility with old systems - implement clean breaks
- **Clean slate approach**: When implementing new features, remove related old implementations entirely
- **No dead code**: Regularly audit and remove unused imports, methods, and files

### Frontend Policy  
- **Remove old components**: Don't keep unused React components around
- **Clean up routes**: Remove old routing logic when implementing new flows
- **Update TypeScript interfaces**: Remove unused type definitions and interfaces
- **Clean imports**: Remove unused imports and dependencies

**Examples of what to avoid:**
- Deprecated API endpoints marked with `@deprecated` 
- Legacy service methods kept "for compatibility"
- Unused React components or pages
- Old routing configurations
- Unused TypeScript interfaces
- Commented-out code blocks
- Old database schemas or migration paths

**Rationale:**
- Reduces cognitive load for developers
- Eliminates maintenance burden of multiple code paths  
- Prevents confusion about which systems to use
- Keeps the codebase clean and focused
- Forces proper planning of breaking changes
- Improves build times and bundle sizes
