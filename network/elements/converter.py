from dataclasses import dataclass


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