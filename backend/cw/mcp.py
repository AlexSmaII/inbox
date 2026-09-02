import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed


class CargoWiseMCP:
    """
    Connection to the CargoWise MCP.

    Args:
        url (str):   The public MCP URL.
        token (str): Bearer token to authorise access to the MCP.
    """
    class MCPError(Exception): pass
    class CW1Error(Exception): pass
    
    def __init__(
        self,
        url : str,
        token : str
    ):
        """
        Connect to the CargoWise MCP.

        Args:
            url (str):   The public MCP URL.
            token (str): Bearer token to authorise access to the MCP.
        """        
        self.url = url
        self.token = token
    

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(60))
    def mcp_query(
        self,
        jsonrpc_payload : dict[str, Any]
    ) -> dict[str, Any]:
        """
        Query the MCP server, retrying a total of 3 times
        if the connection fails with a wait time of one
        minute in between retries.

        Args:
            jsonrpc_payload (dict[str, Any]):
                Raw JSON-RPC 2.0 payload.

        Raises:
            HTTPError: MCP returned a non-200 response.
            MCPError:  MCP response did not contain a 'result' field.
            CW1Error:  CargoWise One database failure.

        Returns:
            dict[str, Any]: The raw response 'result' JSON.
        """
        
        r = requests.post(
            self.url,
            headers = {
                "Authorization" : f"Bearer {self.token}",
                "Accept" : "application/json"
            },
            json = jsonrpc_payload
        )

        r.raise_for_status()

        # Catch errors on the MCP side
        if "error" in r.json():
            error = r.json().get("error")
            code = error.get("code", "")
            message = error.get("message", "")
            raise self.MCPError(f"Error {code}: {message}")
        if not "result" in r.json():
            raise self.MCPError("MCP returned no 'result' field in response")

        response : dict[str, Any] = r.json().get("result", {})

        # Catch errors on the CW1 side
        if response.get("isError"):
            error_message = "Unknown error"
            try:
                error_message = response["content"][0]["text"]
            except Exception: pass

            raise self.CW1Error(error_message)
        
        return response

    def tools_list(
        self
    ) -> dict[str, Any]:
        """
        List all tools available from the MCP.

        Returns:
            dict[str, Any]: Raw JSON response.
        """
        return self.mcp_query({
            "jsonrpc" : "2.0",
            "id" : 1,
            "method" : "tools/list"
        })


    def tool_call(
        self,
        tool_name : str,
        params : dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call a specific tool from the
        MCP server and return its response
        as a JSON object.

        Args:
            tool_name (str):         Tool name (e.g., 'cw.schema.tables')
            params (dict[str, Any]): Tool function parameters.

        Raises:
            self.MCPError: MCP returned an empty response.

        Returns:
            dict[str, Any]: MCP JSON response.
        """

        payload = {
            "jsonrpc" : "2.0",
            "id" : 1,
            "method" : "tools/call",
            "params" : {
                "name" : tool_name,
                "arguments" : params
            }
        }

        response = self.mcp_query(payload)

        # Extract all 'content' 'text' fields from response
        raw_content : list[dict[str, Any]] = response.get("content", [])
        content : list[str] = []
        for entry in raw_content:
            type = entry.get("type")
            if type == "text":
                data = entry.get("text")
                if data:
                    content.append(data)
        
        # Attempt to extract JSON from the content text fields
        content_json : dict = {}
        for string in content:
            data = {}
            try:
                data = json.loads(string)
            except json.JSONDecodeError:
                pass
            if data:
                content_json = data
                break
        
        if not content_json:
            raise self.MCPError(
                "MCP returned no response for request:\n"
                f"{json.dumps(payload, indent=4)}"
            )

        return content_json
        

if __name__ == "__main__":

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
    
    conn = CargoWiseMCP(url=CW_MCP_URL, token=CW_MCP_TOKEN)

    print(
        json.dumps(conn.tool_call(
            "cw.schema.tables",
            {
                "name_like" : "CONSOL",
                "instance" : "prod"
            }
        ), indent=4)
    )
