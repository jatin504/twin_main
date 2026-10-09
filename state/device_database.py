from __future__ import annotations

from typing import Any

from state.plant_database import PlantDatabase
from state.quality import Quality
from state.variable import Variable


class DeviceDatabase:
    """
    Device-scoped view of the PlantDatabase.

    Models receive this class and remain unaware of
    the overall plant structure.
    """

    def __init__(
        self,
        plant: PlantDatabase,
        device_id: str,
    ):

        self._plant = plant

        self._device_id = device_id

    # -------------------------------------------------

    @property
    def id(self):

        return self._device_id

    # -------------------------------------------------

    @property
    def _db(self):

        return self._plant.device(
            self._device_id
        )

    # -------------------------------------------------

    def add(self, variable: Variable):

        return self._db.add(variable)

    def remove(self, name: str):

        return self._db.remove(name)

    def exists(self, name: str):

        return self._db.exists(name)

    def get(self, name: str):

        return self._db.get(name)

    def value(self, name: str):

        return self._db.value(name)

    def quality(self, name: str):

        return self._db.quality(name)

    def set(
        self,
        name: str,
        value: Any,
        quality: Quality = Quality.GOOD,
    ):

        return self._db.set(
            name,
            value,
            quality,
        )

    def changed(self):

        return self._db.changed()

    def reset_dirty(self):

        return self._db.reset_dirty()

    def snapshot(self):

        return self._db.snapshot()

    def clear(self):

        return self._db.clear()

    def __len__(self):

        return len(self._db)

    def __contains__(self, name):

        return name in self._db

    def __iter__(self):

        return iter(self._db)

    def __repr__(self):

        return (
            f"DeviceDatabase("
            f"device='{self.id}')"
        )