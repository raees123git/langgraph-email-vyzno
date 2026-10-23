from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_email.workflow.context import EmailContext
from langgraph_email.workflow.nodes import (
    analyze_user_intent_node,
    ask_user_node,
    input_node,
    prepare_draft_node,
    prepare_email_node,
    save_draft_node,
    send_email_node,
)
from langgraph_email.workflow.state import EmailState


def route_user_intent(state: EmailState) -> str:
    return state["user_intent"]


def draft_has_content(state: EmailState) -> bool:
    details = state["model_response"]

    if details.get("validation_errors"):
        return False

    return bool(
        details.get("to")
        or (details.get("subject") or "").strip()
        or (details.get("body_text") or "").strip()
    )


def email_is_complete(state: EmailState) -> bool:
    details = state["model_response"]

    if details.get("validation_errors"):
        return False

    return bool(
        details.get("to")
        and (details.get("subject") or "").strip()
        and (details.get("body_text") or "").strip()
    )


def build_graph():
    builder = StateGraph(
        EmailState
    )

    builder.add_node("input", input_node)
    builder.add_node("analyze_user_intent", analyze_user_intent_node,)
    builder.add_node("prepare_draft", prepare_draft_node)
    builder.add_node("prepare_email", prepare_email_node)
    builder.add_node("save_draft", save_draft_node)
    builder.add_node("send_email", send_email_node)
    builder.add_node("ask_user", ask_user_node)

    builder.add_edge(START, "input")
    builder.add_edge("input", "analyze_user_intent")

    builder.add_conditional_edges(
        "analyze_user_intent",
        route_user_intent,
        {
            "save_draft": "prepare_draft",
            "send_email": "prepare_email",
            "unknown": "ask_user",
        },
    )

    builder.add_conditional_edges(
        "prepare_draft",
        draft_has_content,
        {
            True: "save_draft",
            False: "ask_user",
        },
    )

    builder.add_conditional_edges(
        "prepare_email",
        email_is_complete,
        {
            True: "send_email",
            False: "ask_user",
        },
    )

    builder.add_edge("ask_user", "input")
    builder.add_edge("save_draft", END)
    builder.add_edge("send_email", END)

    return builder.compile(
        checkpointer=InMemorySaver(),
    )