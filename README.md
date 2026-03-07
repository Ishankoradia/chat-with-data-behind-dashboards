# Dashboard Chat Monorepo

A full-stack application that enables users to chat with their PostgreSQL databases using AI agents. Built with FastAPI, LangGraph, Next.js, and enhanced with transparent reasoning and real-time streaming.

## Project Structure

```
dashboard-chat/
├── backend/           # Python FastAPI server with LangGraph agents
│   ├── app/
│   │   ├── agents/    # Multi-agent orchestration
│   │   ├── models/    # Pydantic models
│   │   ├── services/  # Business logic
│   │   ├── tools/     # Database & DBT tools
│   │   └── main.py    # FastAPI app
│   ├── pyproject.toml
│   └── .env.example
├── frontend/          # Next.js React frontend
│   ├── app/          # Next.js app directory
│   ├── components/   # React components
│   ├── lib/          # Utilities
│   ├── types/        # TypeScript types
│   └── package.json
└── package.json       # Root package.json with scripts
```

## Features

### Enhanced Backend
- **8-Node Agent Pipeline**: Enhanced LangGraph orchestration with transparent reasoning
  - Context Processor → Query Analyzer → Data Planner → SQL Generator → SQL Executor → Insights Generator → Response Formatter
- **Schema-Aware SQL Generation**: Full PostgreSQL table discovery with proper column quoting
- **Real Database Execution**: No mock data - actual PostgreSQL query execution using asyncpg
- **Transparent Reasoning**: Step-by-step process tracking visible in real-time
- **LLM-Powered Insights**: Actionable analysis with recommendations and follow-up questions
- **Streaming Responses**: Real-time Server-Sent Events with progress updates
- **3-Step User Workflow**: Connect Database → Configure Context → Chat with Data

### Enhanced Frontend  
- **Next.js 14**: Modern React with App Router and TypeScript
- **Real-time Chat**: Interactive chat with ReactMarkdown rendering and streaming support
- **Database Connection**: PostgreSQL connection form with test/save functionality
- **Dashboard Context**: Table selection with business context and AI instructions
- **Query Results**: Expandable SQL display with execution timing and sample data
- **Responsive Design**: Mobile-friendly Tailwind CSS with proper UX states

## Quick Start

1. **Install dependencies**:
```bash
cd /Users/ishankoradia/Tech4dev/Dalgo/dashboard-chat

# Install root dependencies (concurrently for dev scripts)
npm install

# Install all dependencies
npm run install:all
```

2. **Configure backend**:
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY
# - DATABASE_URL
# - DBT settings (optional)
```

3. **Start development servers**:
```bash
# Start both backend and frontend
npm run dev

# Or start individually:
npm run dev:backend   # Backend on :11000  
npm run dev:frontend  # Frontend on :4000
```

4. **Test the application**:
- Open http://localhost:4000
- Follow the 3-step workflow:
  1. Connect your PostgreSQL database
  2. Select tables and add business context
  3. Chat with your data and get real insights!

## Environment Variables

### Backend (.env)
```bash
# Required
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Optional DBT
DBT_SEMANTIC_LAYER_URL=https://semantic-layer.cloud.getdbt.com
DBT_API_KEY=your_dbt_api_key
DBT_ENVIRONMENT_ID=your_environment_id

# Configuration
DEFAULT_LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
```

## Development Commands

```bash
# Install dependencies
npm run install:all

# Development
npm run dev              # Start both servers
npm run dev:backend      # Backend only (:8001)
npm run dev:frontend     # Frontend only (:3000)

# Testing
npm run test             # Run all tests
npm run test:backend     # Backend tests only
npm run test:frontend    # Frontend tests only

# Building
npm run build            # Build frontend for production
```

## API Endpoints

### POST /chat
Send a chat message to the dashboard.

**Request**:
```json
{
  "message": "What was our revenue last month?",
  "dashboard_id": "dash_1",
  "stream": false
}
```

**Response**:
```json
{
  "response": "Revenue last month was $150,000...",
  "query_result": {
    "sql": "SELECT SUM(revenue) FROM sales...",
    "data": [{"revenue": 150000}],
    "columns": ["revenue"],
    "row_count": 1
  },
  "conversation_id": "uuid",
  "reasoning": "Classified as metric query..."
}
```

## Testing with Your Database

1. **Update database connection**:
   - Modify `DATABASE_URL` in `backend/.env`
   - Update table schemas in `app/tools/database_tool.py`

2. **Customize dashboards**:
   - Edit `app/services/dashboard_service.py` 
   - Update mock dashboards in `frontend/components/DashboardSelector.tsx`

3. **Test queries**:
   - Ask questions about your actual data
   - Review SQL generation quality
   - Monitor query execution times

## Example Queries

**Metric Queries**:
- "What was our revenue last month?"
- "Show me conversion rates by channel"
- "How many new users signed up this week?"

**Dimension Queries**:
- "Break down sales by region"
- "Which products are performing best?"
- "Show customer segments by revenue"

**General Queries**:
- "Explain this dashboard"
- "What metrics are tracked here?"
- "How is churn rate calculated?"

## Architecture

### Agent Flow
```
User Query → Context Processor → Query Analyzer → Supervisor → [Metric/Dimension/General Agent] → Result Formatter
```

### Frontend Components
- **DashboardSelector**: Browse available dashboards
- **ChatInterface**: Real-time chat with query results
- **Message Components**: Styled chat messages with SQL details

## Customization

### Adding New Agents
1. Create agent node in `backend/app/agents/nodes/`
2. Add to graph in `app/agents/graph.py`
3. Update routing logic in supervisor

### Frontend Styling
- Built with Tailwind CSS
- Customizable design system in `tailwind.config.js`
- Component styles in `frontend/components/`

## Production Deployment

### Backend
- Use `uv run` for Python dependency management
- Set up proper database connections
- Configure environment variables
- Add monitoring and logging

### Frontend
- Build with `npm run build`
- Deploy static files to CDN
- Set up API proxying to backend

## License

MIT License