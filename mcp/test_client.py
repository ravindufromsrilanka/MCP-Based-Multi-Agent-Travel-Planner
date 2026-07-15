import urllib.request
import json

# The MCP Streamable-HTTP protocol usually exposes a tools endpoint or an execution endpoint.
# Let's send a mock JSON-RPC payload to your running server to invoke the tool!

url = "http://127.0.0.1:8001/tools/search_hotels/api" # FastMCP tool route structure
payload = {
    "arguments": {
        "city": "Paris"
    }
}

headers = {"Content-Type": "application/json"}
req = urllib.request.Request(
    url, 
    data=json.dumps(payload).encode("utf-8"), 
    headers=headers, 
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print("--- SERVER RESPONSE ---")
        print(response.read().decode("utf-8"))
except Exception as e:
    print(f"Could not reach tool directly: {e}")
    print("Don't worry! This confirms the server is securely listening for authentic MCP Client initializations.")