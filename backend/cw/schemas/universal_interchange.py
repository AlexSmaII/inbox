from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict
from xsdata_pydantic.fields import field

__NAMESPACE__ = "http://www.cargowise.com/Schemas/Universal/2011/11"


class AcknowledgementChannel(Enum):
    E_HUB = "eHub"
    E_ADAPTOR = "eAdaptor"


class AcknowledgementRequired(Enum):
    ON_ALL = "OnAll"
    ON_ERROR = "OnError"
    ON_SUCCESS = "OnSuccess"


class ValueType(Enum):
    STRING = "String"
    DATE_TIME = "DateTime"
    INTEGER = "Integer"
    DECIMAL = "Decimal"
    BYTE = "Byte"
    BOOLEAN = "Boolean"
    SHORT = "Short"
    DATE_TIME_OFFSET = "DateTimeOffset"
    GEOGRAPHY = "Geography"
    BASE64_BINARY = "Base64Binary"


class UniversalInterchange(BaseModel):
    class Meta:
        namespace = "http://www.cargowise.com/Schemas/Universal/2011/11"

    model_config = ConfigDict(defer_build=True)
    header: UniversalInterchange.Header = field(
        metadata={
            "name": "Header",
            "type": "Element",
        }
    )
    body: UniversalInterchange.Body = field(
        metadata={
            "name": "Body",
            "type": "Element",
        }
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )

    class Header(BaseModel):
        model_config = ConfigDict(defer_build=True)
        sender_id: str = field(
            metadata={
                "name": "SenderID",
                "type": "Element",
            }
        )
        recipient_id: str = field(
            metadata={
                "name": "RecipientID",
                "type": "Element",
            }
        )
        acknowledgement: None | UniversalInterchange.Header.Acknowledgement = (
            field(
                default=None,
                metadata={
                    "name": "Acknowledgement",
                    "type": "Element",
                },
            )
        )
        delivery_metadata: (
            None | UniversalInterchange.Header.DeliveryMetadata
        ) = field(
            default=None,
            metadata={
                "name": "DeliveryMetadata",
                "type": "Element",
            },
        )

        class Acknowledgement(BaseModel):
            model_config = ConfigDict(defer_build=True)
            required: AcknowledgementRequired = field(
                metadata={
                    "name": "Required",
                    "type": "Element",
                }
            )
            channel: AcknowledgementChannel = field(
                metadata={
                    "name": "Channel",
                    "type": "Element",
                }
            )
            recipient_id: str = field(
                metadata={
                    "name": "RecipientID",
                    "type": "Element",
                }
            )
            context_collection: (
                None
                | UniversalInterchange.Header.Acknowledgement.ContextCollection
            ) = field(
                default=None,
                metadata={
                    "name": "ContextCollection",
                    "type": "Element",
                },
            )

            class ContextCollection(BaseModel):
                model_config = ConfigDict(defer_build=True)
                context: list[
                    UniversalInterchange.Header.Acknowledgement.ContextCollection.Context
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "Context",
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )

                class Context(BaseModel):
                    model_config = ConfigDict(defer_build=True)
                    type_value: str = field(
                        metadata={
                            "name": "Type",
                            "type": "Element",
                        }
                    )
                    value: str = field(
                        metadata={
                            "name": "Value",
                            "type": "Element",
                        }
                    )

        class DeliveryMetadata(BaseModel):
            model_config = ConfigDict(defer_build=True)
            value_collection: (
                None
                | UniversalInterchange.Header.DeliveryMetadata.ValueCollection
            ) = field(
                default=None,
                metadata={
                    "name": "ValueCollection",
                    "type": "Element",
                },
            )

            class ValueCollection(BaseModel):
                model_config = ConfigDict(defer_build=True)
                value: list[
                    UniversalInterchange.Header.DeliveryMetadata.ValueCollection.Value
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "Value",
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )

                class Value(BaseModel):
                    model_config = ConfigDict(defer_build=True)
                    name: str = field(
                        metadata={
                            "name": "Name",
                            "type": "Element",
                        }
                    )
                    type_value: ValueType = field(
                        metadata={
                            "name": "Type",
                            "type": "Element",
                        }
                    )
                    data: str = field(
                        metadata={
                            "name": "Data",
                            "type": "Element",
                        }
                    )

    class Body(BaseModel):
        model_config = ConfigDict(defer_build=True)
        any_element: list[object] = field(
            default_factory=list,
            metadata={
                "type": "Wildcard",
                "namespace": "##any",
                "process_contents": "skip",
            },
        )
