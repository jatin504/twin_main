from dataclasses import dataclass

from protocol.datatypes import RegisterType


@dataclass(slots=True)
class Register:

    address: int

    name: str

    datatype: RegisterType

    scale: float = 1.0

    writable: bool = False

    description: str = ""


@dataclass(frozen=True, slots=True)
class RegisterAddress:
    value: int