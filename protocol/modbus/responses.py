from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ReadHoldingRegistersResponse:
    values: list[int]


@dataclass(slots=True, frozen=True)
class WriteSingleRegisterResponse:
    address: int
    value: int


@dataclass(slots=True, frozen=True)
class WriteMultipleRegistersResponse:
    address: int
    quantity: int