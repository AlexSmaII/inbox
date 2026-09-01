from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from schemas.universal_common import Schedule

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalScheduleData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    schedule: Schedule = field(
        metadata={
            "name": "Schedule",
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


class UniversalSchedule(UniversalScheduleData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
