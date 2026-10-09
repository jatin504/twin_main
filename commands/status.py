from enum import Enum


class CommandStatus(Enum):

    PENDING = 0

    ACCEPTED = 1

    RUNNING = 2

    COMPLETED = 3

    REJECTED = 4

    FAILED = 5