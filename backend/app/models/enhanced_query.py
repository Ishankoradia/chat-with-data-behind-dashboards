"""
Enhanced query models for improved SQL execution and result handling
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class QueryComplexity(str, Enum):
    SIMPLE = "simple"  # Single table, basic aggregation
    MEDIUM = "medium"  # Multi-table, joins, complex filters
    COMPLEX = "complex"  # Multiple joins, subqueries, advanced analytics


class QueryType(str, Enum):
    SIMPLE_COUNT = "simple_count"  # COUNT(*) queries
    AGGREGATION = "aggregation"    # SUM, AVG, GROUP BY
    BREAKDOWN = "breakdown"        # Dimensional analysis
    COMPARISON = "comparison"      # Time series, A/B comparisons
    LISTING = "listing"           # SELECT with filters
    GENERAL = "general"           # Non-SQL responses


class ExecutionPlan(str, Enum):
    SIMPLE_SQL = "simple_sql"
    COMPLEX_SQL = "complex_sql" 
    MULTI_STEP_SQL = "multi_step_sql"
    GENERAL_RESPONSE = "general_response"
    USE_CACHED = "use_cached"


class SqlQueryResult(BaseModel):
    """Results from SQL query execution"""
    original_query: str = Field(description="Original user question")
    generated_sql: str = Field(description="Generated SQL query")
    execution_success: bool = Field(description="Whether SQL executed successfully")
    
    # Results - separated for LLM vs frontend use
    llm_results: List[Dict[str, Any]] = Field(default_factory=list, description="Truncated results for LLM processing")
    full_results: List[Dict[str, Any]] = Field(default_factory=list, description="Complete results for frontend display")
    
    # Metadata
    row_count: int = Field(default=0, description="Total number of rows returned")
    execution_time_ms: float = Field(default=0.0, description="Query execution time in milliseconds")
    truncated: bool = Field(default=False, description="Whether results were truncated for LLM")
    
    # Analysis
    insights: Optional[str] = Field(None, description="Generated insights from the data")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from the results")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if execution failed")
    error_type: Optional[str] = Field(None, description="Type of error encountered")
    retry_count: int = Field(default=0, description="Number of retry attempts")


class EnhancedQueryAnalysis(BaseModel):
    """Enhanced query analysis with more detailed classification"""
    query_type: QueryType = Field(description="Detailed query type classification")
    complexity: QueryComplexity = Field(description="Query complexity level")
    needs_sql: bool = Field(description="Whether query requires SQL execution")
    suggested_sql_type: str = Field(description="Suggested SQL pattern (SELECT COUNT, GROUP BY, etc.)")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    
    # Table and column hints
    relevant_tables: List[str] = Field(default_factory=list, description="Tables likely needed for this query")
    suggested_columns: List[str] = Field(default_factory=list, description="Columns likely needed")
    
    # Processing hints
    execution_plan: ExecutionPlan = Field(description="Recommended execution approach")
    reasoning: str = Field(description="Explanation of the analysis decision")


class ReasoningStep(BaseModel):
    """Individual step in the reasoning process"""
    step_number: int = Field(description="Order of this step")
    step_type: str = Field(description="Type of step: analysis, sql_generation, execution, etc.")
    title: str = Field(description="Short title for this step")
    description: str = Field(description="Detailed description of what's happening")
    status: str = Field(description="Status: in_progress, completed, failed")
    duration_ms: Optional[float] = Field(None, description="Time taken for this step")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional step details")


class ThinkingProcess(BaseModel):
    """Complete thinking process for transparency"""
    query_understanding: str = Field(description="How the AI understood the query")
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list, description="Step-by-step reasoning")
    decision_rationale: str = Field(description="Why this approach was chosen")
    execution_summary: str = Field(description="Summary of what was executed")


class DataInsights(BaseModel):
    """Generated insights from query results"""
    summary: str = Field(description="High-level summary of findings")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Important metrics extracted")
    trends: List[str] = Field(default_factory=list, description="Identified trends or patterns")
    outliers: List[str] = Field(default_factory=list, description="Notable outliers or anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    data_limitations: List[str] = Field(default_factory=list, description="Known limitations of the data")


class SchemaInfo(BaseModel):
    """Enhanced schema information for SQL generation"""
    table_name: str
    schema_name: str
    columns: List[Dict[str, Any]]
    row_count: Optional[int] = None
    sample_values: Dict[str, List[Any]] = Field(default_factory=dict)
    relationships: List[Dict[str, str]] = Field(default_factory=list)  # Foreign key relationships