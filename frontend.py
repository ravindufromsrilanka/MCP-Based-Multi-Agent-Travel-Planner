import json
import os
import asyncio,httpx
import gradio as gr

API_URL = os.environ.get("TRAVEL_PLANNER_API_URL", "http://127.0.0.1:8000/chat")

TRAVEL_THEME_CSS = """
body{
    background-color: #f0f8ff;
}

.gradio-container{
    max-width:900px;
    margin:40px auto;
    border-radius:12px
    box-shadow: 0 4px 20px rgba(0,0,0,0.05)
}

button.primary{
    background: linear-gradient(135deg, #0077b6, #0096c7);
    border:none;
    color:#ffff
}

button.primary:hover{
    background:linear-gradient(135deg,#0096c7,#03045e);
}
"""

def format_flights(flights):
    if not flights:
        return ""
    
    lines = ["Flights:"]
    for flight in flights:
        id = flight.get("_id", "Unknown ID")
        airline = flight.get("airline", "Unknown Airline")
        flight_number = flight.get("flightNumber", "Unknown Flight Number")
       
        origin = flight.get("origin", {}).get("airport", "Unknown Origin")
        origin_city = flight.get("origin",{}).get("city","unknown Origin")
        origin_country = flight.get("origin",{}).get("country","unknown Origin")
        
        destination = flight.get("destination", {}).get("airport", "Unknown Destination")
        destination_city = flight.get("destination", {}).get("city", "Unknown Destination")
        destination_country = flight.get("destination", {}).get("country", "Unknown Destination")
       
        flight_date = flight.get("flightDate", "Unknown Date")
       
        departure_time = flight.get("departureTime", "Unknown Departure Time")
        arrival_time = flight.get("arrivalTime", "Unknown Arrival Time")
       
        price = flight.get("price", "Unknown Price")
        currency = flight.get("currency", "Unknown Currency")
        
        available_seats = flight.get("availableSeats", "Unknown Available Seats")
        
        lines.append(
            f"✈️ **{airline} {flight_number}** (ID: `{id}`)\n"
            f"  📍 From: {origin_city}, {origin_country} ➡️ To: {destination_city}, {destination_country}\n"
            f"  📅 {flight_date} | 🕒 {departure_time} - {arrival_time}\n"
            f"  💰 {currency} {price} | 💺 {available_seats} seats left\n"
        )
    return "\n".join(lines)


def format_hotels(hotels):
    
    if not hotels:
        return ""
    
    lines = ["Hotels:"]
    for hotel in hotels:
        id = hotel.get("_id", "Unknown ID")
        name = hotel.get("name") or "Unknown Hotel"
        #expectation : making the answers more humanized
        city_data = hotel.get("city") or hotel.get("location", {})
        bed_count = hotel.get("availableRooms") or "Unknown Rooms Count"
        star_count = hotel.get("starRating") or "Unknown Rooms Count"
        if isinstance(city_data, dict):
            city = city_data.get("name") or city_data.get("city") or "Unknown City"
            country = city_data.get("country") or "Unknown Country"
            location_str = f"{city}, {country}"
        else:
            location_str = city_data
            currency = hotel.get("currency") or hotel.get("currency", "")
            price_per_night = hotel.get("pricePerNight") or "N/A"
       
        lines.append(
           f"🏨**{name}**\n"
           f"📍 {location_str}\n"
           f"💰 {currency}{price_per_night}/Night\n"
           f"🛏️ {bed_count}"
           f"⭐{star_count}"
           )
       
        # lines.append(f"{id}: {name} in {city} - {price_per_night}{currency} per night")
    return "\n".join(lines)


async def call_chat_api_streamed(message):
    """
    Sends the message to the FastAPI backend and yields visual status updates, 
    followed by typewriter-effect streaming of the response.
    """
    
    yield " Analyzing your request, routing to specialized agents...", None, None

    await asyncio.sleep(0.8)
    yield "Contacting database servers...", None, None
    
    payload = {"message": message}
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(API_URL, json=payload)
            response.raise_for_status();
            data = response.json()
    except httpx.ConnectError:
        yield "Connection Error:Could not connect to the servers.Please verify FastAPI Backend is working",None,None
        return
    except Exception as exc:
        yield "Service Error",None,None
        return
    
    chat_text = data.get("response", "No response returned from the agent network.")
    flights = data.get("flights")
    hotels = data.get("hotels")
    
    current_stream = ""
    
    words = chat_text.split(" ")
    for word in words:
        current_stream += word + " "
        yield current_stream +" | ",None,None
        await asyncio.sleep(0.09)

    yield chat_text,flights,hotels


async def respond(message, history):
    if history is None:
        history = []

    history.append({"role": "user", "content": message})
    yield history,""
    
    async for streamed_text,flights,hotels in call_chat_api_streamed(message):

        formatted_response = streamed_text
        
        if flights:
            formatted_response += format_flights(flights)
        if hotels:
            formatted_response += format_hotels(hotels)
        if len(history) > 0 and history[-1]["role"] == "assistant":
            history[-1]["content"] = formatted_response
        else:
            history.append({"role": "assistant", "content": formatted_response}) 
    
        yield history,""

def main():
    with gr.Blocks(title="Tripweaver Planner") as demo:
        gr.Markdown(
            "TripWeaver: MCP-Based Multi-Agent Travel Planner\n"
            "Ask our coordinated AI agents to search for flights, locate accommodations, or coordinate bookings."
        )
        chatbot = gr.Chatbot(label="Agent Collaboration Feed")
        message = gr.Textbox(label="How can we help", placeholder="Search flights from Colombo to Bangkok / Find a hotel in Colombo...")
        submit = gr.Button("Send")

        submit.click(respond, inputs=[message, chatbot], outputs=[chatbot, message])
        message.submit(respond, inputs=[message, chatbot], outputs=[chatbot, message])

    demo.launch(css=TRAVEL_THEME_CSS)


if __name__ == "__main__":
    main()
