import base64
from datetime import timedelta

import requests
from parser import parse_cw_response
from requests import Response
from schemas import (
    CargoWiseObject,
    UniversalResponse,
)
from xsdata.formats.dataclass.serializers.mixins import SerializerConfig
from xsdata_pydantic.bindings import XmlSerializer


class CargoWriter:
    """
    Connection to CargoWise One eAdaptor HTTP+XML
    interface used for writing objects.

    Args:
        url (str):      https://YOUR_PROVIDER_NAME.wisegrid.net/eAdaptor
        username (str): CargoWise Username
        password (str): CargoWise Password
    """
    
    class CW1Error(Exception): pass

    def __init__(
        self,
        url : str,
        username : str,
        password : str
    ):
        """
        Create a new CargoWise eAdaptor connection.

        Args:
            url (str):      https://YOUR_PROVIDER_NAME.wisegrid.net/eAdaptor
            username (str): CargoWise Username
            password (str): CargoWise Password
        """

        self.token = base64.b64encode(
            f"{username}:{password}".encode("iso-8859-1")
        ).decode("ascii")

        self.url = url

        self.CW_NAMESPACE = "http://www.cargowise.com/Schemas/Universal/2011/11"

        self.serializer = XmlSerializer(
            config=SerializerConfig(
                xml_declaration=False,
                xml_version="1.1",
                indent="  "
            )
        )

    
    def _serialize_cargowise_object(
        self,
        data : CargoWiseObject
    ) -> str:
        """
        Convert a Pydantic BaseModel representation of a
        Universal XML Object (see eAdaptor Developer's Guide)
        into an XML string which can be sent to the eAdaptor
        through a HTTP POST request to post data to CargoWise.

        Args:
            data (CargoWiseObject):
                A Pydantic BaseModel representing a Universal
                XML Event, Transaction, Transaction Batch,
                Shipment, or Activity.

        Raises:
            ValueError: The object could not be serialised.

        Returns:
            str: The XML string.
        """
        try:
            xml_string = self.serializer.render(
                data,
                ns_map={None: self.CW_NAMESPACE}
            )
        except Exception as e:
            raise ValueError(f"Failed to serialise XML object: {e!s}")
        
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

        http_response : Response = requests.post(
            url=self.url,
            headers={
                "Authorization" : f"Basic {self.token}",
                "Content-Type" : "text/xml",
                "Accept" : "text/xml"
            },
            data = xml_string,
            timeout = timeout.total_seconds()
        )

        http_response.raise_for_status()

        if not http_response.text:
            raise ValueError("CW1 eAdaptor returned no XML response")

        response : UniversalResponse = parse_cw_response(http_response.text)

        if response.status == "ERR":
            raise self.CW1Error(
                "Error querying CargoWise:\n"
                f"{response.processing_log}"
            )

        return response


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

    conn = CargoWriter(CW_URL, CW_USER, CW_PASS)
    
    from schemas import (
        DataContext,
        DocumentRequest,
        # Event,
        UniversalDocumentRequest,
        # UniversalEvent,
    )
    
    QUERY = UniversalDocumentRequest(
        document_request=DocumentRequest(
            data_context=DataContext()
        )
    )

    # DUMMY_DATA = UniversalEvent(
    #     event=Event(
    #         event_time=datetime.now(timezone.utc).isoformat(),
    #         event_type="ARV"
    #     )
    # )

    print("Sending query to CargoWise:")
    print(conn._serialize_cargowise_object(QUERY))
    
    result = conn.post(QUERY)

    print("Received successful response:")
    print(result.model_dump_json(indent=4))