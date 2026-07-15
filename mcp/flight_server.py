import json
import urllib.request
from mcp.server.fastmcp import FastMCP
from typing import Optional as optional

mcp = FastMCP("Flight Service",port = 8002)

BASE_URL="https://standing-fish-574.convex.site"

def _get_json(url:str):
    with urllib.request.urlopen(url) as response:
        raw_data = response.read()
        text_data = raw_data.decode("utf-8")
        return json.loads(text_data)
    
def _post_json(url:str,payload : dict):
    json_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data = json_bytes,
        headers = {"Content-Type" :"application/json"},
        method = "POST"
    )

    with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
        
@mcp.tool()
def get_flights()->list:
    """
    Retrieve all flights globally.
    """
    url = f"{BASE_URL}/flights"
    return _get_json(url)

@mcp.tool()
def search_flights(
    date: optional[str]=None,
    destination:optional[str]=None,
    country:optional[str]=None,
    time:optional[str]=None,
    seats:int = 1
    )->list:
    """
    Search for available flights by destination city.
    destination is required. date is optional.
    """
    params = {"destination": destination}
    if date:
        params["date"] = date

    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/flights/search?{query_string}"

    return _get_json(url)
    
@mcp.tool()
def book_flight(
    flight_id:int,
    passenger_name:str,
    date:str,
    seats:int =1
    )->dict:
    """Book a flight using the flight ID, passenger name, and travel date."""
    payload={
        "flight_id": flight_id,
        "passenger_name": passenger_name,
        "date": date,
        "seats": seats
    }
    
    return _post_json(BASE_URL+"/book_flight",payload)
    
mcp.run(
    transport = "streamable-http"
)