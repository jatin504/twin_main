"""
Configuration loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


# ---------------------------------------------------
# Sections
# ---------------------------------------------------

@dataclass(slots=True)
class SimulationConfig:
    dt: float
    realtime: bool
    realtime_factor: float


@dataclass(slots=True)
class LoggingConfig:
    level: str
    console: bool
    file: bool
    directory: str


@dataclass(slots=True)
class GridConfig:
    nominal_voltage: float
    nominal_frequency: float


@dataclass(slots=True)
class BatteryConfig:
    capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float


@dataclass(slots=True)
class SchedulerConfig:
    tick_ms: int


# ---------------------------------------------------
# Root Config
# ---------------------------------------------------

@dataclass(slots=True)
class Config:
    simulation: SimulationConfig
    logging: LoggingConfig
    grid: GridConfig
    battery: BatteryConfig
    scheduler: SchedulerConfig


# ---------------------------------------------------
# Loader
# ---------------------------------------------------

def load_config(path: str | Path) -> Config:

    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Config(

        simulation=SimulationConfig(**raw["simulation"]),

        logging=LoggingConfig(**raw["logging"]),

        grid=GridConfig(**raw["grid"]),

        battery=BatteryConfig(**raw["battery"]),

        scheduler=SchedulerConfig(**raw["scheduler"]),
    )