from __future__ import annotations

from abc import ABC, abstractmethod

from sympy import false

from core.device_context import DeviceContext
from state.database import StateDatabase


class BaseSimulationModel(ABC):
    """
    Base class for every simulation model.

    All runtime models inherit from this class.
    """

    def __init__(self, context: DeviceContext):

        self.context = context

        self.device_id = context.id

        self.db = context.database

        self.plant_database = context.plant_database

        self.command_manager = context.command_manager

        self.register_bank = context.register_bank

        self.network = context.network

        self.enabled = True

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def initialize(self) -> None:
        """
        Called once before simulation starts.
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Execute one simulation cycle.

        Parameters
        ----------
        dt
            Elapsed time in seconds.
        """
        ...

    def shutdown(self) -> None:
        """
        Called once before simulator exits.
        """
        pass

    def clear(self) -> None:
        """
        Clear runtime state held by the model.

        Permanent references such as context, database, device_id,
        and managers are intentionally preserved.
        """
        self.db.clear()
