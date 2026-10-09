"""
Engineering Quality Codes

These quality codes describe the validity of every engineering
variable stored inside the StateDatabase.

The quality is protocol-independent and can later be mapped
to Modbus status bits, IEC61850 quality, MQTT metadata, etc.
"""

from __future__ import annotations

from enum import IntEnum


class Quality(IntEnum):
    """
    OPC/SCADA inspired quality codes.
    """

    GOOD = 0

    UNCERTAIN = 1

    BAD = 2

    COMMUNICATION_LOST = 3

    SENSOR_FAILURE = 4

    OUT_OF_RANGE = 5

    NOT_INITIALIZED = 6

    SIMULATED = 7

    OVERRIDDEN = 8

    CALCULATED = 9

    TEST = 10

    FAULT = 11

    DISABLED = 12

    UNKNOWN = 255

    @property
    def is_good(self) -> bool:
        return self == Quality.GOOD

    @property
    def is_bad(self) -> bool:
        return self in {
            Quality.BAD,
            Quality.COMMUNICATION_LOST,
            Quality.SENSOR_FAILURE,
            Quality.OUT_OF_RANGE,
            Quality.NOT_INITIALIZED,
            Quality.FAULT,
            Quality.DISABLED,
            Quality.UNKNOWN,
        }