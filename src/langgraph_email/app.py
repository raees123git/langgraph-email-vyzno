import asyncio
from uuid import uuid4


from langgraph_email.config import Settings
from langgraph_email.model import create_model
from langgraph_email.workflow.context import EmailContext
from langgraph_email.workflow.graph import build_graph


def main() -> None:
    settings = Settings()

    context = EmailContext(
        model=create_model(settings),
        settings=settings,
    )

    graph = build_graph()
    print(graph)

    initial_state = {
        "messages": [],
        "user_prompt": "",
        "user_intent": "unknown",
        "model_response": {},
    }
 
    config = {
        "configurable": {
            "thread_id": str(uuid4()),
        },
    }

    result = asyncio.run(
        graph.ainvoke(
            input = initial_state,
            config=config,
            context=context,
        )
    )

    print(f"Assistant: {result['model_response']['message']}")


if __name__ == "__main__":
    main()