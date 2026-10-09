"""
Enumerations used throughout the simulator.

Using Enums instead of strings eliminates typing mistakes
and makes IDE auto-completion much better.
"""

from __future__ import annotations

from enum import Enum, IntEnum, auto


class SimulationStatus(Enum):
    STOPPED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    SHUTTING_DOWN = auto()


class PCSState(IntEnum):
    OFF = 0
    BOOT = 1
    PRECHARGE = 2
    READY = 3
    GRID_FOLLOWING = 4
    GRID_FORMING = 5
    BLACK_START = 6
    SYNCHRONIZING = 7
    FAULT = 8
    SHUTDOWN = 9


class AlarmState(Enum):
    NORMAL = auto()
    WARNING = auto()
    ALARM = auto()
    TRIP = auto()


class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ProtectionType(Enum):
    OVER_VOLTAGE = auto()
    UNDER_VOLTAGE = auto()
    OVER_CURRENT = auto()
    OVER_TEMPERATURE = auto()
    UNDER_FREQUENCY = auto()
    OVER_FREQUENCY = auto()
    GROUND_FAULT = auto()
    INSULATION_FAULT = auto()
    EMERGENCY_STOP = auto()


class FaultCode(IntEnum):

    NONE = 0

    GRID_LOSS = 1

    OVER_VOLTAGE = 2

    UNDER_VOLTAGE = 3

    OVER_FREQUENCY = 4

    UNDER_FREQUENCY = 5

    BMS_FAULT = 6

    EMERGENCY_STOP = 7

    OVER_TEMPERATURE = 8

    TRANSFORMER_OVERLOADING = 9

    TRANSFORMER_UNDERLOADING = 10


class GridMode(Enum):
    UNKNOWN = auto()
    GRID_CONNECTED = auto()
    ISLANDED = auto()

class GridSource(IntEnum):
    UTILITY = 0
    PCS = 1
    PV = 2

class ConverterControlMode(Enum):

    PQ_REFERENCE = 12

class CommandSource(Enum):
    LOCAL = auto()
    EMS = auto()
    MODBUS = auto()
    API = auto()


class SimulationMode(Enum):
    REALTIME = auto()
    ACCELERATED = auto()
    PAUSED = auto()


class PowerDirection(Enum):
    CHARGE = auto()
    DISCHARGE = auto()
    IDLE = auto()


class BatteryState(Enum):
    IDLE = auto()
    CHARGING = auto()
    DISCHARGING = auto()


class HealthStatus(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    FAILED = auto()