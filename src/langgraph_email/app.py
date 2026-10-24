import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client
from langchain.mcp import MCPAdapter
from fastmcp.client.transports import StreamableHttpTransport
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from uuid import uuid4



async def main():
    load_dotenv()

    idempotency_key = str(uuid4())

    model = ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL"],
    )

    mcp_transport = StreamableHttpTransport(
    url=os.environ["MCP_URL"],
    headers={
        "vyzno-cookie": os.environ["VYZNO_COOKIE"],
        "vyzno-csrf-token": os.environ["VYZNO_CSRF_TOKEN"],
        "vyzno-mailbox-id": os.environ["VYZNO_MAILBOX_ID"],
        "idempotency-key": idempotency_key
    },
    )


    mcp_client = Client(
        auth=os.getenv("MCP_TOKEN") or None,
        transport=mcp_transport
    )

    async with MCPAdapter(mcp_client) as adapter:
        tools = await adapter.list_tools()


        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=(
                "You are Vyzno's AI email assistant. "
                "use the tools which are available to you to help the user. "
                "If no info is provided, ask for the recipient, subject, and message content. "
            ),
        )

        result = await agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": "save an email draft to my mailbox with the subject 'Meeting Reminder' and the message 'Don't forget about the meeting tomorrow at 10 AM.'",
                }
            ]
        })

        print("Assistant:", result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main())