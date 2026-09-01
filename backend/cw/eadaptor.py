import base64
from datetime import timedelta
from pathlib import Path
from xml.etree import ElementTree as Tree

import requests
from parser import parse_cw_response
from requests import Response
from schemas import (
    UniversalActivity,
    UniversalEvent,
    UniversalResponse,
    UniversalShipment,
    UniversalTransaction,
    UniversalTransactionBatch,
)
from xsdata_pydantic.bindings import XmlSerializer
from xsdata.formats.dataclass.serializers.mixins import SerializerConfig

CargoWiseObject = UniversalActivity | UniversalEvent | UniversalShipment | UniversalResponse | UniversalTransaction | UniversalTransactionBatch

CW_NAMESPACE = "http://www.cargowise.com/Schemas/Universal/2011/11"

serializer = XmlSerializer(
    config=SerializerConfig(
        xml_declaration=False,
        xml_version="1.1",
        indent="  "
    )
)

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
    
    
    def _serialize_cargowise_object(
        self,
        data : CargoWiseObject
    ) -> str:
        try:
            xml_string = serializer.render(
                data,
                ns_map={None: CW_NAMESPACE}
            )
        except Exception as e:
            raise ValueError(f"Failed to serialise XML object: {str(e)}")
        
        return xml_string


    def post(
        self,
        data : CargoWiseObject,
        timeout : timedelta = timedelta(minutes=2)
    ) -> UniversalResponse:
        """
        Push a new object to CargoWise One through
        the eAdaptor using HTTP+XML transport.

        Args:
            data (CargoWiseObject):
                The Universal XML object to push.
            timeout (timedelta, optional):
                How long to wait for the request to finish.
                Defaults to 2 minutes.

        Raises:
            ValueError: Failed to serialise Universal XML object.
            HTTPError: Received a non-200 response from the CW1 API.
            ValueError: eAdaptor returned no response content.
            ValueError: Failed to parse eAdaptor response from XML string.

        Returns:
            UniversalResponse: The eAdaptor's response.
        """
        xml_string = self._serialize_cargowise_object(data)

        response : Response = requests.post(
            url=self.url,
            headers={
                "Authorization" : f"Basic {self.token}",
                "Content-Type" : "text/xml",
                "Accept" : "text/xml"
            },
            data = xml_string,
            timeout = timeout.total_seconds()
        )

        response.raise_for_status()

        if not response.text:
            raise ValueError("CW1 eAdaptor returned no XML response")

        response_data : UniversalResponse = parse_cw_response(response.text)

        return response_data


if __name__ == "__main__":
    from datetime import datetime, timezone
    import os

    from dotenv import load_dotenv
    from schemas import Event

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

    conn = CargoWiseConnection(CW_URL, CW_USER, CW_PASS)
    
    # DUMMY_DATA_FILE = Path(r"\\venus\Natrio\IT\eAdaptor\XML\Sample Universal XML\US_BOL_Context_BookingParty.xml")
    # with open(DUMMY_DATA_FILE, "r") as f:
    #     DUMMY_DATA = f.read()
    
    DUMMY_DATA = UniversalEvent(
        event=Event(
            event_time=datetime.now(timezone.utc).isoformat(),
            event_type="ABC"
        )
    )

    result = conn._serialize_cargowise_object(DUMMY_DATA)#post(DUMMY_DATA)

    OUT_PATH = Path(__file__).parent / "test" / "result2.xml"

    with open(OUT_PATH, "w") as f:
        f.write(result)
    
    result = conn.post(DUMMY_DATA)

    print(result)