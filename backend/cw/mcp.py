import json
import os
from pathlib import Path
from typing import Any

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

list_tables = {
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
        "name": "cw.schema.tables",
        "arguments" : {
            "name_like" : "CONSOL",
            "instance" : "prod"
        }
    }
}

r = requests.post(
    CW_MCP_URL,
    headers = {
        "Authorization" : f"Bearer {CW_MCP_TOKEN}",
        "Accept" : "application/json"
    },
    json = list_tables
)

r.raise_for_status()

# Catch errors on the MCP side
if "error" in r.json():
    error = r.json().get("error")
    print(error)
    code = error.get("code", "")
    message = error.get("message", "")
    raise requests.HTTPError(f"Error {code}: {message}")

if "result" in r.json():
    response : dict[str, Any] = r.json().get("result", {})
    raw_content : list[dict[str, Any]] = response.get("content", [])

    content : list[str] = []
    
    for entry in raw_content:
        type = entry.get("type")
        if type == "text":
            data = entry.get("text")
            if data:
                content.append(data)

    # Catch errors on the CW1 side
    if response.get("isError"):
        error_message = content[0] if content else "Unknown error"

        raise requests.HTTPError(f"Error: {error_message}")

SCHEMA_PATH = Path(__file__).parent / "data" / "mcp.json"
SCHEMA_PATH.parent.mkdir(exist_ok=True, parents=True)

with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
    json.dump(content, f, indent=4)
