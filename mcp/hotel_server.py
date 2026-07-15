import json
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP
from typing import Optional as optional

mcp = FastMCP("Hotel Service", port=8001)

BASE_URL = "https://standing-fish-574.convex.site"


def _get_json(url: str):
    with urllib.request.urlopen(url) as response:
        raw_data = response.read()
        text_data = raw_data.decode("utf-8")
        return json.loads(text_data)


def _post_json(url: str, payload: dict):
    json_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=json_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def _only_name_address(data):
    """Convert full hotel response into only name and address structures."""
    if isinstance(data, dict) and "hotels" in data:
        hotels = data["hotels"]
    elif isinstance(data, list):
        hotels = data
    else:
        return data

    return [
        {
            "name": hotel.get("name"),
            "address": hotel.get("address")
        }
        for hotel in hotels
    ]


@mcp.tool()
def get_hotels() -> str:
    """
    Retrieve all hotels with only name and address.
    """
    url = f"{BASE_URL}/hotels"
    print(url)
    
    data = _get_json(url)
    cleaned_data = _only_name_address(data)
    return json.dumps(cleaned_data)


@mcp.tool()
def search_hotels(
    city: optional[str] = None,
    country: optional[str] = None,
    check_in: optional[str] = None,
    check_out: optional[str] = None,
    min_price: optional[float] = None,
    max_price: optional[float] = None
) -> str:
    """
    Search hotels by city.
    Returns only name and address.
    check_in and check_out are optional.
    """
    params = {"city": city}

    if check_in:
        params["checkIn"] = check_in
    if check_out:
        params["checkOut"] = check_out

    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/hotels/search?{query_string}"
    print(url)

    data = _get_json(url)
    return json.dumps(data)


@mcp.tool()
def book_hotel(
    hotel_id: int,
    guest_name: str,
    check_in_date: str,
    check_out_date: str,
    rooms: int = 1
) -> dict:
    """Book a hotel room using the hotel ID, guest name, and travel dates."""
    payload = {
        "hotel_id": hotel_id,
        "guest_name": guest_name,
        "rooms": rooms,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date
    }
    return _post_json(f"{BASE_URL}/book_hotel", payload)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")