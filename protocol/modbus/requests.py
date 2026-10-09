from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ReadHoldingRegistersRequest:

    address: int

    quantity: int

    unit_id : int


@dataclass(slots=True, frozen=True)
class WriteSingleRegisterRequest:

    address: int

    value: int

    unit_id : int


@dataclass(slots=True, frozen=True)
class WriteMultipleRegistersRequest:

    address: int

    values: list[int]

    unit_id : int