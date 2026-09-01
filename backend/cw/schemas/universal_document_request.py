from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from schemas.universal_common import DocumentRequest

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalDocumentRequestData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    document_request: DocumentRequest = field(
        metadata={
            "name": "DocumentRequest",
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


class UniversalDocumentRequest(UniversalDocumentRequestData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
