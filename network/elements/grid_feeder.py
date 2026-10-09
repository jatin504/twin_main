from dataclasses import dataclass


@dataclass(slots=True)
class GridFeeder:

    id: str

    bus: str

    converter: str

    phases: int = 3