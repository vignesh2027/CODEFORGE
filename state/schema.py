from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    task: str
    plan: str
    language: str
    code: str
    code_iteration: int
    review_feedback: str
    review_approved: bool
    execution_output: str
    execution_success: bool
    debug_attempts: int
    debug_notes: str
    current_agent: str
    agent_log: List[str]
    final_code: str
    final_explanation: str
    messages: Annotated[List[BaseMessage], add_messages]
