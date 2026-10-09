"""
Central Simulation Context.

Every model reads and writes ONLY through this object.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from common.datatypes import (
    BatteryData,
    CommandData,
    GridData,
    MeasurementData,
    ProtectionData,
    StatusData,
    ThermalData,
)


@dataclass(slots=True)
class SimulationContext:
    """
    Shared memory of the simulator.

    Every subsystem owns one section.

    No subsystem should directly reference another subsystem.
    """

    command: CommandData = field(default_factory=CommandData)

    measurement: MeasurementData = field(default_factory=MeasurementData)

    battery: BatteryData = field(default_factory=BatteryData)

    grid: GridData = field(default_factory=GridData)

    thermal: ThermalData = field(default_factory=ThermalData)

    protection: ProtectionData = field(default_factory=ProtectionData)

    status: StatusData = field(default_factory=StatusData)


@dataclass(slots=True)
class SimulationMetadata:
    simulation_time_sec: float = 0.0
    dt: float = 0.1
    realtime_factor: float = 1.0
    running: bool = False