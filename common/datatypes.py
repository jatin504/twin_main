"""
Shared datatypes for the PCS simulator.

Every subsystem owns one dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.context import SimulationMetadata
from common.enums import (
    AlarmState,
    BatteryState,
    CommandSource,
    GridMode,
    HealthStatus,
    PCSState,
    SimulationStatus,
)


# ==========================================================
# Commands
# ==========================================================

@dataclass(slots=True)
class CommandData:
    """Commands received from EMS / Modbus / API."""

    start: bool = False
    stop: bool = False
    reset_fault: bool = False

    active_power_kw: float = 0.0
    reactive_power_kvar: float = 0.0

    source: CommandSource = CommandSource.EMS


# ==========================================================
# Measurements
# ==========================================================

@dataclass(slots=True)
class MeasurementData:
    """Measurements exposed by the PCS."""

    active_power_kw: float = 0.0
    reactive_power_kvar: float = 0.0

    dc_voltage_v: float = 1200.0
    dc_current_a: float = 0.0

    ac_voltage_v: float = 690.0
    ac_current_a: float = 0.0

    frequency_hz: float = 50.0


# ==========================================================
# Grid
# ==========================================================

@dataclass(slots=True)
class GridData:

    available: bool = True

    mode: GridMode = GridMode.GRID_CONNECTED

    voltage_ll_v: float = 690.0

    frequency_hz: float = 50.0

    phase_angle_deg: float = 0.0

    rocof_hz_per_sec: float = 0.0


# ==========================================================
# Battery
# ==========================================================

@dataclass(slots=True)
class BatteryData:

    soc: float = 75.0

    soh: float = 100.0

    voltage_v: float = 1200.0

    current_a: float = 0.0

    temperature_c: float = 25.0

    capacity_kwh: float = 3725.0

    max_charge_power_kw: float = 3500.0

    max_discharge_power_kw: float = 3500.0

    state: BatteryState = BatteryState.IDLE


# ==========================================================
# Thermal
# ==========================================================

@dataclass(slots=True)
class ThermalData:

    ambient_temp_c: float = 25.0

    igbt_temp_c: float = 30.0

    reactor_temp_c: float = 30.0

    coolant_temp_c: float = 25.0

    fan_speed_percent: float = 0.0

    pump_speed_percent: float = 0.0


# ==========================================================
# Protection
# ==========================================================

@dataclass(slots=True)
class ProtectionData:

    alarm_state: AlarmState = AlarmState.NORMAL

    trip_active: bool = False

    trip_reason: str | None = None

    active_faults: list[str] = field(default_factory=list)


# ==========================================================
# Simulator Status
# ==========================================================

@dataclass(slots=True)
class StatusData:

    simulation: SimulationStatus = SimulationStatus.STOPPED

    pcs_state: PCSState = PCSState.OFF

    health: HealthStatus = HealthStatus.HEALTHY

    uptime_sec: float = 0.0

    cycle_count: int = 0

    metadata: SimulationMetadata = field(default_factory=SimulationMetadata)