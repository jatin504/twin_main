from dataclasses import dataclass

from protocol.datatypes import RegisterType


@dataclass(slots=True)
class RegisterMapping:
    """
    Mapping between an engineering tag and one Modbus register.
    """

    tag: str

    address: int

    datatype: RegisterType

    scale: float = 1.0

    writable: bool = False

    register_count: int = 1