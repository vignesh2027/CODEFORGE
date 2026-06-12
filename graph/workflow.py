from langgraph.graph import END, START, StateGraph

from agents.coder import code
from agents.debugger import debug
from agents.executor import execute
from agents.orchestrator import orchestrate
from agents.planner import plan
from agents.reviewer import review
from config.settings import MAX_CODE_ITERATIONS, MAX_DEBUG_ATTEMPTS
from state.schema import AgentState


def _route_after_review(state: AgentState) -> str:
    if state.get("review_approved"):
        return "executor"
    if state.get("code_iteration", 0) >= MAX_CODE_ITERATIONS:
        return "executor"
    return "coder"


def _route_after_execution(state: AgentState) -> str:
    if state.get("execution_success"):
        return END
    if state.get("debug_attempts", 0) >= MAX_DEBUG_ATTEMPTS:
        return END
    return "debugger"


def create_workflow():
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrate)
    graph.add_node("planner", plan)
    graph.add_node("coder", code)
    graph.add_node("reviewer", review)
    graph.add_node("executor", execute)
    graph.add_node("debugger", debug)

    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        _route_after_review,
        {"executor": "executor", "coder": "coder"},
    )

    graph.add_conditional_edges(
        "executor",
        _route_after_execution,
        {END: END, "debugger": "debugger"},
    )

    graph.add_edge("debugger", "coder")

    return graph.compile()
