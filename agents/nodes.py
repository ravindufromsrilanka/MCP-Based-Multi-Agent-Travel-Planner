from typing import Optional, Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .tools import get_hotels, search_hotel, book_hotel, get_flights, search_flights, book_flight
from .llm import llm
from .prompts import get_system_prompt_for_unknown_node, get_system_prompt_with_history
from .entity import GraphState


class TravelExtraction(BaseModel):
    intent: Literal["hotel", "flight", "unknown"] = Field(
        default="unknown",
        description="Main user intent: hotel, flight, or unknown."
    )

    sub_action: Literal["search", "list_all","book", "confirm" ,"general"] = Field(
        default="general",
        description="Action type: search, list_all, book ,confirm(Yes/No) or general."
    )

    location: Optional[str] = Field(
        default=None,
        description="The location targeted for the hotel search.Extract the location name from the user query.Can be a city name, country name, state, or region. Examples: Mumbai, Thailand, Japan, Bangkok."
    )

    check_in: Optional[str] = Field(
        default=None,
        description="Hotel check-in date in YYYY-MM-DD format. Null if not provided."
    )

    check_out: Optional[str] = Field(
        default=None,
        description="Hotel check-out date in YYYY-MM-DD format. Null if not provided."
    )

    origin: Optional[str] = Field(
        default=None,
        description="Flight origin city or airport code. Extract the destination name from the user query .Example: DEL, BKK, Delhi,Thailand,India,Canada."
    )

    destination: Optional[str] = Field(
        default=None,
        description="Flight destination city,Country or airport code.Extract the destination name from the user query .Example: DEL, BKK, Delhi,Thailand,India,Canada."
    )

    flight_date: Optional[str] = Field(
        default=None,
        description="Flight date in YYYY-MM-DD format.Retain from history context if already provided. Null if not provided."
    )

    hotel_id: Optional[str] = Field(
        default=None,
        description="ID of the hotel to book.Retain from history context if already provided. Null if not provided."
    )

    guest_name: Optional[str] = Field(
        default=None,
        description="Guest full name for hotel booking.Retain from history context if already provided. Null if not provided."
    )

    guest_email: Optional[str] = Field(
        default=None,
        description="Guest email for hotel booking.Retain from history context if already provided. Null if not provided."
    )

    room_type: Optional[str] = Field(
        default=None,
        description="Hotel room type such as single, double, or suite.Retain from history context if already provided. Null if not provided."
    )

    flight_id: Optional[str] = Field(
        default=None,
        description=(
            "The unique database alphanumeric string ID of the flight to book (e.g., 'k9750cd...'). "
            "Do NOT use the flight number (like CA7613 or AI7790). Look for the ID value inside the parentheses "
            "matching the user's requested flight selection. Retain from context history if already provided."
        )
    )

    passenger_name: Optional[str] = Field(
        default=None,
        description="Passenger full name for flight booking.Retain from history context if already provided. Null if not provided."
    )

    passenger_email: Optional[str] = Field(
        default=None,
        description="Passenger email for flight booking.Retain from history context if already provided. Null if not provided."
    )
    
    seat_count:Optional[int] = Field(
        default=None,
        description = "The total number of seats to book for the flight. Extract as an integer digit (e.g., 2). "
            "Look closely for explicit numbers, words like 'two seats', or a standalone trailing number "
            "provided in a comma-separated list of details. Always retain from history context if already captured."
        )


travel_extractor = llm.with_structured_output(TravelExtraction)


def router(state: GraphState) -> dict:
    user_message = state["messages"][-1]
    history_messages = state["messages"][:-1]
    
    system_prompt = get_system_prompt_with_history("\n".join(history_messages))

    invocation_messages = [SystemMessage(content=system_prompt)]
    for i in range(0, len(history_messages), 2):
        invocation_messages.append(HumanMessage(content=history_messages[i]))
        if i + 1 < len(history_messages):
            invocation_messages.append(AIMessage(content=history_messages[i + 1]))
    invocation_messages.append(HumanMessage(content=user_message))

    try:
        extracted = travel_extractor.invoke(invocation_messages)

        data = extracted.dict()

        print(f"AI extraction :{data} ---")

    except Exception:
        data = {
            "intent": "unknown",
            "sub_action": "general",
            "location": None,
            "check_in": None,
            "check_out": None,
            "origin": None,
            "destination": None,
            "flight_date": None,
            "hotel_id": None,
            "guest_name": None,
            "guest_email": None,
            "room_type": None,
            "flight_id": None,
            "passenger_name": None,
            "passenger_email": None,
            "seat_count" : None
        }

    return {
        "intent": data.get("intent", "unknown"),
        "sub_action": data.get("sub_action", "general"),

        "location": data.get("location"),
        "check_in": data.get("check_in"),
        "check_out": data.get("check_out"),

        "origin": data.get("origin"),
        "destination": data.get("destination"),
        "flight_date": data.get("flight_date"),

        "hotel_id": data.get("hotel_id"),
        "guest_name": data.get("guest_name"),
        "guest_email": data.get("guest_email"),
        "room_type": data.get("room_type"),

        "flight_id": data.get("flight_id"),
        "passenger_name": data.get("passenger_name"),
        "passenger_email": data.get("passenger_email"),
        "seat_count": data.get("seat_count"),

        "hotel_results": [],
        "flight_results": [],
        "response_text": "",
    }



def _format_hotel(hotel: dict) -> str:
    name = hotel.get("name", "Unknown hotel")

    city_data = hotel.get("city", "unknown city")
    if isinstance(city_data, dict):
        city = city_data.get("name", "unknown city")
        country = city_data.get("country", "")
        location_str = f"{city}, {country}" if country else city
    else:
        location_str = city_data

    stars = hotel.get("stars", hotel.get("rating", "N/A"))
    price = hotel.get("price", hotel.get("pricePerNight", "N/A"))
    currency = hotel.get("currency", "USD")

    available = hotel.get(
        "available_rooms",
        hotel.get("availableRooms", hotel.get("available", "N/A"))
    )

    return (
        f"🏨 **{name}** \n"
        f"📍 {location_str}\n "
        f"⭐{stars} stars \n"
        f"💰{currency} {price}/night - "
        f"🛏️{available} rooms \n"
        f"\n"
    )


def _format_flight(flight: dict) -> str:
    airline = flight.get("airline", "Unknown airline")

    number = flight.get(
        "flightNumber",
        flight.get("flight_number", flight.get("flightNo", "N/A"))
    )

    origin_data = flight.get("origin", "unknown")
    destination_data = flight.get("destination", "unknown")

    if isinstance(origin_data, dict):
        origin = origin_data.get("airport", origin_data.get("city", "unknown"))
        origin_city = origin_data.get("city", origin_data.get("city", "unknown"))
        origin_country = origin_data.get("country", origin_data.get("country", "unknown"))
        origin_str = f"{origin_city} , {origin_country}"
    else:
        origin_str = origin_data

    if isinstance(destination_data, dict):
        destination = destination_data.get("airport", destination_data.get("city", "unknown"))
        destination_city = destination_data.get("city", destination_data.get("city", "unknown"))
        destination_country = destination_data.get("country", destination_data.get("country", "unknown"))
        destination_str = f"{destination_city} , {destination_country}"
    else:
        destination_str = destination_data

    flight_date = flight.get(
        "flightDate",
        flight.get("date", flight.get("departure_date", "unknown"))
    )

    departure_time = flight.get(
        "departureTime",
        flight.get("departure_time", "N/A")
    )

    arrival_time = flight.get(
        "arrivalTime",
        flight.get("arrival_time", "N/A")
    )

    price = flight.get("price", "N/A")
    currency = flight.get("currency", "USD")

    seats = flight.get(
        "availableSeats",
        flight.get("available_seats", flight.get("seats", "N/A"))
    )
    return(
        f"✈️ **{airline} {number}**\n"
    f"  📍 From: {origin_str} ➡️ To: {destination_str}\n"
    f"  📅 {flight_date} | 🕒 {departure_time} - {arrival_time}\n"
    f"  💰 {currency} {price} | 💺 {seats} seats left\n"
    )



def hotel_node(state: GraphState) -> dict:
    try:
        location = state.get("location")
        check_in = state.get("check_in")
        check_out = state.get("check_out")

        if state.get("sub_action") == "book":
            hotel_id = state.get("hotel_id")
            guest_name = state.get("guest_name")
            guest_email = state.get("guest_email")
            room_type = state.get("room_type")
            check_in_date = state.get("check_in")
            check_out_date = state.get("check_out")

            if state.get("sub_action") == "confirm":
                result = book_hotel.invoke(
                    {
                    "hotel_id": hotel_id,
                    "guest_name": guest_name,
                    "guest_email": guest_email,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "room_type": room_type,
                }
                )
                
                confirmation_msg = "Hotel booking successfully completed!"
                
            if isinstance(result, dict):
                confirmation_msg = result.get("message") or result.get("status") or confirmation_msg

            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": (
                    f"🎉 **{confirmation_msg}**\n"
                    f"🏨 **Confirmed Booking Details:**\n"
                    f"  • Hotel ID: `{hotel_id}`\n"
                    f"  • Guest Name: {guest_name}\n"
                    f"  • Email: {guest_email}\n"
                    f"  • Room Type: {room_type}\n"
                    f"  • Stay Duration: {check_in_date} to {check_out_date}\n\n"
                    f"Have a wonderful and comfortable stay!"
                ),
            }

        elif state.get("sub_action") == "book":
            missing = [
                field
                for field, value in [
                    ("hotel_id", hotel_id),
                    ("guest_name", guest_name),
                    ("guest_email", guest_email),
                    ("room_type", room_type),
                    ("check_in", check_in_date),
                    ("check_out", check_out_date),
                ]
                if not value
            ]

            if missing:
                readable_missing = ", ".join([m.replace("_", " ") for m in missing])
                return {
                    "hotel_results": [],
                    "flight_results": [],
                    "response_text": f"I need more details to prepare your booking. Please provide: **{readable_missing}**.",
                }

            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": (
                    f"📋 **Please verify your hotel booking summary:**\n\n"
                    f"🏨 **Hotel ID:** `{hotel_id}`\n"
                    f"👤 **Guest Name:** {guest_name}\n"
                    f"📧 **Guest Email:** {guest_email}\n"
                    f"🛏️ **Room Type:** {room_type}\n"
                    f"📅 **Check-in:** {check_in_date}\n"
                    f"📅 **Check-out:** {check_out_date}\n\n"
                    f"Is all the data correct? Please reply **Yes** to confirm booking, or specify what needs to be changed."
                ),
            }

        elif location:
            params = {
                "location": location,
            }

            if check_in:
                params["checkIn"] = check_in

            if check_out:
                params["checkOut"] = check_out

            result = search_hotel.invoke(params)

        else:
            result = get_hotels.invoke({})


        if isinstance(result, dict):
            hotel_results = result.get("hotels", [])
        elif isinstance(result, list):
            hotel_results = result
        else:
            hotel_results = []

        if not hotel_results:
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": (
                    "I couldn't find any hotels. "
                    "Try searching by city, for example: 'available hotels in Mumbai'."
                ),
            }

        return {
            "hotel_results": hotel_results,
            "flight_results": [],
            "response_text": "",
        }
    except Exception as e:
         return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": f"I couldn't understand your request clearly. Error: {str(e)}",
        }


def flight_node(state: GraphState) -> dict:
    origin = state.get("origin")
    destination = state.get("destination")
    flight_date = state.get("flight_date")

    flight_id = state.get("flight_id")
    passenger_name = state.get("passenger_name")
    passenger_email = state.get("passenger_email")
    seat_count = state.get("seat_count")
    sub_action = state.get("sub_action", "general")

    if state.get("sub_action") == "confirm":
        result = book_flight.invoke(
            {
                "flight_id": flight_id,
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
                "seat_count": seat_count
            }
        )
        
        confirmation_msg = "Flight booking successfully completed!"
        if isinstance(result, dict):
            confirmation_msg = result.get("message") or result.get("status") or confirmation_msg

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": (
                f"🎉 **{confirmation_msg}**\n\n"
                f"🎟️ **Confirmed Booking Details:**\n"
                f"  • Flight ID: `{flight_id}`\n"
                f"  • Passenger: {passenger_name}\n"
                f"  • Email: {passenger_email}\n"
                f"  • Seats Secured: {seat_count}\n\n"
                f"Have a safe and wonderful flight!"
            ),
        }
        
    elif state.get("sub_action") == "book":
        missing = [
            field for field, value in [
                ("flight_id", flight_id),
                ("passenger_name", passenger_name),
                ("passenger_email", passenger_email),
                ("seat_count", seat_count), # Validates seat count presence
            ] if not value
        ]

        if missing:
            readable_missing = ", ".join([m.replace("_", " ") for m in missing])
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": f"I need more details to prepare your booking. Please provide: **{readable_missing}**.",
            }

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": (
                f"📋 **Please verify your flight booking summary:**\n\n"
                f"✈️ **Flight ID:** `{flight_id}`\n"
                f"👤 **Passenger Name:** {passenger_name}\n"
                f"📧 **Passenger Email:** {passenger_email}\n"
                f"💺 **Number of Seats:** {seat_count}\n\n"
                f"Is all the data correct? Please reply **Yes** to confirm booking, or specify what needs to be changed."
            ),
        }
    
    #booking
    if state.get("sub_action") == "book":
        flight_id = state.get("flight_id")
        passenger_name = state.get("passenger_name")
        passenger_email = state.get("passenger_email")

        missing = [
            field
            for field, value in [
                ("flight_id", flight_id),
                ("passenger_name", passenger_name),
                ("passenger_email", passenger_email),
            ]
            if not value
        ]

        if missing:
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": (
                    "I need more details to book the flight. "
                    "Please provide flight_id, passenger_name, and passenger_email."
                ),
            }

        result = book_flight.invoke(
            {
                "flight_id": flight_id,
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
            }
        )

    elif origin and destination:
        params = {
            "origin": origin,
            "destination": destination,
        }

        if flight_date:
            params["date"] = flight_date

        result = search_flights.invoke(params)

    # elif origin or destination:
    #     return {
    #         "hotel_results": [],
    #         "flight_results": [],
    #         "response_text": (
    #             "I need both departure and destination information. "
    #             "For example: 'flight from BOM to DEL'."
    #         ),
    #     }

    else:
        result = get_flights.invoke({})

    if state.get("sub_action") == "book":
        if isinstance(result, dict):
            confirmation = result.get("message") or result.get("status") or "Flight booking completed."
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": confirmation,
            }

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": "Flight booking completed.",
        }
    
    if isinstance(result, (dict, list)):
        all_data = result
    else:
        all_data = []

    if isinstance(all_data,dict):
        all_flights = all_data.get("flights",[])
    elif isinstance (all_data,list):
        all_flights = all_data
    else:
        all_flights = []

    flight_results = []
    
    #data filtering
    if origin or destination:
        for flight in all_flights:
            match = True;
            
            #Match with destination
            if destination:
                dest_lower = destination.lower().strip()
                desti_info = flight.get("destination",{})
                if isinstance(desti_info, dict):
                    if (dest_lower != desti_info.get("city", "").lower().strip() and
                        dest_lower != desti_info.get("country", "").lower().strip() and
                        dest_lower != desti_info.get("airport", "").lower().strip()):
                        match = False
                else:
                    if dest_lower != str(desti_info).lower().strip():
                        match = False
            
            #Match with origin       
            if origin:
                origin_lower = origin.lower().strip()
                origin_info = flight.get("origin",{})
                if isinstance(origin_info, dict):
                    if(origin_lower != origin_info.get("city","").lower().strip() and
                       origin_lower != origin_info.get("country","").lower().strip() and
                       origin_lower != origin_info.get("airport","").lower().strip()):
                        match = False;
                else:
                    if origin_lower != str(origin_info).lower().strip():
                        match = False
            
            if match:
                flight_results.append(flight)
    else:
        flight_results = all_flights
    
    # if isinstance(result, dict):
    #     flight_results = result.get("flights", [])
    # elif isinstance(result, list):
    #     flight_results = result
    # else:
    #     flight_results = []

    if not flight_results:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": (
                "I couldn't find flights matching your request. "
                "Try another route or ask for all flights."
            ),
        }

    return {
        "hotel_results": [],
        "flight_results": flight_results,
        "response_text": "",
    }


def unknown_node(state: GraphState) -> dict:
    user_message = state["messages"][-1]
    history_messages = state["messages"][:-1]

    system_prompt = get_system_prompt_for_unknown_node("\n".join(history_messages))

    invocation_messages = [SystemMessage(content=system_prompt)]
    for i in range(0, len(history_messages), 2):
        invocation_messages.append(HumanMessage(content=history_messages[i]))
        if i + 1 < len(history_messages):
            invocation_messages.append(AIMessage(content=history_messages[i + 1]))
    invocation_messages.append(HumanMessage(content=user_message))

    try:
        response = llm.invoke(invocation_messages)

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": response.content,
        }

    except Exception as e:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": f"I couldn't understand your request clearly. Error: {str(e)}",
        }



def generate_response(state: GraphState) -> dict:
    if state.get("response_text"):
        return {
            "response_text": state["response_text"]
        }

    hotel_results = state.get("hotel_results", [])
    flight_results = state.get("flight_results", [])

    if hotel_results:
        count = len(hotel_results)
        # lines = [_format_hotel(hotel) for hotel in hotel_results[:5]]
        lines = [_format_hotel(hotel) for hotel in hotel_results]

        return {
            "response_text": (
                f"I found {count} hotel option{'s' if count != 1 else ''}:\n"
                + "\n".join(lines)
            )
        }

    if flight_results:
        count = len(flight_results)
        # lines = [_format_flight(flight) for flight in flight_results[:5]]
        lines = [_format_flight(flight) for flight in flight_results]

        return {
            "response_text": (
                f"I found {count} flight option{'s' if count != 1 else ''}:\n"
                + "\n".join(lines)
            )
        }

    return {
        "response_text": "I couldn't find matching travel options."
    }


def route_after_extraction(state: GraphState) -> str:
    intent = state.get("intent", "unknown")

    if intent == "hotel":
        return "hotel"

    if intent == "flight":
        return "flight"

    return "unknown"