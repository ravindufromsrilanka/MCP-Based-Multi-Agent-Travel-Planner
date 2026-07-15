from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVERS = {
    "hotel-service": {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable_http",
    },
    "flight-service": {
        "url": "http://localhost:8002/mcp",
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