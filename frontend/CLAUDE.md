# CLAUDE.md - Dashboard Chat Frontend

This file provides guidance to Claude Code when working with the Dashboard Chat frontend (Next.js + React + TypeScript).

## Frontend Overview

The frontend is a Next.js application that provides a 3-step workflow for connecting databases, configuring dashboard context, and chatting with data using AI agents.

## Quick Start

```bash
cd /Users/ishankoradia/Tech4dev/Dalgo/dashboard-chat/frontend

# Install dependencies and start
npm install
npm run dev  # Runs on http://localhost:4000
```

## Development Commands

```bash
# Dependencies
npm install              # Install Node dependencies
npm install <package>    # Add new package

# Development  
npm run dev              # Start Next.js dev server on port 4000 (updated from 3000)
npm run build            # Build for production
npm run start            # Start production server

# Testing & Quality
npm run test             # Jest tests (if configured)
npm run lint             # ESLint
npm run type-check       # TypeScript checking (if configured)
```

## Project Structure

```
frontend/
├── app/                     # Next.js app router
│   ├── page.tsx            # Main 3-step workflow page
│   ├── layout.tsx          # Root layout with metadata
│   └── globals.css         # Global styles and Tailwind
├── components/             # React components
│   ├── DatasourceSetup.tsx     # Step 1: Database connection form
│   ├── DatasetSelection.tsx    # Step 2: Dashboard context config
│   ├── ChatInterface.tsx       # Step 3: Chat UI with query results
│   └── DashboardSelector.tsx   # Legacy dashboard selector
├── types/                  # TypeScript definitions
│   └── index.ts           # All interfaces and types
├── lib/                    # Utilities
│   └── utils.ts           # Helper functions
├── public/                 # Static assets
├── package.json            # Frontend dependencies
├── next.config.js          # Next.js config with API proxy
├── tailwind.config.js      # Tailwind CSS configuration
└── tsconfig.json           # TypeScript configuration
```

## Key Components

### 1. Main Workflow (app/page.tsx)
3-step process with progress indicators and localStorage persistence:

```typescript
type Step = 'datasource' | 'datasets' | 'chat';

// State management
const [currentStep, setCurrentStep] = useState<Step>('datasource');
const [selectedDatasource, setSelectedDatasource] = useState<Datasource | null>(null);
const [dashboardContext, setDashboardContext] = useState<DashboardContext | null>(null);
```

**Steps:**
1. **Connect Database** - Enter PostgreSQL connection details
2. **Dashboard Context** - Select tables and add context information
3. **Chat with Data** - AI-powered chat interface

### 2. DatasourceSetup Component
- Connection form with validation
- Test connection functionality
- Save datasource to backend
- List existing datasources for reuse

### 3. DatasetSelection Component  
- Table discovery and selection
- Business context textarea
- Structured JSON context
- Additional AI instructions
- Real-time table schema viewing

### 4. Enhanced ChatInterface Component
- **Real-time chat** with enhanced AI agent pipeline
- **ReactMarkdown rendering** for proper formatting of assistant responses
- **SQL query result display** with expandable details including:
  - Executed SQL query with syntax highlighting
  - Query execution time and row count
  - Sample results in table format
- **Streaming response support** via Server-Sent Events (SSE)
- **Real-time reasoning tracking** showing step-by-step agent progress
- **Query history** with full context and reasoning
- **Enhanced UX** with loading states and error handling

## TypeScript Interfaces

### Core Types
```typescript
// Database connection
interface Datasource {
  id: string;
  name: string;
  type: 'postgresql';
  host: string;
  port: number;
  database: string;
  username: string;
}

// Dashboard context configuration
interface DashboardContext {
  selectedTables: string[];
  textContext?: string;           // Business descriptions
  jsonContext?: string;           // Structured metadata
  additionalInstructions?: string; // AI-specific instructions
}

// Table information
interface TableInfo {
  name: string;
  schema: string;
  description?: string;
  row_count?: number;
  columns: TableColumn[];
  full_name: string;
}

// Enhanced chat messages
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;  // SQL execution results with data
  reasoning?: string;         // Step-by-step reasoning process
}

// Query execution results
interface QueryResult {
  sql: string;                // Executed SQL query
  data: any[];               // Query result rows
  columns: string[];         // Column names
  rowCount: number;          // Total number of rows
  executionTimeMs: number;   // Query execution time
}
```

## API Integration

### Next.js Proxy Configuration
```javascript
// next.config.js
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:11000/api/:path*',  // Enhanced backend proxy (port 11000)
    },
  ];
}
```

### API Calls
```typescript
// Test database connection
const response = await fetch('/api/v1/test-connection', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(connectionData)
});

// Save datasource
const response = await fetch('/api/v1/datasources', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(datasourceData)
});

// Get tables
const response = await fetch(`/api/v1/datasources/${id}/tables`);
```

## State Management

### LocalStorage Persistence
```typescript
// Save state
localStorage.setItem('selectedDatasource', JSON.stringify(datasource));
localStorage.setItem('dashboardContext', JSON.stringify(context));

// Load state on refresh
useEffect(() => {
  const savedDatasource = localStorage.getItem('selectedDatasource');
  const savedContext = localStorage.getItem('dashboardContext');
  
  if (savedDatasource) {
    setSelectedDatasource(JSON.parse(savedDatasource));
    setCurrentStep('datasets');
  }
  
  if (savedContext) {
    setDashboardContext(JSON.parse(savedContext));
  }
}, []);
```

## Styling

### Tailwind CSS Classes
```css
/* Progress indicators */
.step-active { @apply text-blue-600 bg-blue-100; }
.step-completed { @apply text-green-600 bg-green-100; }
.step-inactive { @apply text-gray-400 bg-gray-100; }

/* Form styling */
.input-field { @apply w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500; }
.button-primary { @apply py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700; }
.button-secondary { @apply py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50; }
```

## Development Patterns

### Adding New Component
1. Create component in `components/`
2. Add TypeScript interfaces in `types/index.ts`
3. Import and use in parent components
4. Add Tailwind CSS styling

### Adding New API Integration
1. Define request/response types in `types/index.ts`
2. Create API call functions in components
3. Handle loading/error states
4. Update UI based on responses

### Form Handling
```typescript
const [formData, setFormData] = useState({
  field1: '',
  field2: ''
});

const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const { name, value } = e.target;
  setFormData(prev => ({
    ...prev,
    [name]: value
  }));
};
```

## Dashboard Context Features

### Table Selection
- Multi-select checkboxes for tables
- Table details expansion (columns, types, sample data)
- Select all/clear all functionality
- Real-time count display

### Business Context
- Freeform text area for business descriptions
- Structured JSON for metadata (metrics, dimensions, filters)
- Additional instructions for AI behavior
- Context validation and formatting

### Context Usage
The dashboard context is passed to the chat interface and used by AI agents:
- **Table selection** determines available data
- **Business context** provides domain knowledge
- **JSON context** structures metadata for better queries
- **Instructions** guide AI response style and focus

## Performance Optimization

### React Optimization
```typescript
// Memoize expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
});

// Use callbacks for event handlers
const handleClick = useCallback(() => {
  // Handler logic
}, [dependencies]);
```

### Next.js Optimization
- Dynamic imports for code splitting
- Image optimization with `next/image`
- Static generation where possible
- API route optimization

## Error Handling

### Component Error Boundaries
```typescript
const [error, setError] = useState<string | null>(null);
const [isLoading, setIsLoading] = useState(false);

try {
  setIsLoading(true);
  const result = await apiCall();
  // Handle success
} catch (error) {
  setError('Failed to perform action');
} finally {
  setIsLoading(false);
}
```

### API Error Display
- User-friendly error messages
- Retry mechanisms
- Loading states
- Validation feedback

## Testing

### Component Testing (if configured)
```typescript
import { render, screen } from '@testing-library/react';
import { DatasourceSetup } from './DatasourceSetup';

test('renders connection form', () => {
  render(<DatasourceSetup onDatasourceSelected={jest.fn()} />);
  expect(screen.getByLabelText(/host/i)).toBeInTheDocument();
});
```

## Common Issues

### TypeScript Errors
- Ensure all interfaces match backend models
- Check import paths for `@/` alias
- Verify component prop types

### API Calls Failing
- Check Next.js proxy configuration
- Verify backend server is running
- Check network/CORS issues

### Styling Issues
- Verify Tailwind CSS configuration
- Check class name conflicts
- Ensure responsive design

## Deployment

### Build Process
```bash
npm run build    # Create production build
npm run start    # Start production server
```

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Static Deployment
- Deploy static files to CDN
- Configure API proxy for production backend
- Add error boundary components
- Optimize images and assets

This frontend architecture provides a modern, type-safe, and responsive interface for the Dashboard Chat application with excellent developer experience and user functionality.