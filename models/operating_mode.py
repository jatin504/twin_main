from enum import IntEnum


class OperatingMode(IntEnum):

    OFF = 0

    STANDBY = 1

    GRID_FOLLOWING = 2

    GRID_FORMING = 3