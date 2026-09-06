import re
from xml.etree import ElementTree as Tree

from xsdata_pydantic.bindings import XmlParser

from cwio.schemas import UniversalResponse

parser = XmlParser()

def parse_cw_response(
    response : str
) -> UniversalResponse:
    """
    Parse a CargoWise One eAdaptor HTTP+XML
    response into a UniversalResponse object.

    Args:
        response (str): The CW1 XML response as a string.

    Raises:
        ValueError: Could not parse the XML object into a UniversalResponse.

    Returns:
        UniversalResponse: The formatted response
    """    

    object : Tree = Tree.fromstring(response)

    if not re.match(r"\{.*\}UniversalResponse", object.tag):
        raise ValueError(f"Not a CW1 eAdaptor HTTP+XML response: {response}")
    
    try:
        content = parser.from_string(
            response
        )
    except Exception as e:
        raise ValueError(
            "Failed to parse CW1 eAdaptor HTTP+XML response. "
            f"Traceback: {e!s}"
        )

    if not isinstance(content, UniversalResponse):
        raise ValueError(
            f"Not a CW1 eAdaptor HTTP+XML response: {response}"
        )

    return content
