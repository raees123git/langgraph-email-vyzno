import asyncio

from langgraph_email.config import Settings
from langgraph_email.mcp_client import create_mcp_client


async def main() -> None:
    settings = Settings()

    async with create_mcp_client(settings) as client:
        tools = await client.list_tools()

        print("Connected to the email MCP server.")
        print("Available tools:", [tool.name for tool in tools])


if __name__ == "__main__":
    asyncio.run(main())