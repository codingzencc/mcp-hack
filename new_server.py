# /Users/rshetty9/code/mcp-hack/mcp-hack/new_server.py
import os
import json
from datetime import datetime, timedelta
import anthropic
import subprocess
import sys
import shutil

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_server():
    print("Starting MCP Flight Search server...")
    
    # Find the mcp-flights-search executable
    mcp_flights_search = shutil.which("mcp-flight-search")
    if not mcp_flights_search:
        print("Error: mcp-flights-search command not found. Please make sure it's installed:")
        print("pip install mcp-flights-search")
        sys.exit(1)
    
    try:
        # Start the server process with the full path
        process = subprocess.Popen(
            [mcp_flights_search, "--connection_type", "stdio"],
            env={"SERP_API_KEY": os.getenv("SERP_API_KEY")},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Server started successfully!")
        print("Waiting for input...")
        
        # Keep the process running
        process.wait()
        
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
