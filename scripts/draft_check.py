import argparse
import asyncio
from uuid import UUID

from fastmcp.exceptions import ToolError

from langgraph_email.config import Settings
from langgraph_email.mcp_client import create_mcp_client


async def main(recipient: str, idempotency_key: UUID) -> None:
    settings = Settings()

    print("Operation key:", idempotency_key)

    try:
        async with create_mcp_client(settings) as client:
            result = await client.call_tool(
                "create_draft",
                {
                    "mailbox_id": str(settings.vyzno_mailbox_id),
                    "draft": {
                        "type": "new",
                        "to": [recipient],
                        "subject": "LangGraph project connection test",
                        "bodyText": (
                            "This draft was created using credentials "
                            "forwarded from the LangGraph project."
                        ),
                        "bodyHtml": (
                            "<p>This draft was created using credentials "
                            "forwarded from the LangGraph project.</p>"
                        ),
                    },
                    "idempotency_key": str(idempotency_key),
                },
                timeout=60.0,
            )

    except ToolError as error:
        print(f"MCP tool failed: {error}")
        raise SystemExit(1) from None

    except Exception as error:
        print(f"Request failed: {type(error).__name__}.")
        print("The outcome is unconfirmed. Keep the operation key.")
        raise SystemExit(1) from None

    data = result.structured_content

    if not isinstance(data, dict) or not data.get("id"):
        print("Unexpected response. Keep the operation key.")
        raise SystemExit(1)

    print("Draft created successfully.")
    print("Draft ID:", data["id"])
    print("Status:", data.get("status"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check draft creation with forwarded Vyzno credentials."
    )
    parser.add_argument("recipient")
    parser.add_argument("--idempotency-key", type=UUID, required=True)
    arguments = parser.parse_args()

    if arguments.idempotency_key.version != 4:
        parser.error("--idempotency-key must be a UUID v4.")

    asyncio.run(
        main(arguments.recipient, arguments.idempotency_key)
    )