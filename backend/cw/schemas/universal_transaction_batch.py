from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

from schemas.universal_common import TransactionBatch

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class UniversalTransactionBatchData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    transaction_batch: TransactionBatch = field(
        metadata={
            "name": "TransactionBatch",
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


class UniversalTransactionBatch(UniversalTransactionBatchData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
