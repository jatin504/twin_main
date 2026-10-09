from dataclasses import dataclass

from common.constants import DEFAULT_SOC, DEFAULT_SOH


@dataclass
class BatteryState:

    soc: float = DEFAULT_SOC
    soh: float = DEFAULT_SOH

    power: float = 0.0
    current: float = 0.0

    voltage: float = 0.0
    terminal_voltage: float = 0.0
    ocv: float = 0.0

    capacity: float = 0.0
    discharge_ah: float = 0.0
    stored_energy: float = 0.0
    available_energy: float = 0.0

    available_charge_power: float = 0.0
    available_discharge_power: float = 0.0

    temperature: float = 25.0
    core_temperature: float = 25.0
    surface_temperature: float = 25.0

    internal_resistance: float = 0.0

    efficiency: float = 1.0

    cycle_count: float = 0.0

    charge_throughput: float = 0.0
    discharge_throughput: float = 0.0