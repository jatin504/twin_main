from dataclasses import dataclass

from common.config import Config
from common.logger import create_logger
from core.clock import SimulationClock
from core.context import SimulationContext
from core.events import EventBus


@dataclass(slots=True)
class Services:

    config: Config

    context: SimulationContext

    logger: object

    clock: SimulationClock

    events: EventBus