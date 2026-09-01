from pathlib import Path
from xml.etree import ElementTree as Tree
from xml.etree.ElementTree import Element

from xsdata_pydantic.bindings import XmlParser
from pydantic import BaseModel

from schemas import (
    UniversalActivity,
    UniversalEvent,
    UniversalResponse,
    UniversalShipment,
    UniversalTransaction,
    UniversalTransactionBatch
)

CargoWiseObject = UniversalActivity | UniversalEvent | UniversalShipment | UniversalResponse | UniversalTransaction | UniversalTransactionBatch

CW_DTYPES : [dict[str, BaseModel]] = {
    "UniversalActivity" : UniversalActivity,
    "UniversalEvent" : UniversalEvent,
    "UniversalResponse" : UniversalResponse,
    "UniversalShipment" : UniversalShipment,
    "UniversalTransaction" : UniversalTransaction,
    "UniversalTransactionBatch" : UniversalTransactionBatch
}

parser = XmlParser()

def parse_cargowise_object(
    object : Element
) -> CargoWiseObject:

    if not "Universal" in object.tag:
        raise ValueError(
            f"XML element must have a tag containing one of these values: {list(CW_DTYPES.keys())}"
        )
    
    universal_data_type = object.tag.rpartition("}")[2]

    if not universal_data_type in CW_DTYPES:
        raise ValueError(
            f"Illegal Universal Data Type: {universal_data_type}. "
            f"Should be one of these types: {list(CW_DTYPES.keys())}"
        )

    universal_class : BaseModel = CW_DTYPES.get(universal_data_type)

    data_string = Tree.tostring(object, encoding="unicode")

    content = parser.from_string(
        data_string
    )

    if not isinstance(content, universal_class):
        raise TypeError(f"Illegal {universal_data_type}: {data_string}")

    return content

def parse_cw_eadaptor_xml(
    xml_data : str
) -> list[Element]:
    tree : Tree = Tree.fromstring(xml_data)

    data_elem : Element = tree.find("{*}Data")
    if data_elem is None:
        raise ValueError("CW1 XML response missing a 'Data' element")

    # status_elem : Element = tree.find("{*}Status")
    # if status_elem is None:
    #     raise ValueError("CW1 XML response missing a 'Status' element")
    # status_code : str = status_elem.text

    objects : list[Element] = [i for i in data_elem]

    if not objects:
        raise ValueError("CW1 XML response did not contain any objects")

    return objects

if __name__ == "__main__":
        
    FILE_PATH = Path(__file__).parent / "test" / "result.xml"

    with open(FILE_PATH, "r") as f:
        xml_data : str = f.read()
    
    object : CargoWiseObject = parse_cargowise_object(
        Tree.fromstring(xml_data)
    )

    print(object)
