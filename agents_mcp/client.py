from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP_SERVERS = {
#     "hotel-service": {
#         "url": "http://localhost:8001/mcp",
#         "transport": "streamable_http",
#     },
#     "flight-service": {
#         "url": "http://localhost:8002/mcp",
#         "transport": "streamable_http",
#     },
# }

HOTEL_SERVICE_URL = os.environ.get("HOTEL_SERVER_URL", "http://localhost:8001").rstrip("/") + "/mcp"
FLIGHT_SERVICE_URL = os.environ.get("FLIGHT_SERVER_URL", "http://localhost:8002").rstrip("/") + "/mcp"

MCP_SERVERS = {
    "hotel-service": {
        "url": "HOTEL_SERVICE_URL",
        "transport": "streamable_http",
    },
    "flight-service": {
        "url": "FLIGHT_SERVICE_URL",
        "transport": "streamable_http",
    },
}

client = None
tools = None


async def get_tools():

    global client
    global tools

    if tools is not None:
        return tools

    client = MultiServerMCPClient(MCP_SERVERS)

    tools = await client.get_tools()

    return tools