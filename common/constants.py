"""
Global immutable constants.

These values should never change during runtime.
"""

from __future__ import annotations

from datetime import timezone, timedelta

IST: timezone = timezone(timedelta(hours=5, minutes=30), name="IST")

SIMULATION_STEP_SEC: float = 0.1

DEFAULT_GRID_VOLTAGE: float = 690.0

BASE_HV_VOLTAGE: float = 33000.0

BASE_LV_VOLTAGE: float = 433.0

DEFAULT_GRID_FREQUENCY: float = 49.0

DEFAULT_GRID_AVAILABLE: bool = True

DEFAULT_SOC: float = 25.0

DEFAULT_SOH: float = 100.0

DEFAULT_AMBIENT_TEMP: float = 25.0

DEFAULT_DC_BUS: float = 1200.0

DEFAULT_CAPACITY_KWH: float = 4000#5016

DEFAULT_MAX_CHARGE_POWER_KW: float = 1000#2508

DEFAULT_MAX_DISCHARGE_POWER_KW: float = 1000#2508

DEFAULT_BATTERY_VOLTAGE_V: float = 1000.0

DEFAULT_BATTERY_CURRENT_A: float = 0.0

DEFAULT_BATTERY_TEMPERATURE_C: float = 25.0

MIN_SOC: float = 20.0

MAX_SOC: float = 80.0

DEFAULT_RAMP_RATE_KW_PER_SEC: float = 500.0

NOMINAL_POWER_KW: float = 1000#3500.0

NOMINAL_CURRENT_A: float = 2928.0

NOMINAL_EFFICIENCY: float = 0.986

SECONDS_PER_HOUR: int = 3600

MILLISECONDS: float = 1000.0


# Cell / Pack configuration
SERIES_CELLS = 416
PARALLEL_CELLS = 2
PARALLEL_STRINGS = 6

TOTAL_PARALLEL = PARALLEL_CELLS * PARALLEL_STRINGS

PACK_CAPACITY_KWH = 5016.0
PACK_CAPACITY_AH = 3768.0

MAX_POWER_KW = 2500.0