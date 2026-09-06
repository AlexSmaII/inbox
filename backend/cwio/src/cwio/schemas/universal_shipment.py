from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from cwio.schemas.universal_common import Shipment

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalShipmentData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    shipment: Shipment = field(
        metadata={
            "name": "Shipment",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        }
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


class UniversalShipment(UniversalShipmentData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
