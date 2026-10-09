from dataclasses import dataclass, field


@dataclass
class Bus:

    name: str

    voltage: float


@dataclass
class Line:

    name: str

    from_bus: str

    to_bus: str

    resistance: float

    reactance: float


@dataclass
class Transformer:

    name: str

    hv_bus: str

    lv_bus: str

    kva: float

    hv_voltage: float

    lv_voltage: float


@dataclass
class Generator:

    name: str

    type: str

    bus: str


@dataclass
class Load:

    name: str

    bus: str

    default_kw: float

@dataclass(slots=True)
class Converter:

    id: str

    rated_power_kva: float

    dc_voltage: float

    filter_r: float

    filter_l: float

    filter_c: float

    control_mode: str

    soc_max_kwh: float

    soc_initial_kwh: float

@dataclass(slots=True)
class GridFeeder:

    id: str

    bus: str

    converter: str

    phases: int = 3


@dataclass
class PlantTopology:

    name: str

    base_voltage: float

    base_frequency: float

    buses: list[Bus] = field(default_factory=list)

    transformers: list[Transformer] = field(default_factory=list)

    lines: list[Line] = field(default_factory=list)

    generators: list[Generator] = field(default_factory=list)

    loads: list[Load] = field(default_factory=list)

    converters: list[Converter] = field(default_factory=list)

    grid_feeders: list[GridFeeder] = field(default_factory=list)