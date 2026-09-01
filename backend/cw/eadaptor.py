import base64
from datetime import timedelta
from pathlib import Path

import requests
from parser import parse_cw_response
from requests import Response
from schemas import UniversalResponse


class CargoWiseConnection:
    """
    Connection to CargoWise One eAdaptor HTTP+XML
    interface.
    """
    
    def __init__(
        self,
        url : str,
        username : str,
        password : str
    ):

        self.token = base64.b64encode(
            f"{username}:{password}".encode("iso-8859-1")
        ).decode("ascii")

        self.url = url
    

    def post(
        self,
        data : str,
        timeout : timedelta = timedelta(minutes=2)
    ) -> UniversalResponse:

        response : Response = requests.post(
            url=self.url,
            headers={
                "Authorization" : f"Basic {self.token}",
                "Content-Type" : "text/xml",
                "Accept" : "text/xml"
            },
            data = data
        )

        response.raise_for_status()

        if not response.text:
            raise ValueError("CW1 eAdaptor returned no XML response")

        response_data : UniversalResponse = parse_cw_response(response.text)

        return response_data


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()

    class MissingConfiguration(Exception): pass

    try:
        CW_URL  = os.environ["CW_EADAPTOR_URL"]
        CW_USER = os.environ["CW_EADAPTOR_USER"]
        CW_PASS = os.environ["CW_EADAPTOR_PASS"]
    except KeyError:
        raise MissingConfiguration(
            "CargoWise MCP credentials not found. "
            "Please ensure .env exists and that you have "
            "filled in values for CW_EADAPTOR_URL, "
            "CW_EADAPTOR_USER, and CW_EADAPTOR_PASS."
        )
    
    DUMMY_DATA_FILE = Path(r"\\venus\Natrio\IT\eAdaptor\XML\Sample Universal XML\US_BOL_Context_BookingParty.xml")
    with open(DUMMY_DATA_FILE, "r") as f:
        DUMMY_DATA = f.read()
    
    OUT_PATH = Path(__file__).parent / "result.xml"

    conn = CargoWiseConnection(CW_URL, CW_USER, CW_PASS)
    
    result = conn.post(
        DUMMY_DATA
    )

    print(result.status)