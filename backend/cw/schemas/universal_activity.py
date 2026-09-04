from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from cw.schemas.universal_common import Activity

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalActivityData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    activity: Activity = field(
        metadata={
            "name": "Activity",
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


class UniversalActivity(UniversalActivityData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
