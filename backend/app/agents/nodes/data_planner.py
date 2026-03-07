"""
Data planning node - determines optimal execution strategy
"""
import time
from typing import Dict, Any
from app.agents.types import AgentState
from app.models.enhanced_query import ExecutionPlan, ReasoningStep
from app.agents.utils import log_agent_state, create_node_logger

# Configure logger for this node
logger = create_node_logger("data_planner")


def plan_data_retrieval(state: AgentState) -> Dict[str, Any]:
    """
    Determines the best approach for handling the query based on analysis
    """
    # Log incoming state
    log_agent_state(logger, "DATA_PLANNER", state, "input")
    
    logger.debug("Data planner executing")
    enhanced_analysis = state.get("enhanced_analysis")
    thinking_process = state.get("thinking_process")
    
    if not enhanced_analysis or not thinking_process:
        return {
            "error": "Missing enhanced analysis or thinking process",
            "execution_plan": ExecutionPlan.GENERAL_RESPONSE
        }
    
    start_time = time.time()
    
    # Add planning step to thinking process
    planning_step = ReasoningStep(
        step_number=len(thinking_process.reasoning_steps) + 1,
        step_type="data_planning",
        title="🎯 Planning Data Retrieval",
        description="Determining the best way to get your data",
        status="in_progress"
    )
    thinking_process.reasoning_steps.append(planning_step)
    
    try:
        execution_plan = enhanced_analysis.execution_plan
        dashboard_context = state.get("dashboard_context")
        
        # Determine routing based on execution plan and context
        routing_decision = ""
        next_step = ""
        
        if execution_plan == ExecutionPlan.SIMPLE_SQL:
            if enhanced_analysis.needs_sql and dashboard_context:
                routing_decision = "Will execute a single SQL query to get your answer"
                next_step = "sql_generator"
            else:
                routing_decision = "Missing database context, falling back to general response"
                next_step = "general_agent"
                execution_plan = ExecutionPlan.GENERAL_RESPONSE
        
        elif execution_plan == ExecutionPlan.COMPLEX_SQL:
            if enhanced_analysis.needs_sql and dashboard_context:
                routing_decision = "Will execute a complex SQL query with multiple steps"
                next_step = "sql_generator"
            else:
                routing_decision = "Missing database context for complex query, falling back to general response"
                next_step = "general_agent"
                execution_plan = ExecutionPlan.GENERAL_RESPONSE
        
        elif execution_plan == ExecutionPlan.GENERAL_RESPONSE:
            routing_decision = "Will provide a general informational response"
            next_step = "general_agent"
        
        else:
            # Default fallback
            routing_decision = "Using default general response approach"
            next_step = "general_agent"
            execution_plan = ExecutionPlan.GENERAL_RESPONSE
        
        # Complete the planning step
        duration_ms = (time.time() - start_time) * 1000
        planning_step.duration_ms = duration_ms
        planning_step.status = "completed"
        planning_step.description = routing_decision
        planning_step.details = {
            "execution_plan": execution_plan.value,
            "next_step": next_step,
            "requires_sql": enhanced_analysis.needs_sql,
            "has_context": bool(dashboard_context)
        }
        
        # Update thinking process
        thinking_process.execution_summary += f" → {routing_decision}"
        
        logger.debug("Data planner completed successfully")
        
        result = {
            "execution_plan": execution_plan,
            "routing_decision": routing_decision,
            "next_step": next_step,
            "thinking_process": thinking_process,
            "current_step": f"Planning: {routing_decision}",
            "step_details": {
                "execution_plan": execution_plan.value,
                "duration_ms": duration_ms
            }
        }
        
        # Log output state
        log_agent_state(logger, "DATA_PLANNER", state, "output", result)
        
        return result
        
    except Exception as e:
        # Handle planning errors
        duration_ms = (time.time() - start_time) * 1000
        planning_step.duration_ms = duration_ms
        planning_step.status = "failed"
        planning_step.description = f"Planning failed: {str(e)}"
        planning_step.details = {"error": str(e)}
        
        return {
            "execution_plan": ExecutionPlan.GENERAL_RESPONSE,
            "routing_decision": "Planning failed, using general response",
            "next_step": "general_agent",
            "thinking_process": thinking_process,
            "current_step": "Planning Error",
            "error": f"Planning error: {str(e)}",
            "step_details": {"error": str(e)}
        }