from flask import Flask, request, jsonify
import httpx
import asyncio
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# MCP service endpoints
MAPS_MCP_URL = "https://your-maps-mcp-server.com/api/maps"
FLIGHT_API_URL = "https://your-flights-api.com/api/flights"
HOTEL_API_URL = "https://your-hotels-api.com/api/hotels"
UBER_API_URL = "https://your-transport-api.com/api/uber"

# Async data fetcher
async def fetch_data(client, url, payload, service_name):
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

@app.route('/plan-trip', methods=['POST'])
def plan_trip():
    data = request.get_json()
    required_keys = ['origin', 'destination', 'start_date', 'end_date', 'num_people']
    if not all(k in data for k in required_keys):
        return jsonify({'error': 'Missing required fields'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def fetch_all():
        async with httpx.AsyncClient() as client:
            maps_task = fetch_data(client, MAPS_MCP_URL, data, "Maps")
            flight_task = fetch_data(client, FLIGHT_API_URL, data, "Flights")
            hotel_task = fetch_data(client, HOTEL_API_URL, data, "Hotels")
            uber_task = fetch_data(client, UBER_API_URL, data, "Transport")
            return await asyncio.gather(maps_task, flight_task, hotel_task, uber_task)

    maps, flights, hotels, transport = loop.run_until_complete(fetch_all())
    itinerary = {
        "maps": maps,
        "flights": flights,
        "hotels": hotels,
        "transport": transport
    }

    if any("error" in result for result in [maps, flights, hotels, transport]):
        return jsonify({"status": "error", "itinerary": itinerary}), 502

    return jsonify({"status": "success", "itinerary": itinerary})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
