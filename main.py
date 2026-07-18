import os
import asyncio
from fastapi import FastAPI
import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mangum import Mangum

from fastapi.middleware.cors import CORSMiddleware
from entity import ChatRequest, ChatResponse
from agents.tools import get_hotels, get_flights
from agents.graph import graph
from contextlib import asynccontextmanager


conversation_history_messages = []

@asynccontextmanager
async def lifespan(app : FastAPI):
    print("Application starting")
    yield
    print("Application stopping")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


 #app.get(/) removed caused gradio frontend need to be load as homepage   
# @app.get("/")
# async def hello():
#     return {"message": "Hello, World!"}


@app.get("/hotels")
async def list_hotels():
    try:
        return await get_hotels.ainvoke({})
    except Exception as e:
        return {"error": str(e)}


@app.get("/flights")
async def list_flights():
    try:
        return await get_flights.ainvoke({})
    except Exception as e:
        return {"error": str(e)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    recent_pairs = conversation_history_messages[-3:]
    flattened_messages = []
    for user_msg, assistant_msg in recent_pairs:
        flattened_messages.append(user_msg)
        flattened_messages.append(assistant_msg)
    flattened_messages.append(request.message)

    initial_state = {
        "messages": flattened_messages,
        "intent": "",
        "sub_action": "",
        "city": None,
        "country":None,
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
        "hotel_results": [],
        "flight_results": [],
        "response_text": "",
    }

    try:
         result = await graph.ainvoke(initial_state)
         response_text = result.get("response_text", "Something went wrong. Please try again.")

    except Exception as e:
        response_text = f"Error: {str(e)}"
        result = {}
        conversation_history_messages.append((request.message, response_text))
        return ChatResponse(
            response=response_text,
            hotels=result.get("hotel_results", []) or None,
         
            flights=result.get("flight_results", []) or None,
        )

    conversation_history_messages.append((request.message, response_text))

    return ChatResponse(
        response=response_text,
        hotels=result.get("hotel_results", []) or None,
        flights=result.get("flight_results", []) or None,
    )

async def gradio_chat_handler(message,history):
    """
    This helper function connects front-end text box directly 
    to existing FastAPI /chat endpoint logic safely.
    """
    request_payload = ChatRequest(message=message)
    chat_response = await chat(request_payload)

    return chat_response.response

demo = gr.ChatInterface(
    fn = gradio_chat_handler,
    title= "TripWeaver AI Travel Planner",
    description="Ask me to search for flights, list hotels, or make bookings seamlessly!",
)

app = gr.mount_gradio_app(app, demo, path="/")
handler = Mangum(app)
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
