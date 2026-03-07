"""
Insights Generation Agent - analyzes results and creates actionable insights
"""
import time
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents.types import AgentState
from app.core.config import settings
from app.models.enhanced_query import DataInsights, ReasoningStep
from app.agents.utils import log_agent_state, create_node_logger

# Configure logger for this node
logger = create_node_logger("insights_generation_agent")


class InsightGenerationResult(BaseModel):
    """Result of insight generation process"""
    summary: str = Field(description="High-level summary of findings")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Important metrics extracted")
    trends: List[str] = Field(default_factory=list, description="Identified trends or patterns")
    outliers: List[str] = Field(default_factory=list, description="Notable outliers or anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    data_limitations: List[str] = Field(default_factory=list, description="Known limitations of the data")
    context_interpretation: str = Field(description="How to interpret these results")


def generate_data_insights(state: AgentState) -> Dict[str, Any]:
    """
    Generate actionable insights from SQL query results
    """
    # Log incoming state
    log_agent_state(logger, "INSIGHTS_GENERATION_AGENT", state, "input")
    
    print("DEBUG: Insights generation starting")
    sql_query_result = state.get("sql_query_result")
    user_query = state["user_query"]
    enhanced_analysis = state.get("enhanced_analysis")
    dashboard_context = state.get("dashboard_context")
    thinking_process = state.get("thinking_process")
    
    print(f"DEBUG: sql_query_result exists: {sql_query_result is not None}")
    if sql_query_result:
        print(f"DEBUG: sql_query_result.execution_success: {sql_query_result.execution_success}")
        print(f"DEBUG: sql_query_result.row_count: {sql_query_result.row_count}")
    
    if not thinking_process:
        print("DEBUG: Missing thinking process")
        return {"error": "Missing thinking process"}
    
    if not sql_query_result or not sql_query_result.execution_success:
        print(f"DEBUG: No valid SQL results to analyze - sql_query_result: {sql_query_result}, execution_success: {sql_query_result.execution_success if sql_query_result else 'N/A'}")
        return {"error": "No valid SQL results to analyze"}
    
    start_time = time.time()
    
    # Add insights generation step
    insights_step = ReasoningStep(
        step_number=len(thinking_process.reasoning_steps) + 1,
        step_type="insights_generation",
        title="📊 Analyzing Results",
        description="Generating insights from your data",
        status="in_progress"
    )
    thinking_process.reasoning_steps.append(insights_step)
    
    try:
        # Prepare data context for analysis
        results_summary = f"Query returned {sql_query_result.row_count} rows"
        
        # Build context about the data
        data_context = ""
        if dashboard_context:
            datasource = dashboard_context.get("datasource")
            text_context = dashboard_context.get("text_context")
            
            if datasource:
                data_context += f"Data Source: {datasource.name}\n"
            if text_context:
                data_context += f"Business Context: {text_context}\n"
        
        # Format results for analysis (limit for LLM)
        formatted_results = ""
        if sql_query_result.llm_results:
            if len(sql_query_result.llm_results) == 1 and "count" in sql_query_result.generated_sql.lower():
                # Handle count queries specially
                count_result = sql_query_result.llm_results[0]
                count_value = list(count_result.values())[0]
                formatted_results = f"Count result: {count_value}"
            else:
                # Handle other result types
                formatted_results = "Sample results:\n"
                for i, row in enumerate(sql_query_result.llm_results[:10]):  # Limit to first 10 rows
                    formatted_results += f"Row {i+1}: {row}\n"
                
                if sql_query_result.truncated:
                    formatted_results += f"\n(Results truncated - showing {len(sql_query_result.llm_results)} of {sql_query_result.row_count} total rows)"
        
        # Update step description
        insights_step.description = "🧠 Analyzing patterns and trends..."
        
        # Build comprehensive prompt for insight generation
        insights_prompt = f"""
        You are an expert data analyst. Analyze the query results and provide actionable insights.

        USER QUESTION: {user_query}
        
        QUERY ANALYSIS:
        - Type: {enhanced_analysis.query_type.value if enhanced_analysis else 'Unknown'}
        - Complexity: {enhanced_analysis.complexity.value if enhanced_analysis else 'Unknown'}
        
        DATA CONTEXT:
        {data_context}
        
        SQL EXECUTED:
        {sql_query_result.generated_sql}
        
        RESULTS:
        {formatted_results}
        
        EXECUTION DETAILS:
        - Rows returned: {sql_query_result.row_count}
        - Execution time: {sql_query_result.execution_time_ms:.1f}ms
        - Query successful: {sql_query_result.execution_success}
        
        INSTRUCTIONS:
        1. **ALWAYS USE THE EXACT NUMBERS FROM THE RESULTS SECTION ABOVE** - Never use placeholders like "X" or "Y"
        2. Start with a clear, direct answer using the actual data values
        3. Extract key metrics and insights from the data
        4. Identify any interesting patterns, trends, or outliers
        5. Suggest actionable recommendations based on the findings
        6. Propose relevant follow-up questions for deeper analysis
        7. Note any data limitations or considerations
        8. Interpret the context and business implications
        
        CRITICAL: Your summary MUST include the actual numbers from the query results. Never use generic placeholders.
        
        STYLE GUIDELINES:
        - Be conversational yet professional
        - Lead with the direct answer using ACTUAL NUMBERS from the results
        - Use clear, non-technical language
        - Focus on actionable insights, not just data description
        - Include relevant business context when available
        - Suggest specific next steps for exploration
        
        EXAMPLES:
        - For count queries: "There are [ACTUAL NUMBER] records, which represents..."
        - For breakdowns: "The distribution shows that..."
        - For trends: "Over time, we can see..."
        """
        
        llm = ChatOpenAI(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=0.3,  # Slightly higher for more creative insights
            openai_api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(InsightGenerationResult, method="function_calling")
        
        messages = [
            SystemMessage(content=insights_prompt),
            HumanMessage(content=f"Analyze results for: {user_query}")
        ]
        
        print(f"DEBUG: Insights generation - formatted_results: {formatted_results}")
        print(f"DEBUG: Insights generation - sending to LLM with {sql_query_result.row_count} rows")
        
        # Use sync invoke instead of async ainvoke
        insights_result = llm.invoke(messages)
        
        # Create DataInsights object
        data_insights = DataInsights(
            summary=insights_result.summary,
            key_metrics=insights_result.key_metrics,
            trends=insights_result.trends,
            outliers=insights_result.outliers,
            recommendations=insights_result.recommendations,
            follow_up_questions=insights_result.follow_up_questions,
            data_limitations=insights_result.data_limitations
        )
        
        # Complete the insights generation step
        total_duration = (time.time() - start_time) * 1000
        insights_step.duration_ms = total_duration
        insights_step.status = "completed"
        insights_step.description = "✅ Generated insights with key findings and recommendations"
        insights_step.details = {
            "summary": insights_result.summary,
            "key_metrics_count": len(insights_result.key_metrics),
            "trends_identified": len(insights_result.trends),
            "recommendations_count": len(insights_result.recommendations),
            "follow_up_questions_count": len(insights_result.follow_up_questions)
        }
        
        thinking_process.execution_summary += f" → Generated insights and recommendations"
        
        result = {
            "generated_insights": data_insights,
            "insights_summary": insights_result.summary,
            "context_interpretation": insights_result.context_interpretation,
            "thinking_process": thinking_process,
            "current_step": f"Insights Complete: {insights_result.summary[:100]}...",
            "step_details": insights_step.details
        }
        
        # Log output state
        log_agent_state(logger, "INSIGHTS_GENERATION_AGENT", state, "output", result)
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        insights_step.duration_ms = duration_ms
        insights_step.status = "failed"
        insights_step.description = f"❌ Insights generation failed: {str(e)}"
        insights_step.details = {"error": str(e)}
        
        thinking_process.execution_summary += f" → Insights generation failed: {str(e)}"
        
        # Create fallback insights
        fallback_insights = DataInsights(
            summary=f"Query executed successfully returning {sql_query_result.row_count} results, but insight generation failed.",
            key_metrics={},
            trends=[],
            outliers=[],
            recommendations=["Review the raw data in the results tab for manual analysis"],
            follow_up_questions=[],
            data_limitations=[f"Automated analysis failed: {str(e)}"]
        )
        
        error_result = {
            "generated_insights": fallback_insights,
            "insights_error": str(e),
            "thinking_process": thinking_process,
            "current_step": f"Insights Error: {str(e)}",
            "error": str(e),
            "step_details": {"error": str(e)}
        }
        
        # Log error state
        log_agent_state(logger, "INSIGHTS_GENERATION_AGENT", state, "error", error_result, e)
        
        return error_result


def format_enhanced_response(state: AgentState) -> Dict[str, Any]:
    """
    Format the final response with insights, data, and transparency
    """
    # Log incoming state
    log_agent_state(logger, "RESPONSE_FORMATTER", state, "input")
    
    print("DEBUG: Format enhanced response starting")
    generated_insights = state.get("generated_insights")
    sql_query_result = state.get("sql_query_result")
    thinking_process = state.get("thinking_process")
    user_query = state["user_query"]
    
    print(f"DEBUG: generated_insights exists: {generated_insights is not None}")
    print(f"DEBUG: sql_query_result exists: {sql_query_result is not None}")
    
    if not thinking_process:
        return {"error": "Missing thinking process"}
    
    start_time = time.time()
    
    # Add final formatting step
    format_step = ReasoningStep(
        step_number=len(thinking_process.reasoning_steps) + 1,
        step_type="response_formatting",
        title="✨ Formatting Response",
        description="Preparing your final answer with insights",
        status="in_progress"
    )
    thinking_process.reasoning_steps.append(format_step)
    
    try:
        # Build the final response
        response_parts = []
        
        # Start with direct answer
        if generated_insights:
            response_parts.append(generated_insights.summary)
            
            # Add key metrics if available
            if generated_insights.key_metrics:
                response_parts.append("\n**Key Findings:**")
                for metric, value in generated_insights.key_metrics.items():
                    response_parts.append(f"• {metric}: {value}")
            
            # Add trends if identified
            if generated_insights.trends:
                response_parts.append("\n**Patterns & Trends:**")
                for trend in generated_insights.trends:
                    response_parts.append(f"• {trend}")
            
            # Add recommendations
            if generated_insights.recommendations:
                response_parts.append("\n**Recommendations:**")
                for rec in generated_insights.recommendations:
                    response_parts.append(f"• {rec}")
            
            # Add follow-up questions
            if generated_insights.follow_up_questions:
                response_parts.append("\n**Explore Further:**")
                for question in generated_insights.follow_up_questions:
                    response_parts.append(f"• \"{question}\"")
            
            # Add data context and limitations
            if sql_query_result:
                response_parts.append(f"\n**Query Details:**")
                response_parts.append(f"• Executed in {sql_query_result.execution_time_ms:.0f}ms")
                response_parts.append(f"• Analyzed {sql_query_result.row_count} records")
                if sql_query_result.truncated:
                    response_parts.append(f"• Results truncated for display (see full data in results tab)")
            
            if generated_insights.data_limitations:
                response_parts.append("\n**Data Notes:**")
                for limitation in generated_insights.data_limitations:
                    response_parts.append(f"• {limitation}")
        
        else:
            # Fallback response if no insights
            response_parts.append(f"I executed your query successfully.")
            if sql_query_result:
                response_parts.append(f"Found {sql_query_result.row_count} results in {sql_query_result.execution_time_ms:.0f}ms.")
                response_parts.append("Please check the results tab for detailed data.")
        
        final_response = "\n".join(response_parts)
        
        # Complete formatting step
        duration_ms = (time.time() - start_time) * 1000
        format_step.duration_ms = duration_ms
        format_step.status = "completed"
        format_step.description = "✅ Response ready with insights and recommendations"
        format_step.details = {
            "response_length": len(final_response),
            "includes_insights": bool(generated_insights),
            "includes_recommendations": bool(generated_insights and generated_insights.recommendations),
            "includes_follow_ups": bool(generated_insights and generated_insights.follow_up_questions)
        }
        
        thinking_process.execution_summary += " → Final response formatted"
        
        result = {
            "final_response": final_response,
            "thinking_process": thinking_process,
            "current_step": "Response Complete",
            "step_details": format_step.details,
            "query_result": {
                "sql": sql_query_result.generated_sql if sql_query_result else None,
                "data": sql_query_result.full_results if sql_query_result else None,
                "columns": list(sql_query_result.full_results[0].keys()) if sql_query_result and sql_query_result.full_results else [],
                "row_count": sql_query_result.row_count if sql_query_result else 0,
                "execution_time_ms": sql_query_result.execution_time_ms if sql_query_result else 0
            } if sql_query_result else None
        }
        
        # Log output state
        log_agent_state(logger, "RESPONSE_FORMATTER", state, "output", result)
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        format_step.duration_ms = duration_ms
        format_step.status = "failed"
        format_step.description = f"❌ Response formatting failed: {str(e)}"
        format_step.details = {"error": str(e)}
        
        # Create minimal fallback response
        fallback_response = f"I processed your query '{user_query}' but encountered an issue formatting the response. "
        if sql_query_result and sql_query_result.execution_success:
            fallback_response += f"The SQL query executed successfully returning {sql_query_result.row_count} results."
        
        error_result = {
            "final_response": fallback_response,
            "thinking_process": thinking_process,
            "current_step": f"Formatting Error: {str(e)}",
            "error": str(e),
            "step_details": {"error": str(e)}
        }
        
        # Log error state
        log_agent_state(logger, "RESPONSE_FORMATTER", state, "error", error_result, e)
        
        return error_result