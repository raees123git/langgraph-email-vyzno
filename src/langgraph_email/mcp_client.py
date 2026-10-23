from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from langgraph_email.config import Settings


def create_mcp_client(settings: Settings) -> Client:
    transport = StreamableHttpTransport(
        url=str(settings.mcp_server_url),
        headers={
            "Vyzno-Cookie": (
                settings.vyzno_cookie_header.get_secret_value()
            ),
            "Vyzno-CSRF-Token": (
                settings.vyzno_csrf_token.get_secret_value()
            ),
        },
    )

    return Client(transport, timeout=120.0)