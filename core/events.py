"""
Typed Event Bus

Every module communicates through events.

No module should call another module directly.

Battery
   │
   ▼
publish(BatterySOCChanged)

Protection
   │
   ▼
publish(FaultRaised)

Dashboard
   │
   ▼
subscribes()

Modbus
   │
   ▼
subscribes()

Logger
   │
   ▼
subscribes()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable, Type, TypeVar, Any

# ======================================================
# Base Event
# ======================================================


@dataclass(slots=True)
class Event:
    """
    Base event.
    """

    timestamp: float
    source: str
    correlation_id: str | None = None


# ======================================================
# Generic typing
# ======================================================

T = TypeVar("T", bound=Event)

Subscriber = Callable[[Event], None]


# ======================================================
# Event Bus
# ======================================================

class EventBus:

    """
    Simple typed publish/subscribe bus.
    """

    def __init__(self):

        self._subscribers: dict[
            Type[Event],
            list[Subscriber]
        ] = defaultdict(list)

    # -------------------------------------------------

    def subscribe(
        self,
        event_type: Type[T],
        callback: Callable[[T], None],
    ) -> None:

        self._subscribers[event_type].append(callback)

    # -------------------------------------------------

    def unsubscribe(
        self,
        event_type: Type[T],
        callback: Callable[[T], None],
    ) -> None:

        if callback in self._subscribers[event_type]:

            self._subscribers[event_type].remove(callback)

    # -------------------------------------------------

    def publish(self, event: Event) -> None:

        event_type = type(event)

        for callback in self._subscribers[event_type]:

            callback(event)

    # -------------------------------------------------

    def clear(self):

        self._subscribers.clear()


@dataclass(slots=True)
class StartCommandEvent(Event):
    pass


@dataclass(slots=True)
class StartCommandEvent(Event):
    pass


from common.enums import ProtectionType


@dataclass(slots=True)
class FaultRaisedEvent(Event):

    fault: ProtectionType

    description: str


from common.enums import ProtectionType


@dataclass(slots=True)
class FaultRaisedEvent(Event):

    fault: ProtectionType

    description: str


@dataclass(slots=True)
class FaultClearedEvent(Event):

    fault: ProtectionType


@dataclass(slots=True)
class GridStatusChangedEvent(Event):

    available: bool

    voltage: float

    frequency: float


@dataclass(slots=True)
class SOCChangedEvent(Event):

    previous_soc: float

    current_soc: float