from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import llm
from state.schema import AgentState

SYSTEM_PROMPT = """You are the Planner Agent in CODEFORGE — a senior software architect.

Create a detailed, numbered implementation plan for the given coding task.

Your plan must:
1. Break the task into clear, logical steps
2. Identify all required functions, classes, and data structures
3. List any external libraries or dependencies needed
4. Note important edge cases and error handling requirements
5. Specify the expected inputs and outputs

Be specific and actionable — the Coder Agent will follow this plan exactly."""


def plan(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Create a detailed implementation plan for:

Task: {state['task']}
Language: {state['language']}

Provide a numbered, step-by-step plan that covers all aspects of the implementation."""
        ),
    ]

    response = llm.invoke(messages)

    logs = list(state.get("agent_log", []))
    logs.append("[PLANNER] Implementation plan created")

    return {
        "plan": response.content,
        "current_agent": "coder",
        "agent_log": logs,
    }
