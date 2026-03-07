export interface Datasource {
  id: string;
  name: string;
  type: 'postgresql';
  host: string;
  port: number;
  database: string;
  username: string;
}

export interface TableColumn {
  name: string;
  data_type: string;
  is_nullable: boolean;
  description?: string;
  sample_values?: string[];
}

export interface TableInfo {
  name: string;
  schema: string;
  description?: string;
  row_count?: number;
  columns: TableColumn[];
  full_name: string;
}

export interface Dataset {
  datasource_id: string;
  table_name: string;
  table_schema: string;
  alias?: string;
  description?: string;
  is_enabled: boolean;
  full_table_name: string;
  display_name: string;
}

export interface DashboardContext {
  id?: string;
  selectedTables: string[];
  textContext?: string;
  jsonContext?: string;
  additionalInstructions?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResult?: QueryResult;
  reasoning?: string;
}

export interface QueryResult {
  sql: string;
  data: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time_ms?: number;
}

export interface ChatRequest {
  message: string;
  dashboardContextId: string;
  stream?: boolean;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  query_result?: QueryResult;
  conversation_id: string;
  reasoning?: string;
}

export interface ConnectionTestRequest {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode?: string;
}

export interface SaveDatasourceRequest {
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode?: string;
}