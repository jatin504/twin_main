"""
Engineering Variable

This module defines the fundamental data object used throughout the
simulation engine.

Every engineering point in the PCS Twin is represented as a Variable.

Examples
--------
Battery.SOC
Battery.Voltage
PCS.ActivePower
PCS.ReactivePower
Grid.Voltage
Grid.Frequency
Protection.AlarmCode
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Any

from state.quality import Quality
from common.constants import IST


@dataclass(slots=True)
class VariableMetadata:
    """
    Static information about an engineering variable.
    """

    name: str
    datatype: type
    unit: str = ""
    description: str = ""
    writable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    precision: int | None = None
    enable_store: bool = False


class Variable:
    """
    Represents one engineering value.

    Thread-safe.

    Tracks quality, timestamp and changes.
    """

    __slots__ = (
        "_metadata",
        "_value",
        "_quality",
        "_timestamp",
        "_dirty",
        "_lock",
    )

    def __init__(
        self,
        metadata: VariableMetadata,
        initial_value: Any = None,
        quality: Quality = Quality.NOT_INITIALIZED,
    ):

        self._metadata = metadata

        self._value = initial_value

        self._quality = quality

        self._timestamp = datetime.now(IST)

        self._dirty = True

        self._lock = RLock()

    # -------------------------------------------------

    @property
    def metadata(self) -> VariableMetadata:
        return self._metadata

    @property
    def name(self) -> str:
        return self._metadata.name

    @property
    def value(self) -> Any:
        return self._value

    @property
    def quality(self) -> Quality:
        return self._quality

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def enable_store(self) -> bool:
        return self._metadata.enable_store

    @enable_store.setter
    def enable_store(self, value: bool) -> None:
        self._metadata.enable_store = value

    # -------------------------------------------------

    def set(
        self,
        value: Any,
        quality: Quality = Quality.GOOD,
    ) -> None:
        """
        Update variable value.

        Marks variable dirty only when value changes.
        """

        with self._lock:

            if self._metadata.writable is False and self._dirty is False:
                # writable applies to protocol writes.
                # Internal simulator can still update.
                pass

            if value == self._value and quality == self._quality:
                return

            # Range validation
            if isinstance(value, (int, float)):
                if (
                    self._metadata.minimum is not None
                    and value < self._metadata.minimum
                ):
                    quality = Quality.OUT_OF_RANGE

                if (
                    self._metadata.maximum is not None
                    and value > self._metadata.maximum
                ):
                    quality = Quality.OUT_OF_RANGE

            self._value = value
            self._quality = quality
            self._timestamp = datetime.now(IST)
            self._dirty = True

    # -------------------------------------------------

    def acknowledge(self) -> None:
        """
        Clear dirty flag after mapper/database synchronization.
        """
        with self._lock:
            self._dirty = False

    # -------------------------------------------------

    def force_quality(self, quality: Quality) -> None:
        with self._lock:
            self._quality = quality
            self._timestamp = datetime.now(IST)
            self._dirty = True

    # -------------------------------------------------

    def as_dict(self) -> dict:
        """
        Serialize variable.
        """

        return {
            "name": self.name,
            "value": self._value,
            "quality": self._quality.name,
            "timestamp": self._timestamp.isoformat(),
            "unit": self._metadata.unit,
            "dirty": self._dirty,
            "enable_store": self.enable_store,
        }

    # -------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Variable("
            f"name={self.name}, "
            f"value={self._value}, "
            f"quality={self._quality.name})"
        )