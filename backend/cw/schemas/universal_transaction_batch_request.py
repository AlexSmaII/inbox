from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from cw.schemas.universal_common import TransactionBatchRequest

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalTransactionBatchRequestData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    transaction_batch_request: TransactionBatchRequest = field(
        metadata={
            "name": "TransactionBatchRequest",
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


class UniversalTransactionBatchRequest(UniversalTransactionBatchRequestData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
