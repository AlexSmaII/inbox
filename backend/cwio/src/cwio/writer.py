import base64
from datetime import timedelta

import requests
from requests import Response
from xsdata.formats.dataclass.serializers.mixins import SerializerConfig
from xsdata_pydantic.bindings import XmlSerializer

from cwio import credentials
from cwio.parser import parse_cw_response
from cwio.schemas import (
    CargoWiseObject,
    UniversalResponse,
)


class CargoWriter:
    """
    Connection to CargoWise One eAdaptor HTTP+XML
    interface used for writing objects.
    Uses credentials from .env by default unless
    they are given as arguments.

    Args:
        production (bool, optional):
            Use CW1 production instance rather than test instance.
            Only has any effect if no credentials are supplied.
        url (str, optional):      https://YOUR_PROVIDER_NAME.wisegrid.net/eAdaptor
        username (str, optional): CargoWise Username
        password (str, optional): CargoWise Password
    """
    
    class CW1Error(Exception): pass

    def __init__(
        self,
        production : bool = False,
        url      : str | None = None,
        username : str | None = None,
        password : str | None = None
    ):
        """
        Create a new CargoWise eAdaptor connection.
        Uses credentials from .env by default unless
        they are given as class constructor arguments.

        Args:
            production (bool, optional):
                Use CW1 production instance rather than test instance.
                Only has any effect if using default connection values.
            url (str, optional):      https://YOUR_PROVIDER_NAME.wisegrid.net/eAdaptor
            username (str, optional): CargoWise Username
            password (str, optional): CargoWise Password
        """

        if not any([
            url, username, password
        ]):
            url, username, password = credentials.write(
                production=production
            )

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
