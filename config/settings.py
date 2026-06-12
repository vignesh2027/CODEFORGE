import logging
import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
MAX_CODE_ITERATIONS: int = int(os.getenv("MAX_CODE_ITERATIONS", "3"))
MAX_DEBUG_ATTEMPTS: int = int(os.getenv("MAX_DEBUG_ATTEMPTS", "3"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))

# LangSmith — personal token (lsv2_pt_*) must be set before any langchain imports
_ls_key = os.getenv("LANGSMITH_API_KEY", "") or os.getenv("LANGCHAIN_API_KEY", "")
_ls_workspace = os.getenv("LANGSMITH_WORKSPACE_ID", "")

if _ls_key:
    os.environ["LANGSMITH_API_KEY"] = _ls_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "CODEFORGE")
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    # Legacy vars for langchain_core internals
    os.environ["LANGCHAIN_API_KEY"] = _ls_key
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "CODEFORGE")
    if _ls_workspace:
        os.environ["LANGSMITH_WORKSPACE_ID"] = _ls_workspace

# Suppress background-thread trace errors so they don't clutter the terminal
logging.getLogger("langsmith").setLevel(logging.CRITICAL)
logging.getLogger("langchain_core.tracers").setLevel(logging.CRITICAL)

LANGSMITH_ENABLED: bool = bool(_ls_key)
LANGSMITH_WORKSPACE_ID: str = _ls_workspace
