from dataclasses import dataclass
from datetime import datetime

from commands.base import Command


@dataclass(slots=True)
class StartCommand(Command):
    pass


@dataclass(slots=True)
class StopCommand(Command):
    pass


@dataclass(slots=True)
class ResetCommand(Command):
    pass


@dataclass(slots=True)
class ActivePowerCommand(Command):

    power: float


@dataclass(slots=True)
class ReactivePowerCommand(Command):

    kvar: float