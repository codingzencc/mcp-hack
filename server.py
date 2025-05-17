# pip install anthropic mcp
import asyncio
import os
import json
from datetime import datetime, timedelta
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Get the absolute path to the server script
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "Google-Flights-MCP-Server", "server.py")

# Server parameters
server_params = StdioServerParameters(
    command="python",
    args=[SERVER_SCRIPT],
    env={"SERP_API_KEY": os.getenv("SERP_API_KEY")},
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Use a date 30 days in the future
            future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            prompt = f"Find Flights from Atlanta to Las Vegas {future_date}"
            await session.initialize()

            mcp_tools = await session.list_tools()
            
            # Convert MCP tools to Claude's tool format with exact schema match
            tools = []
            for tool in mcp_tools.tools:
                tool_schema = {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "type": "object",
                        "title": "get_flights_on_date_toolArguments",
                        "properties": {
                            "origin": {
                                "title": "Origin",
                                "type": "string"
                            },
                            "destination": {
                                "title": "Destination",
                                "type": "string"
                            },
                            "date": {
                                "title": "Date",
                                "type": "string"
                            },
                            "adults": {
                                "title": "Adults",
                                "type": "integer",
                                "default": 1
                            },
                            "seat_type": {
                                "title": "Seat Type",
                                "type": "string",
                                "default": None
                            },
                            "return_cheapest_only": {
                                "title": "Return Cheapest Only",
                                "type": "boolean",
                                "default": False
                            }
                        },
                        "required": ["origin", "destination", "date"]
                    }
                }
                tools.append(tool_schema)

            # Create the message with tools
            message = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                system=f"""You are a flight search assistant. Your only job is to use the get_flights_on_date tool to search for flights. Do not think about it. Do not explain. Just make the tool call.

For the current request, you must call get_flights_on_date with these exact parameters:
{{
    "origin": "ATL",
    "destination": "LAS",
    "date": "{future_date}",
    "adults": 1,
    "return_cheapest_only": false
}}

Do not think. Do not explain. Just make the tool call.""",
                messages=[
                    {
                        "role": "user",
                        "content": f"Search for flights from Atlanta to Las Vegas on {future_date}"
                    }
                ],
                tools=tools,
                tool_choice={"type": "tool", "name": "get_flights_on_date"}
            )

            # Check if there's a tool call in the response
            if message.content and message.content[0].type == "tool_use":
                tool_call = message.content[0]
                
                # Call the MCP tool with the extracted parameters
                result = await session.call_tool(
                    tool_call.name, 
                    arguments=tool_call.input
                )

                # Parse and print formatted JSON result
                print("--- Formatted Result ---")
                try:
                    flight_data = json.loads(result.content[0].text)
                    print(json.dumps(flight_data, indent=2))
                except json.JSONDecodeError:
                    print("MCP server returned non-JSON response:")
                    print(result.content[0].text)
                except (IndexError, AttributeError):
                    print("Unexpected result structure from MCP server:")
                    print(result)
            else:
                print("No tool call was made in the response")

# Run the async function
if __name__ == "__main__":
    print(f"Starting MCP Flight Search server...")
    asyncio.run(run())
