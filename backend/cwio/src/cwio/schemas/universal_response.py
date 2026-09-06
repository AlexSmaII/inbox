from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class MessageNumberType(Enum):
    TRACKING_ID = "TrackingID"
    INTERCHANGE_NUMBER = "InterchangeNumber"
    MESSAGE_NUMBER = "MessageNumber"
    EXTERNAL = "External"


class UniversalResponseData(BaseModel):
    model_config = ConfigDict(defer_build=True)
    validation_rule_collection: (
        None | UniversalResponseData.ValidationRuleCollection
    ) = field(
        default=None,
        metadata={
            "name": "ValidationRuleCollection",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        },
    )
    status: str = field(
        metadata={
            "name": "Status",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
            "max_length": 3,
        }
    )
    data: UniversalResponseData.Data = field(
        metadata={
            "name": "Data",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        }
    )
    message_number_collections: (
        None | UniversalResponseData.MessageNumberCollections
    ) = field(
        default=None,
        metadata={
            "name": "MessageNumberCollections",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        },
    )
    message_number_collection: (
        None | UniversalResponseData.MessageNumberCollection
    ) = field(
        default=None,
        metadata={
            "name": "MessageNumberCollection",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        },
    )
    processing_log: None | str = field(
        default=None,
        metadata={
            "name": "ProcessingLog",
            "type": "Element",
            "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
        },
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )

    class ValidationRuleCollection(BaseModel):
        model_config = ConfigDict(defer_build=True)
        validation_rule: list[
            UniversalResponseData.ValidationRuleCollection.ValidationRule
        ] = field(
            default_factory=list,
            metadata={
                "name": "ValidationRule",
                "type": "Element",
                "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
            },
        )

        class ValidationRule(BaseModel):
            model_config = ConfigDict(defer_build=True)
            code: str = field(
                metadata={
                    "name": "Code",
                    "type": "Element",
                    "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
                }
            )
            sequence: int = field(
                metadata={
                    "name": "Sequence",
                    "type": "Element",
                    "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
                }
            )
            message_log: str = field(
                metadata={
                    "name": "MessageLog",
                    "type": "Element",
                    "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
                }
            )
            result: str = field(
                metadata={
                    "name": "Result",
                    "type": "Element",
                    "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
                }
            )

    class Data(BaseModel):
        model_config = ConfigDict(defer_build=True)
        any_element: None | object = field(
            default=None,
            metadata={
                "type": "Wildcard",
                "namespace": "##any",
                "process_contents": "skip",
            },
        )

    class MessageNumberCollections(BaseModel):
        model_config = ConfigDict(defer_build=True)
        message_number_collection: (
            None
            | UniversalResponseData.MessageNumberCollections.MessageNumberCollection
        ) = field(
            default=None,
            metadata={
                "name": "MessageNumberCollection",
                "type": "Element",
                "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
            },
        )

        class MessageNumberCollection(BaseModel):
            model_config = ConfigDict(defer_build=True)
            message_number: list[
                UniversalResponseData.MessageNumberCollections.MessageNumberCollection.MessageNumber
            ] = field(
                default_factory=list,
                metadata={
                    "name": "MessageNumber",
                    "type": "Element",
                    "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
                },
            )

            class MessageNumber(BaseModel):
                model_config = ConfigDict(defer_build=True)
                value: str = field(default="")
                type_value: None | MessageNumberType = field(
                    default=None,
                    metadata={
                        "name": "Type",
                        "type": "Attribute",
                    },
                )

    class MessageNumberCollection(BaseModel):
        model_config = ConfigDict(defer_build=True)
        message_number: list[
            UniversalResponseData.MessageNumberCollection.MessageNumber
        ] = field(
            default_factory=list,
            metadata={
                "name": "MessageNumber",
                "type": "Element",
                "namespace": "http://www.cargowise.com/Schemas/Universal/2011/11",
            },
        )

        class MessageNumber(BaseModel):
            model_config = ConfigDict(defer_build=True)
            value: str = field(default="")
            type_value: None | MessageNumberType = field(
                default=None,
                metadata={
                    "name": "Type",
                    "type": "Attribute",
                },
            )


class UniversalResponse(UniversalResponseData):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
