from dataclasses import dataclass


@dataclass
class Bus:

    name: str


@dataclass
class Generator:

    name: str

    bus: str

    p_kw: float = 0.0

    q_kvar: float = 0.0


@dataclass
class Load:

    name: str

    bus: str

    p_kw: float = 0.0

    q_kvar: float = 0.0