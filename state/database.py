"""
Engineering State Database

Single source of truth for every engineering value in the simulator.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from threading import RLock
from typing import Any

from state.variable import Variable
from state.quality import Quality
from common.constants import IST


import os

class StateDatabase:
    """
    Thread-safe engineering database.

    Owns every engineering variable.

    Models never talk to each other.
    They communicate only through this database.
    """

    def __init__(
        self,
        history_window_sec: float | None = None,
        history_max_samples: int | None = None,
    ):

        self._variables: dict[str, Variable] = {}

        self._history: dict[str, deque] = {}
        from common.history_config import load_history_config
        cfg = load_history_config()
        self._history_window_sec: float = (
            history_window_sec if history_window_sec is not None else cfg.history_window_seconds
        )
        self._history_max_samples: int = (
            history_max_samples if history_max_samples is not None else cfg.history_max_samples
        )

        self._lock = RLock()

    @property
    def history_window_sec(self) -> float:
        return self._history_window_sec

    @property
    def history_max_samples(self) -> int:
        return self._history_max_samples

    def set_history_window(
        self,
        window_sec: float,
        max_samples: int | None = None,
    ) -> None:
        """
        Configure the rolling history window duration in seconds.
        E.g. 900 for 15 minutes, 1800 for 30 minutes, 3600 for 1 hour.
        """
        with self._lock:
            self._history_window_sec = float(window_sec)
            self._history_max_samples = (
                max_samples if max_samples is not None else max(1, int(window_sec / 0.5))
            )
            for name, dq in self._history.items():
                self._history[name] = deque(dq, maxlen=self._history_max_samples)

    # -------------------------------------------------

    def add(self, variable: Variable) -> None:

        with self._lock:

            if variable.name in self._variables:

                raise ValueError(
                    f"Variable '{variable.name}' already exists."
                )

            self._variables[variable.name] = variable

    # -------------------------------------------------

    def remove(self, name: str) -> None:

        with self._lock:

            self._variables.pop(name, None)

    # -------------------------------------------------

    def exists(self, name: str) -> bool:

        return name in self._variables

    # -------------------------------------------------

    def get(self, name: str) -> Variable:

        try:

            return self._variables[name]

        except KeyError as ex:

            raise KeyError(
                f"Unknown engineering variable '{name}'."
            ) from ex

    # -------------------------------------------------

    def value(self, name: str) -> Any:

        return self.get(name).value

    # -------------------------------------------------

    def quality(self, name: str) -> Quality:

        return self.get(name).quality

    # -------------------------------------------------

    def set(
        self,
        name: str,
        value: Any,
        quality: Quality = Quality.GOOD,
    ) -> None:

        self.get(name).set(value, quality)

    # -------------------------------------------------

    def changed(self) -> list[Variable]:

        return [

            variable

            for variable in self._variables.values()

            if variable.dirty

        ]

    # -------------------------------------------------

    def reset_dirty(self) -> None:

        for variable in self.changed():

            variable.acknowledge()

    # -------------------------------------------------

    def snapshot(self) -> dict[str, dict]:

        return {

            variable.name: variable.as_dict()

            for variable in self._variables.values()

        }

    # -------------------------------------------------

    def record_history(self, timestamp: datetime | None = None) -> dict[str, Any]:
        """
        Record a snapshot of all variables that have enable_store=True.
        Maintains a rolling 1-hour buffer (pruning data older than 1 hour).
        """
        with self._lock:
            if timestamp is not None:
                if timestamp.tzinfo is None:
                    now = timestamp.replace(tzinfo=IST)
                else:
                    now = timestamp.astimezone(IST)
            else:
                now = datetime.now(IST)
            now_ts = now.timestamp()
            now_iso = now.isoformat()
            cutoff = now_ts - self._history_window_sec

            recorded = {}
            for variable in self._variables.values():
                if variable.enable_store:
                    name = variable.name
                    if name not in self._history:
                        self._history[name] = deque(maxlen=self._history_max_samples)

                    dq = self._history[name]
                    entry = {
                        "timestamp": now_iso,
                        "time": now_ts,
                        "value": variable.value,
                        "quality": variable.quality.name,
                    }
                    dq.append(entry)

                    # Prune samples older than rolling window
                    while dq and dq[0]["time"] < cutoff:
                        dq.popleft()

                    recorded[name] = entry

            return recorded

    # -------------------------------------------------

    def get_history(
        self,
        name: str | None = None,
        last_seconds: float | None = 3600.0,
    ) -> list[dict] | dict[str, list[dict]]:
        """
        Retrieve historical samples.
        If name is provided, returns list of samples for that variable.
        If name is None, returns a dictionary of all recorded variables and their samples.
        """
        with self._lock:
            now_ts = datetime.now(IST).timestamp()
            cutoff = (now_ts - last_seconds) if last_seconds is not None else 0.0

            if name is not None:
                dq = self._history.get(name)
                if dq is None:
                    return []
                return [entry for entry in dq if entry["time"] >= cutoff]

            result = {}
            for var_name, dq in self._history.items():
                result[var_name] = [entry for entry in dq if entry["time"] >= cutoff]
            return result

    # -------------------------------------------------

    def enable_history(self, name: str, enabled: bool = True) -> None:
        """
        Dynamically enable or disable history recording for a variable.
        """
        with self._lock:
            variable = self.get(name)
            variable.enable_store = enabled

    # -------------------------------------------------

    def clear_history(self, name: str | None = None) -> None:
        """
        Clear history for a specific variable or all variables.
        """
        with self._lock:
            if name is not None:
                self._history.pop(name, None)
            else:
                self._history.clear()

    # -------------------------------------------------

    def clear(self) -> None:

        with self._lock:

            self._variables.clear()
            self._history.clear()

    # -------------------------------------------------

    def __len__(self) -> int:

        return len(self._variables)

    # -------------------------------------------------

    def __contains__(self, name: str) -> bool:

        return name in self._variables

    # -------------------------------------------------

    def __iter__(self):

        return iter(self._variables.values())

    # -------------------------------------------------

    def __repr__(self):

        return (
            f"StateDatabase("
            f"variables={len(self._variables)})"
        )