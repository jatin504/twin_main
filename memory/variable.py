from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class DataType(Enum):
    BOOL = auto()
    INT16 = auto()
    UINT16 = auto()
    INT32 = auto()
    UINT32 = auto()
    FLOAT32 = auto()
    STRING = auto()


@dataclass(slots=True)
class MemoryVariable:
    """
    Internal PCS memory variable.

    This class represents the real engineering value,
    not its protocol representation.
    """

    name: str

    datatype: DataType

    value: object

    unit: str = ""

    writable: bool = False

    description: str = ""

    quality: int = 0

    timestamp: float = 0.0