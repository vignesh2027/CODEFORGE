from langchain_groq import ChatGroq

from config.settings import GROQ_API_KEY, MODEL_NAME, TEMPERATURE


def get_llm(temperature: float = TEMPERATURE) -> ChatGroq:
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=MODEL_NAME,
        temperature=temperature,
    )


llm = get_llm()
