import json
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import llm
from state.schema import AgentState

SYSTEM_PROMPT = """You are the Orchestrator Agent in CODEFORGE — a multi-agent code generation system.

Analyze the user's coding task and extract key information.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{
    "task_summary": "Clear, specific description of what needs to be built",
    "language": "python",
    "complexity": "simple|moderate|complex",
    "key_requirements": ["req1", "req2", "req3"]
}

Language must be one of: python, javascript, typescript, java, cpp, rust, go
Default to python if not specified."""


def _parse_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    for delimiter in ["```json", "```"]:
        if delimiter in content:
            content = content.split(delimiter)[1].split("```")[0].strip()
            break
    return json.loads(content)


def orchestrate(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this coding task: {state['task']}"),
    ]

    response = llm.invoke(messages)

    try:
        result = _parse_json(response.content)
        language = result.get("language", "python").lower().strip()
        task_summary = result.get("task_summary", state["task"])
    except (json.JSONDecodeError, KeyError, IndexError):
        language = "python"
        task_summary = state["task"]

    logs = list(state.get("agent_log", []))
    logs.append(f"[ORCHESTRATOR] Task analyzed → Language: {language.upper()}")

    return {
        "task": task_summary,
        "language": language,
        "current_agent": "planner",
        "agent_log": logs,
    }
