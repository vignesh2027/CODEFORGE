from langchain_groq import ChatGroq

from config.settings import GROQ_API_KEY, MODEL_NAME, TEMPERATURE


def get_llm(temperature: float = TEMPERATURE) -> ChatGroq:
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=temperature,
        max_retries=3,        # auto-retry on 429 rate limits with backoff
        request_timeout=60,
    )


llm = get_llm()
