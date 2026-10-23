from typing import Any, Literal, TypedDict, Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class EmailState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_prompt: str
    user_intent: Literal["save_draft", "send_email", "unknown"]
    model_response: dict[str, Any]