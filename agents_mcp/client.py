from langchain_mcp_adapters.client import MultiServerMCPClient

# ---------------------------------------------------
# MCP Server Configuration
# ---------------------------------------------------

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

# ---------------------------------------------------
# These variables are stored in memory.
# They help us avoid reconnecting every request.
# ---------------------------------------------------

client = None
tools = None


# ---------------------------------------------------
# Return all MCP tools
# ---------------------------------------------------

async def get_tools():

    global client
    global tools

    # Already connected
    if tools is not None:
        return tools

    # Connect only once
    client = MultiServerMCPClient(MCP_SERVERS)

    tools = await client.get_tools()

    return tools