import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
MAX_CODE_ITERATIONS: int = int(os.getenv("MAX_CODE_ITERATIONS", "3"))
MAX_DEBUG_ATTEMPTS: int = int(os.getenv("MAX_DEBUG_ATTEMPTS", "3"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))

# LangSmith — must be set before any langchain imports
_ls_key = os.getenv("LANGCHAIN_API_KEY", "")
if _ls_key:
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_API_KEY"] = _ls_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "CODEFORGE")
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
        "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
    )

LANGSMITH_ENABLED: bool = bool(_ls_key)
