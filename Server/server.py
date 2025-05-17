from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Define request schema
class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str  # ISO format (YYYY-MM-DD)
    end_date: str    # ISO format (YYYY-MM-DD)
    num_people: int

# External API endpoints (replace with actual endpoints or use API gateways)
MAPS_MCP_URL = "https://your-maps-mcp-server.com/api/maps"
FLIGHT_API_URL = "https://your-flights-api.com/api/flights"
HOTEL_API_URL = "https://your-hotels-api.com/api/hotels"
UBER_API_URL = "https://your-transport-api.com/api/uber"

async def fetch_data(client: httpx.AsyncClient, url: str, payload: dict, service_name: str):
    try:
        response = await client.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as http_err:
        logging.error(f"HTTP error in {service_name}: {http_err}")
        return {"error": f"HTTP error from {service_name}: {str(http_err)}"}
    except Exception as e:
        logging.error(f"Unhandled error in {service_name}: {e}")
        return {"error": f"Unhandled error from {service_name}: {str(e)}"}

@app.post("/plan-trip")
async def plan_trip(trip: TripRequest):
    payload = trip.dict()
    async with httpx.AsyncClient() as client:
        maps_task = fetch_data(client, MAPS_MCP_URL, payload, "Maps")
        flight_task = fetch_data(client, FLIGHT_API_URL, payload, "Flights")
        hotel_task = fetch_data(client, HOTEL_API_URL, payload, "Hotels")
        uber_task = fetch_data(client, UBER_API_URL, payload, "Transport")

        maps, flights, hotels, transport = await asyncio.gather(
            maps_task, flight_task, hotel_task, uber_task
        )

    itinerary = {
        "maps": maps,
        "flights": flights,
        "hotels": hotels,
        "transport": transport
    }

    # Validate and clean errors from results
    if any("error" in result for result in [maps, flights, hotels, transport]):
        raise HTTPException(status_code=502, detail=itinerary)

    return {"status": "success", "itinerary": itinerary}
