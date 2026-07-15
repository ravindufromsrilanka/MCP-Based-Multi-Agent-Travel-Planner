from client import get_tools


# ----------------------------------------
# Helper Function
# ----------------------------------------

async def find_tool(tool_name):

    tools = await get_tools()

    for tool in tools:

        if tool.name == tool_name:
            return tool

    return None


# ----------------------------------------
# HOTEL TOOLS
# ----------------------------------------

async def get_hotels():

    tool = await find_tool("get_hotels")

    return await tool.ainvoke({})


async def search_hotels(city):

    tool = await find_tool("search_hotels")

    return await tool.ainvoke({
        "city": city
    })


async def book_hotel(
    hotel_id,
    guest_name,
    check_in_date,
    check_out_date,
    rooms=1
):

    tool = await find_tool("book_hotel")

    return await tool.ainvoke({
        "hotel_id": hotel_id,
        "guest_name": guest_name,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "rooms": rooms
    })


# ----------------------------------------
# FLIGHT TOOLS
# ----------------------------------------

async def get_flights():

    tool = await find_tool("get_flights")

    return await tool.ainvoke({})


async def search_flights(destination):

    tool = await find_tool("search_flights")

    return await tool.ainvoke({
        "destination": destination
    })


async def book_flight(
    flight_id,
    passenger_name,
    date,
    seats=1
):

    tool = await find_tool("book_flight")

    return await tool.ainvoke({
        "flight_id": flight_id,
        "passenger_name": passenger_name,
        "date": date,
        "seats": seats
    })