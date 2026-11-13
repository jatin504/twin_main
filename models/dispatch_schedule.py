"""Replay a dispatch plan against the headless simulator's clock."""
import json
from bisect import bisect_right
from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path
from threading import Lock

from common.constants import IST
from models.base import BaseSimulationModel
from state.tags import Tags


def _timestamp(value):
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=IST)


class DispatchPlan:
    """Read scheduled intervals and format their API representation."""

    def __init__(self, path: Path):
        with path.open(encoding="utf-8-sig") as source:
            plan = json.load(source)
        self.load_shedding_events = plan.get("load_shedding_events", [])
        self._rows = sorted(plan["schedule"], key=lambda row: _timestamp(row["time_stamp"]))
        if not self._rows:
            raise ValueError("Dispatch schedule has no intervals")
        self._starts = [_timestamp(row["time_stamp"]) for row in self._rows]
        if len(set(self._starts)) != len(self._starts):
            raise ValueError("Dispatch interval timestamps must be unique")
        self._end = self._starts[-1] + timedelta(minutes=15)
        self._outcomes = {
            _timestamp(decision["time_stamp"]): result
            for result in plan.get("results", [])
            if (decision := result.get("bess_event_decision", {})).get("time_stamp")
        }
        self._initial_time = self._select_start(plan)
        self.running_event_id = plan.get("running_event_id")
        self.running_timestamp = (
            _timestamp(plan["running_timestamp"]) if plan.get("running_timestamp") else None
        )

    def display_snapshot(self, elapsed_seconds):
        """Display the file's selected interval with a clock independent of the solver."""
        if not self.running_event_id and self.running_timestamp is None:
            return self._snapshot(None, None, waiting=True)
        index = bisect_right(self._starts, self._initial_time) - 1
        return self._snapshot(
            index, (self.running_timestamp or self._starts[index]) + timedelta(seconds=elapsed_seconds),
            elapsed_seconds=elapsed_seconds,
        )

    def display_position(self):
        """Return the event and interval selected by the dispatch file."""
        if not self.running_event_id and self.running_timestamp is None:
            return None
        index = bisect_right(self._starts, self._initial_time) - 1
        row = self._rows[index]
        event_id = row.get("event_id")
        if event_id:
            return event_id, index, self._initial_time, row
        return None

    def event_window(self, index):
        """Return the contiguous scheduled window containing this interval."""
        event_id = self._rows[index].get("event_id")
        first = last = index
        while first > 0 and self._rows[first - 1].get("event_id") == event_id:
            first -= 1
        while last + 1 < len(self._rows) and self._rows[last + 1].get("event_id") == event_id:
            last += 1
        end = self._starts[last + 1] if last + 1 < len(self._rows) else self._end
        return {"from": self._starts[first].isoformat(), "to": end.isoformat()}

    @property
    def display_start(self):
        index = bisect_right(self._starts, self._initial_time) - 1
        return self.running_timestamp or self._starts[index]

    def _select_start(self, plan):
        event_id = plan.get("running_event_id")
        timestamp = plan.get("running_timestamp")
        start = _timestamp(timestamp) if timestamp else None
        candidates = [
            candidate for row, candidate in zip(self._rows, self._starts)
            if not event_id or row.get("event_id") == event_id
        ]
        if not candidates:
            raise ValueError("Dispatch running event does not match the schedule")
        if start is None:
            return candidates[0]
        index = bisect_right(self._starts, start) - 1
        if index >= 0 and start < self._end and self._starts[index] in candidates:
            return start
        # The exported timestamp can point into a different event. Honor the
        # explicit event ID and resume from a row belonging to that event.
        return candidates[max(0, bisect_right(candidates, start) - 1)]

    def _row(self, index, active_index, waiting):
        row = self._rows[index]
        outcome = self._outcomes.get(self._starts[index], {})
        decision = outcome.get("bess_event_decision", {})
        actual = next(
            (step["battery_energy_mwh"] for step in reversed(outcome.get("strategy_result", []))
             if "battery_energy_mwh" in step),
            None,
        )
        passed = outcome.get("is_pass")
        status = "running" if index == active_index else (
            "pass" if passed is True else "fail" if passed is False else
            "completed" if not waiting and (active_index is None or index < active_index) else "upcoming"
        )
        return {
            **row,
            "status": status,
            "expected_energy_mwh": decision.get("battery_energy_mwh", row.get("battery_energy_mwh")),
            "actual_energy_mwh": actual,
            "is_pass": passed,
            "fault": outcome.get("fault"),
        }

    def _snapshot(self, index, timestamp, *, elapsed_seconds=None, waiting=False):
        rows = [self._row(i, index, waiting) for i in range(len(self._rows))]
        if index is None:
            return {"status": "waiting" if waiting else "completed",
                    "simulation_time": None if waiting else self._end.isoformat(),
                    "active_event": None, "current_interval": None, "rows": rows}
        start = self._starts[index]
        end = self._starts[index + 1] if index + 1 < len(rows) else self._end
        duration = (end - start).total_seconds()
        if elapsed_seconds is None:
            elapsed_seconds = (timestamp - start).total_seconds()
        else:
            duration = 900
        return {
            "status": "running",
            "simulation_time": timestamp.isoformat(),
            "active_event": {"event_id": rows[index].get("event_id")},
            "current_interval": {
                **rows[index],
                "index": index,
                "elapsed_seconds": elapsed_seconds,
                "remaining_seconds": duration - elapsed_seconds,
            },
            "rows": rows,
        }


class DispatchSchedule(DispatchPlan, BaseSimulationModel):
    """Replay dispatch inputs on the simulation clock."""

    def __init__(self, context, path: Path):
        BaseSimulationModel.__init__(self, context)
        DispatchPlan.__init__(self, path)
        self._clock = self._initial_time
        self._lock = Lock()
        self._index = None
        self._published_time = None
        self._powers = [
            (self._power(row, "load_kw"), self._power(row, "pv_kw"))
            for row in self._rows
        ]

    @staticmethod
    def _power(row, key):
        value = float(row.get(key, 0))
        if not isfinite(value) or value < 0:
            raise ValueError(f"Invalid dispatch {key} at {row['time_stamp']}")
        return value

    def initialize(self):
        with self._lock:
            self._clock = self._initial_time
            self._apply_interval()

    def update(self, dt):
        with self._lock:
            self._apply_interval()
            if self._index is not None:
                self._clock += timedelta(seconds=dt)

    def _apply_interval(self):
        if self._clock >= self._end:
            self._index = None
            return
        self._index = bisect_right(self._starts, self._clock) - 1
        load_kw, pv_kw = self._powers[self._index]
        # self.db.set(Tags.Network.LOAD_POWER, load_kw)
        # self.db.set(Tags.SOLAR.PV_POWER, pv_kw)
        self._published_time = self._clock

    def active_position(self):
        """Return the current event, its interval index and simulation time."""
        with self._lock:
            if self._index is None:
                return None
            event_id = self._rows[self._index].get("event_id")
            if not event_id:
                return None
            return event_id, self._index, self._published_time, self._rows[self._index]

    def snapshot(self):
        """Return the applied interval, its clock, and the plan rows."""
        with self._lock:
            return self._snapshot(self._index, self._published_time)
