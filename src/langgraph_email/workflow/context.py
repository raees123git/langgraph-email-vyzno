from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_email.config import Settings


@dataclass
class EmailContext:
    model: ChatGoogleGenerativeAI
    settings: Settings