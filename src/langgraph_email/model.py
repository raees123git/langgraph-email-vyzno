from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_email.config import Settings

def create_model(settings: Settings) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key.get_secret_value(),
        vertexai=False,
        timeout=30.0,
        max_retries=2,
    )