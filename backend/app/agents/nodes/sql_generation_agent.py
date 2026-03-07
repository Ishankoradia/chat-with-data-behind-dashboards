"""
SQL Generation Agent - creates schema-aware SQL queries with transparent reasoning
"""
import time
import asyncio
import logging
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field, field_validator

from app.agents.types import AgentState
from app.core.config import settings
from app.agents.utils import log_agent_state

# Configure logger for this node
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from app.models.enhanced_query import ReasoningStep
from app.services.datasource_service import DatasourceService


class SqlGenerationResult(BaseModel):
    """Result of SQL generation process"""
    sql_query: str = Field(description="Generated SQL query")
    explanation: str = Field(description="Explanation of what the query does")
    reasoning: str = Field(description="Why this approach was chosen")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the query")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    
    @field_validator('assumptions', mode='before')
    @classmethod
    def validate_assumptions(cls, v):
        """Convert string to list if needed"""
        if isinstance(v, str):
            return [v]  # Convert string to single-item list
        return v


def generate_sql_query(state: AgentState) -> Dict[str, Any]:
    """
    Generate SQL query with schema awareness and transparent reasoning
    """
    # Log incoming state
    logger.info("⚡ SQL_GENERATION_AGENT - Starting")
    logger.info(f"📥 INPUT STATE: {json.dumps({
        'user_query': state.get('user_query', 'N/A'),
        'has_enhanced_analysis': bool(state.get('enhanced_analysis')),
        'has_dashboard_context': bool(state.get('dashboard_context')),
        'execution_plan': str(state.get('execution_plan', 'N/A')),
        'current_step': state.get('current_step'),
        'thinking_process_steps': len(getattr(state.get('thinking_process'), 'reasoning_steps', [])) if state.get('thinking_process') else 0,
        'retry_count': state.get('retry_count', 0),
        'error': state.get('error')
    }, indent=2)}")
    
    logger.debug("SQL generator executing")
    user_query = state["user_query"]
    enhanced_analysis = state.get("enhanced_analysis")
    dashboard_context = state.get("dashboard_context")
    thinking_process = state.get("thinking_process")
    
    # DEBUG: Print complete dashboard context
    print("=" * 80)
    print("🔍 DASHBOARD CONTEXT DEBUG INFO:")
    print("=" * 80)
    
    if dashboard_context:
        print(f"✅ Dashboard context exists: {type(dashboard_context)}")
        
        # Print datasource info
        datasource = dashboard_context.get("datasource")
        if datasource:
            print(f"📊 Datasource: {datasource.name} ({datasource.type}) - {datasource.host}:{datasource.port}/{datasource.database}")
        else:
            print("❌ No datasource found in context")
        
        # Print datasets (tables) info
        datasets = dashboard_context.get("datasets", [])
        print(f"📋 Number of datasets/tables: {len(datasets)}")
        
        for i, dataset in enumerate(datasets):
            print(f"\n🗂️  TABLE {i+1}:")
            if hasattr(dataset, 'table_name'):
                print(f"   Name: {dataset.table_schema}.{dataset.table_name}")
                print(f"   Schema: {dataset.table_schema}")
                print(f"   Alias: {getattr(dataset, 'alias', 'None')}")
                print(f"   Enabled: {getattr(dataset, 'is_enabled', 'Unknown')}")
                # Check if it has column information
                if hasattr(dataset, 'columns') and dataset.columns:
                    print(f"   ✅ Columns: {len(dataset.columns)} available (STORED METADATA)")
                    for col in dataset.columns[:5]:  # Show first 5 columns
                        nullable_str = "NULL" if col.is_nullable else "NOT NULL"
                        desc_str = f" - {col.description}" if col.description else ""
                        print(f"      - {col.name} ({col.data_type}) {nullable_str}{desc_str}")
                    if len(dataset.columns) > 5:
                        print(f"      ... and {len(dataset.columns) - 5} more columns")
                else:
                    print("   ❌ NO COLUMN INFORMATION AVAILABLE")
            else:
                print(f"   Raw dataset object: {type(dataset)} = {dataset}")
        
        # Print business context
        text_context = dashboard_context.get("text_context")
        json_context = dashboard_context.get("json_context") 
        additional_instructions = dashboard_context.get("additional_instructions")
        
        print(f"\n📝 Text context: {'✅ Present' if text_context else '❌ None'}")
        if text_context:
            print(f"   Content: {text_context[:100]}...")
            
        print(f"📋 JSON context: {'✅ Present' if json_context else '❌ None'}")
        if json_context:
            print(f"   Content: {json_context[:100]}...")
            
        print(f"🔧 Additional instructions: {'✅ Present' if additional_instructions else '❌ None'}")
        if additional_instructions:
            print(f"   Content: {additional_instructions[:100]}...")
        
    else:
        print("❌ NO dashboard context found in state!")
    
    print("=" * 80)
    
    if not thinking_process:
        return {"error": "Missing thinking process"}
    
    start_time = time.time()
    
    # Add SQL generation step
    sql_step = ReasoningStep(
        step_number=len(thinking_process.reasoning_steps) + 1,
        step_type="sql_generation",
        title="⚡ Generating SQL Query",
        description="Writing SQL to get your data from the database",
        status="in_progress"
    )
    thinking_process.reasoning_steps.append(sql_step)
    
    try:
        datasource_id = state.get("datasource_id")
        user_id = state.get("user_id")
        
        if not datasource_id or not user_id:
            raise ValueError("Missing datasource_id or user_id")
        
        # Step 1: Get schema information
        schema_step_start = time.time()
        sql_step.description = "📊 Analyzing database schema..."
        
        # Get table info from dashboard context instead of discovering
        dashboard_context = state.get("dashboard_context")
        datasets = dashboard_context.get("datasets", []) if dashboard_context else []
        
        logger.debug(f"Using {len(datasets)} tables from dashboard context")
        logger.debug(f"Dashboard context keys: {list(dashboard_context.keys()) if dashboard_context else 'None'}")
        if datasets:
            logger.debug(f"First dataset: {datasets[0]}")
            logger.debug(f"First dataset type: {type(datasets[0])}")
            logger.debug(f"First dataset attributes: {dir(datasets[0]) if hasattr(datasets[0], '__dict__') else 'No attributes'}")
        
        # Get actual table schemas from database
        schema_info = []
        user_id = state.get("user_id")
        datasource_id = state.get("datasource_id")
        
        if user_id and datasource_id:
            try:
                # We need to get the datasource connection info from the dashboard context
                # instead of creating new database connections here since we're in sync context
                datasource = dashboard_context.get("datasource") if dashboard_context else None
                # Process datasets regardless of datasource availability
                logger.debug(f"Processing {len(datasets)} tables from dashboard context")
                
                for dataset in datasets:
                    dataset_table_name = getattr(dataset, 'table_name', str(dataset))
                    dataset_schema_name = getattr(dataset, 'table_schema', 'public')
                    full_name = f"{dataset_schema_name}.{dataset_table_name}"
                    
                    logger.debug(f"Adding table from dashboard context: {full_name}")
                    
                    # Use stored column information from dataset
                    columns = []
                    row_count = None
                    description = f"Table {full_name} from dashboard context"
                    
                    # Get column information from stored metadata
                    if hasattr(dataset, 'columns') and dataset.columns:
                        columns = [
                            {
                                "name": col.name,
                                "data_type": col.data_type,
                                "nullable": col.is_nullable,
                                "description": col.description
                            }
                            for col in dataset.columns
                        ]
                        print(f"✅ Using stored column metadata: {len(columns)} columns for {full_name}")
                    else:
                        print(f"⚠️ No stored column metadata found for {full_name}")
                    
                    schema_info.append({
                        "table_name": dataset_table_name,
                        "schema_name": dataset_schema_name,
                        "full_name": full_name,
                        "columns": columns,
                        "row_count": row_count,
                        "description": description
                    })
                    
                if datasource:
                    logger.debug(f"Using datasource: {datasource.name}")
                else:
                    logger.debug("No datasource found in dashboard context - using basic table info")
                        
            except Exception as e:
                logger.debug(f"Error getting table schemas: {e}")
                print(f"❌ Error processing datasets: {e}")
        else:
            logger.debug("No user_id or datasource_id available for schema discovery")
        
        # Schema info is already built above from dashboard context
        
        schema_duration = (time.time() - schema_step_start) * 1000
        
        # Step 2: Build schema context for prompt
        sql_step.description = "🧠 Planning SQL query structure..."
        
        schema_context = ""
        if schema_info:
            for table in schema_info:
                schema_context += f"\nTable: {table['full_name']}\n"
                if table.get('description'):
                    schema_context += f"Description: {table['description']}\n"
                schema_context += f"Rows: {table.get('row_count', 'Unknown')}\n"
                schema_context += "Columns:\n"
                
                for col in table['columns'][:10]:  # Limit to first 10 columns
                    # Show column name with proper quoting for PostgreSQL
                    schema_context += f"  - \"{col['name']}\" ({col['data_type']})"
                    if not col['nullable']:
                        schema_context += " NOT NULL"
                    if col.get('description'):
                        schema_context += f" - {col['description']}"
                    schema_context += "\n"
                
                if len(table['columns']) > 10:
                    schema_context += f"  ... and {len(table['columns']) - 10} more columns\n"
        
        # Step 3: Generate SQL with enhanced prompt
        sql_step.description = "✍️ Writing SQL query..."
        
        # Build comprehensive prompt for SQL generation
        sql_prompt = f"""
        You are an expert PostgreSQL analyst. Generate a precise SQL query to answer the user's question.

        USER QUESTION: {user_query}

        QUERY ANALYSIS:
        - Type: {enhanced_analysis.query_type.value if enhanced_analysis else 'Unknown'}
        - Complexity: {enhanced_analysis.complexity.value if enhanced_analysis else 'Unknown'}
        - Suggested SQL Type: {enhanced_analysis.suggested_sql_type if enhanced_analysis else 'Unknown'}

        AVAILABLE SCHEMA:
        {schema_context}

        BUSINESS CONTEXT:
        {dashboard_context.get('text_context', 'No specific business context provided') if dashboard_context else 'No business context'}

        REQUIREMENTS:
        1. Generate ONLY PostgreSQL-compatible SQL
        2. Use exact column names from schema (case-sensitive)
        3. **ALWAYS quote column names with double quotes**: "column_name"
        4. **ALWAYS quote table/schema names if they contain special characters**: "schema"."table"
        5. Always use explicit table aliases for clarity
        6. Include appropriate WHERE clauses if filtering is implied
        7. Use proper aggregations for count/sum questions
        8. Add comments for complex logic
        9. Ensure query is efficient and follows PostgreSQL best practices
        10. If multiple interpretations exist, choose the most logical one

        SAFETY RULES:
        - ONLY use SELECT statements
        - NO DROP, DELETE, UPDATE, INSERT, CREATE, ALTER
        - Include reasonable LIMIT if not specified (default: 1000)
        - Use proper data types in comparisons

        EXAMPLES:
        - "How many NGOs?" → SELECT COUNT(*) as total_ngos FROM "schema"."table_name";
        - "How many unique NGOs?" → SELECT COUNT(DISTINCT "NGO") as unique_ngos FROM "schema"."table_name";
        - "Show NGO names" → SELECT "NGO" FROM "schema"."table_name" LIMIT 10;
        - "NGOs by region" → SELECT region, COUNT(*) as ngo_count FROM schema.table_name GROUP BY region ORDER BY ngo_count DESC;
        
        Provide detailed reasoning for your SQL approach.
        """
        
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.1,  # Low temperature for consistent SQL generation
            openai_api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(SqlGenerationResult, method="function_calling")
        
        messages = [
            SystemMessage(content=sql_prompt),
            HumanMessage(content=f"Generate SQL for: {user_query}")
        ]
        
        sql_result = llm.invoke(messages)
        
        # Complete the SQL generation step
        total_duration = (time.time() - start_time) * 1000
        sql_step.duration_ms = total_duration
        sql_step.status = "completed"
        sql_step.description = f"✅ Generated SQL query: {sql_result.sql_query[:50]}..."
        sql_step.details = {
            "sql_query": sql_result.sql_query,
            "explanation": sql_result.explanation,
            "confidence": sql_result.confidence,
            "schema_analysis_ms": schema_duration,
            "tables_analyzed": len(schema_info) if schema_info else 0
        }
        
        # Update thinking process
        thinking_process.execution_summary += f" → Generated SQL query ({sql_result.confidence:.2f} confidence)"
        
        logger.debug("SQL generator completed successfully")
        
        result = {
            "generated_sql": sql_result.sql_query,
            "sql_explanation": sql_result.explanation,
            "sql_reasoning": sql_result.reasoning,
            "sql_confidence": sql_result.confidence,
            "sql_assumptions": sql_result.assumptions,
            "thinking_process": thinking_process,
            "current_step": f"SQL Generated: {sql_result.explanation}",
            "step_details": {
                "sql_query": sql_result.sql_query,
                "confidence": sql_result.confidence,
                "generation_time_ms": total_duration
            }
        }
        
        # Log output state with generated SQL
        log_agent_state(logger, "SQL_GENERATION_AGENT", state, "output", result)
        
        return result
        
    except Exception as e:
        # Handle SQL generation errors
        duration_ms = (time.time() - start_time) * 1000
        sql_step.duration_ms = duration_ms
        sql_step.status = "failed"
        sql_step.description = f"❌ SQL generation failed: {str(e)}"
        sql_step.details = {"error": str(e)}
        
        thinking_process.execution_summary += f" → SQL generation failed: {str(e)}"
        
        return {
            "error": f"SQL generation failed: {str(e)}",
            "thinking_process": thinking_process,
            "current_step": "SQL Generation Error",
            "step_details": {"error": str(e)}
        }