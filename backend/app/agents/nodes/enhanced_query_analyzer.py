"""
Enhanced query analyzer with transparent reasoning and better classification
"""
import time
import logging
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents.types import AgentState
from app.core.config import settings
from app.agents.utils import log_agent_state, create_node_logger

# Configure logger for this node
logger = create_node_logger("enhanced_query_analyzer")
from app.models.enhanced_query import (
    EnhancedQueryAnalysis, 
    QueryType, 
    QueryComplexity, 
    ExecutionPlan,
    ThinkingProcess,
    ReasoningStep
)


class QueryAnalysisResult(BaseModel):
    """Structured output for enhanced query analysis"""
    query_type: QueryType = Field(description="Detailed query type classification")
    complexity: QueryComplexity = Field(description="Query complexity level")
    needs_sql: bool = Field(description="Whether query requires SQL execution")
    suggested_sql_type: str = Field(description="Suggested SQL pattern")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    execution_plan: ExecutionPlan = Field(description="Recommended execution approach")
    reasoning: str = Field(description="Detailed reasoning for this classification")
    relevant_tables: list = Field(default_factory=list, description="Tables likely needed")
    suggested_columns: list = Field(default_factory=list, description="Columns likely needed")


def enhanced_query_analyzer(state: AgentState) -> Dict[str, Any]:
    """
    Enhanced query analysis with transparent reasoning
    """
    # Log incoming state
    log_agent_state(logger, "ENHANCED_QUERY_ANALYZER", state, "input")
    
    print("DEBUG: Enhanced query analyzer executing")
    user_query = state["user_query"]
    dashboard_context = state.get("dashboard_context")
    
    start_time = time.time()
    
    # Initialize thinking process
    thinking_process = ThinkingProcess(
        query_understanding=f"Analyzing query: '{user_query}'",
        reasoning_steps=[],
        decision_rationale="",
        execution_summary=""
    )
    
    # Step 1: Understanding the query
    step1_start = time.time()
    thinking_process.reasoning_steps.append(ReasoningStep(
        step_number=1,
        step_type="understanding",
        title="🧠 Understanding Your Question",
        description=f"Breaking down what you're asking: '{user_query}'",
        status="in_progress"
    ))
    
    try:
        # Build context for analysis
        context_info = ""
        available_tables = []
        
        if dashboard_context:
            datasource = dashboard_context.get("datasource")
            datasets = dashboard_context.get("datasets", [])
            text_context = dashboard_context.get("text_context")
            
            context_info += f"Database: {datasource.name if datasource else 'Unknown'}\n"
            
            if datasets:
                table_info = []
                for dataset in datasets:
                    table_name = getattr(dataset, 'display_name', getattr(dataset, 'table_name', str(dataset)))
                    available_tables.append(table_name)
                    table_info.append(table_name)
                context_info += f"Available tables: {', '.join(table_info)}\n"
            
            if text_context:
                context_info += f"Business Context: {text_context}\n"
        
        step1_duration = (time.time() - step1_start) * 1000
        thinking_process.reasoning_steps[0].duration_ms = step1_duration
        thinking_process.reasoning_steps[0].status = "completed"
        thinking_process.reasoning_steps[0].details = {
            "available_tables": available_tables,
            "has_business_context": bool(dashboard_context and dashboard_context.get("text_context"))
        }
        
        # Step 2: Query classification
        step2_start = time.time()
        thinking_process.reasoning_steps.append(ReasoningStep(
            step_number=2,
            step_type="classification",
            title="🔍 Classifying Query Type",
            description="Determining what kind of analysis you need",
            status="in_progress"
        ))
        
        # Enhanced analysis prompt
        system_prompt = f"""
        You are an expert data analyst assistant. Analyze the user's query and classify it with high precision.

        CONTEXT:
        {context_info}

        QUERY TYPES:
        - SIMPLE_COUNT: Basic counting queries (e.g., "How many NGOs?", "Total users?")
        - AGGREGATION: Sum, average, statistical queries (e.g., "Total revenue?", "Average age?")
        - BREAKDOWN: Dimensional analysis (e.g., "NGOs by region", "Sales by month")
        - COMPARISON: Time series, A/B comparisons (e.g., "This year vs last year")
        - LISTING: Show specific records with filters (e.g., "Show me top 10 customers")
        - GENERAL: Non-data questions, explanations, help

        COMPLEXITY LEVELS:
        - SIMPLE: Single table, basic operations
        - MEDIUM: Multiple tables, joins, complex filters
        - COMPLEX: Advanced analytics, subqueries, calculations

        EXECUTION PLANS:
        - SIMPLE_SQL: Direct single query
        - COMPLEX_SQL: Multi-step or complex query
        - GENERAL_RESPONSE: No SQL needed

        Analyze the query thoroughly and provide detailed reasoning for your classification.
        """
        
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.1,  # Lower temperature for more consistent classification
            openai_api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(QueryAnalysisResult, method="function_calling")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {user_query}")
        ]
        
        analysis_result = llm.invoke(messages)
        
        step2_duration = (time.time() - step2_start) * 1000
        thinking_process.reasoning_steps[1].duration_ms = step2_duration
        thinking_process.reasoning_steps[1].status = "completed"
        thinking_process.reasoning_steps[1].details = {
            "query_type": analysis_result.query_type.value,
            "confidence": analysis_result.confidence_score,
            "needs_sql": analysis_result.needs_sql
        }
        
        # Step 3: Execution planning
        step3_start = time.time()
        thinking_process.reasoning_steps.append(ReasoningStep(
            step_number=3,
            step_type="planning",
            title="📋 Planning Execution",
            description=f"Deciding how to get your answer: {analysis_result.execution_plan.value}",
            status="in_progress"
        ))
        
        # Create enhanced analysis object
        enhanced_analysis = EnhancedQueryAnalysis(
            query_type=analysis_result.query_type,
            complexity=analysis_result.complexity,
            needs_sql=analysis_result.needs_sql,
            suggested_sql_type=analysis_result.suggested_sql_type,
            confidence_score=analysis_result.confidence_score,
            relevant_tables=analysis_result.relevant_tables,
            suggested_columns=analysis_result.suggested_columns,
            execution_plan=analysis_result.execution_plan,
            reasoning=analysis_result.reasoning
        )
        
        step3_duration = (time.time() - step3_start) * 1000
        thinking_process.reasoning_steps[2].duration_ms = step3_duration
        thinking_process.reasoning_steps[2].status = "completed"
        thinking_process.reasoning_steps[2].details = {
            "execution_plan": analysis_result.execution_plan.value,
            "suggested_sql": analysis_result.suggested_sql_type
        }
        
        # Complete thinking process
        total_duration = (time.time() - start_time) * 1000
        thinking_process.decision_rationale = analysis_result.reasoning
        thinking_process.execution_summary = f"Query classified as {analysis_result.query_type.value} with {analysis_result.execution_plan.value} execution plan (confidence: {analysis_result.confidence_score:.2f})"
        
        print("DEBUG: Enhanced query analyzer completed successfully")
        
        result = {
            "enhanced_analysis": enhanced_analysis,
            "execution_plan": analysis_result.execution_plan,
            "query_type": analysis_result.query_type.value,  # For legacy compatibility
            "needs_database_query": analysis_result.needs_sql,  # For legacy compatibility
            "reasoning": analysis_result.reasoning,  # For legacy compatibility
            "thinking_process": thinking_process,
            "current_step": "Query Analysis Complete",
            "step_details": {
                "total_duration_ms": total_duration,
                "confidence": analysis_result.confidence_score
            }
        }
        
        # Log outgoing state changes
        log_agent_state(logger, "ENHANCED_QUERY_ANALYZER", state, "output", result)
        
        return result
        
    except Exception as e:
        # Handle errors transparently
        error_step = ReasoningStep(
            step_number=len(thinking_process.reasoning_steps) + 1,
            step_type="error",
            title="❌ Analysis Error",
            description=f"Encountered an error during analysis: {str(e)}",
            status="failed",
            details={"error": str(e)}
        )
        thinking_process.reasoning_steps.append(error_step)
        
        # Default fallback analysis
        fallback_analysis = EnhancedQueryAnalysis(
            query_type=QueryType.GENERAL,
            complexity=QueryComplexity.SIMPLE,
            needs_sql=False,
            suggested_sql_type="N/A",
            confidence_score=0.1,
            execution_plan=ExecutionPlan.GENERAL_RESPONSE,
            reasoning=f"Error in analysis: {str(e)}. Defaulting to general response."
        )
        
        thinking_process.decision_rationale = f"Due to an error, falling back to general response mode."
        thinking_process.execution_summary = "Analysis failed, using general response approach"
        
        error_result = {
            "enhanced_analysis": fallback_analysis,
            "execution_plan": ExecutionPlan.GENERAL_RESPONSE,
            "query_type": "general",
            "needs_database_query": False,
            "reasoning": f"Error in analysis: {str(e)}",
            "thinking_process": thinking_process,
            "current_step": "Analysis Error",
            "error": str(e),
            "step_details": {"error": str(e)}
        }
        
        # Log error state
        log_agent_state(logger, "ENHANCED_QUERY_ANALYZER", state, "error", error=e)
        
        return error_result