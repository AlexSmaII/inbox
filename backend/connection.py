import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

class MissingConfiguration(Exception): pass

try:
    CW_MCP_URL = os.environ["CW_MCP_URL"]
    CW_MCP_TOKEN = os.environ["CW_MCP_TOKEN"]
except KeyError:
    raise MissingConfiguration(
        "CargoWise MCP credentials not found. "
        "Please ensure .env exists and that you have "
        "filled in values for CW_MCP_URL and CW_MCP_TOKEN."
    )

list_tools = {
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/list"
}

r = requests.post(
    CW_MCP_URL,
    headers = {
        "Authorization" : f"Bearer {CW_MCP_TOKEN}",
        "Accept" : "application/json, text/event-stream",
        "Content-Type": "application/json"
    },
    json = list_tools
)

print(r.status_code)
r.raise_for_status()
print(json.dumps(r.json(), indent=4))