from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from schemas.universal_common import ActivityRequest

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalActivityRequestData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    activity_request: ActivityRequest = field(
        metadata={
            "name": "ActivityRequest",
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


class UniversalActivityRequest(UniversalActivityRequestData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
