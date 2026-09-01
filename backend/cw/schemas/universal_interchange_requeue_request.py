from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from schemas.universal_common import InterchangeRequeueRequest

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalInterchangeRequeueRequestData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    interchange_requeue_request: InterchangeRequeueRequest = field(
        metadata={
            "name": "InterchangeRequeueRequest",
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


class UniversalInterchangeRequeueRequest(
    UniversalInterchangeRequeueRequestData
):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
