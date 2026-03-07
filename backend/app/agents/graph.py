"""
Enhanced agent orchestration graph with transparent reasoning and SQL execution
"""

from langgraph.graph import StateGraph, START, END

from .types import AgentState
from .nodes.context_processor import process_dashboard_context
from .nodes.enhanced_query_analyzer import enhanced_query_analyzer
from .nodes.data_planner import plan_data_retrieval
from .nodes.sql_generation_agent import generate_sql_query
from .nodes.sql_execution_agent import execute_sql_with_reasoning
from .nodes.insights_generation_agent import generate_data_insights, format_enhanced_response
from .nodes.general_agent import handle_general_query


def route_after_planning(state: AgentState) -> str:
    """Route based on execution plan from data planner"""
    execution_plan = state.get("execution_plan")
    print(f"DEBUG: Routing after planning, execution_plan={execution_plan}")
    if not execution_plan:
        print("DEBUG: No execution plan, routing to general_agent")
        return "general_agent"

    from app.models.enhanced_query import ExecutionPlan

    if (
        execution_plan == ExecutionPlan.SIMPLE_SQL.value
        or execution_plan == ExecutionPlan.COMPLEX_SQL.value
    ):
        print("DEBUG: SQL execution plan, routing to sql_generator")
        return "sql_generator"
    else:
        print(f"DEBUG: Non-SQL execution plan ({execution_plan}), routing to general_agent")
        return "general_agent"


def should_retry_sql(state: AgentState) -> str:
    """Determine if SQL should be retried after execution"""
    should_retry = state.get("should_retry", False)
    if should_retry:
        return "sql_generator"
    else:
        execution_success = state.get("execution_success", False)
        if execution_success:
            return "validate_results"
        else:
            return "generate_insights"


def route_after_validation(state: AgentState) -> str:
    """Route after result validation"""
    results_valid = state.get("results_valid", True)
    if results_valid:
        return "generate_insights"
    else:
        # Could add retry logic here if needed
        return "generate_insights"


def create_enhanced_chat_graph():
    """Create complete enhanced graph with all nodes"""

    graph_builder = StateGraph(AgentState)

    # Add all enhanced nodes
    graph_builder.add_node("process_context", process_dashboard_context)
    graph_builder.add_node("analyze_query", enhanced_query_analyzer)
    graph_builder.add_node("plan_data", plan_data_retrieval)
    graph_builder.add_node("sql_generator", generate_sql_query)
    graph_builder.add_node("execute_sql", execute_sql_with_reasoning)
    graph_builder.add_node("generate_insights", generate_data_insights)
    graph_builder.add_node("format_response", format_enhanced_response)
    graph_builder.add_node("general_agent", handle_general_query)

    # Complete enhanced flow
    graph_builder.add_edge(START, "process_context")
    graph_builder.add_edge("process_context", "analyze_query")
    graph_builder.add_edge("analyze_query", "plan_data")

    # Route based on execution plan
    graph_builder.add_conditional_edges(
        "plan_data",
        route_after_planning,
        {
            "sql_generator": "sql_generator",
            "general_agent": "general_agent",
        },
    )

    # SQL path: generator → execution → insights → formatting
    graph_builder.add_edge("sql_generator", "execute_sql")
    graph_builder.add_edge("execute_sql", "generate_insights")
    graph_builder.add_edge("generate_insights", "format_response")

    # General agent path: general → formatting
    graph_builder.add_edge("general_agent", "format_response")

    # Both paths end at formatting
    graph_builder.add_edge("format_response", END)

    return graph_builder.compile()


# Create the compiled graph
dashboard_chat_graph = create_enhanced_chat_graph()
