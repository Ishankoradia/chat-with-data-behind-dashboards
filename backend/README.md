# Dashboard Chat Server

A lightweight multi-agent chat server for dashboard conversations, built with FastAPI and LangGraph.

## Features

- **Multi-Agent Orchestration**: Uses LangGraph to route queries to specialized agents
- **Dashboard Context**: Automatically retrieves dashboard metadata and context
- **DBT Integration**: Optional integration with DBT semantic layer
- **Database Queries**: Generates and executes SQL queries based on natural language
- **Streaming Responses**: Real-time response streaming via Server-Sent Events
- **Type Safety**: Full Pydantic models for request/response validation

## Architecture

```
User Query → Context Processor → Query Analyzer → Supervisor → Specialized Agent → Result Formatter
```

### Agents

1. **Metric Agent**: Handles KPI and metric-related queries
2. **Dimension Agent**: Manages breakdowns and categorical analysis
3. **General Agent**: Answers general dashboard questions

## Quick Start

1. **Clone and setup**:
```bash
cd /Users/ishankoradia/Tech4dev/Dalgo/dashboard-chat-server

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the server**:
```bash
uv run python -m app.main
# or
uv run dashboard-chat-server
```

4. **Test the API**:
```bash
curl -X POST "http://localhost:8001/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What was our revenue last month?",
       "dashboard_id": "dash_1"
     }'
```

## Development Setup

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Code formatting
uv run black .
uv run isort .

# Linting
uv run ruff check .

# Type checking
uv run mypy .
```

## Configuration

### Required Settings

- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string

### Optional Settings

- `DBT_SEMANTIC_LAYER_URL`: DBT semantic layer endpoint
- `DBT_API_KEY`: DBT API key
- `DBT_ENVIRONMENT_ID`: DBT environment ID

## API Endpoints

### POST /chat

Chat with dashboard context.

**Request Body**:
```json
{
  "message": "What was our revenue last month?",
  "dashboard_id": "dash_1",
  "stream": false,
  "context": {
    "dashboard_id": "dash_1",
    "dashboard_name": "Sales Dashboard",
    "metrics": ["revenue", "sales_count"],
    "dimensions": ["month", "region"]
  }
}
```

**Response**:
```json
{
  "response": "Revenue last month was $150,000, showing a 12% increase...",
  "query_result": {
    "sql": "SELECT SUM(revenue) FROM sales WHERE month = '2024-03'",
    "data": [{"total_revenue": 150000}],
    "columns": ["total_revenue"],
    "row_count": 1
  },
  "conversation_id": "uuid-here",
  "reasoning": "Query classified as metric type..."
}
```

### GET /health

Health check endpoint.

## Project Structure

```
dashboard-chat-server/
├── app/
│   ├── agents/          # LangGraph agents and orchestration
│   │   ├── graph.py     # Main agent graph
│   │   ├── types.py     # Agent state definitions
│   │   └── nodes/       # Individual agent nodes
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic services
│   ├── tools/           # Database and DBT tools
│   ├── core/           # Configuration and utilities
│   └── main.py         # FastAPI application
├── tests/              # Test suite
├── pyproject.toml      # Project dependencies and config
└── README.md          # This file
```

## Integration Guide

### Dashboard Service

Implement `DashboardService.get_dashboard_context()` to connect to your dashboard storage:

```python
async def get_dashboard_context(self, dashboard_id: str, org_id: str):
    # Query your dashboard database
    # Extract widgets, metrics, dimensions
    # Return DashboardContext object
    pass
```

### DBT Semantic Layer

Configure DBT settings in `.env` and implement authentication in `DBTService`.

### Database Connection

Update `DATABASE_URL` to point to your data warehouse. The system supports PostgreSQL by default.

## Examples

### Metric Queries
- "What was our revenue last month?"
- "How many new customers did we acquire?"
- "Show me the conversion rate trend"

### Dimension Queries  
- "Break down sales by region"
- "What are our top performing products?"
- "Show me customer segments"

### General Queries
- "Explain this dashboard"
- "What metrics are available?"
- "How is conversion rate calculated?"

## License

MIT License