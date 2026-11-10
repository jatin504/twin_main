"""Capture the current day's PPC readings by dispatch event."""
import json
import logging
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from threading import Lock

from common.constants import IST
from twin_api.event_feasibility import CHECK_TAGS, EventFeasibility


SAMPLE_INTERVAL_SECONDS = 15
logger = logging.getLogger(__name__)


class EventHistory:
    """Persist event samples to daily JSON Lines files and cache today's samples."""

    def __init__(self, storage_dir: Path = Path("data/event_history")):
        self._storage_dir = storage_dir
        self._lock = Lock()
        self._day = None
        self._events = {}
        self._reports = {}
        self._active_event = None
        self._last_interval = None
        self._last_slot = None

    def _roll_day(self, today):
        if self._day != today:
            events = self._load_day(today)
            self._day = today
            self._events = events
            self._reports.clear()
            self._active_event = None
            self._last_interval = self._last_slot = None

    def _daily_file(self, day):
        return self._storage_dir / f"{day.isoformat()}.jsonl"

    def _load_day(self, day):
        path = self._daily_file(day)
        events = {}
        try:
            with path.open("rb") as source:
                for index, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                        event_id = item.pop("event_id")
                        timestamp = datetime.fromisoformat(item["timestamp"])
                        if not isinstance(event_id, str) or timestamp.tzinfo is None:
                            raise ValueError
                    except (ValueError, TypeError, KeyError, AttributeError):
                        logger.warning("Skipping invalid event history record in %s at line %s", path, index)
                        continue
                    events.setdefault(event_id, []).append(item)
        except FileNotFoundError:
            pass
        return events

    def _append_sample(self, event_id, sample):
        path = self._daily_file(self._day)
        line = json.dumps({"event_id": event_id, **sample}, allow_nan=False).encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab+") as target:
            target.seek(0, 2)
            if target.tell():
                target.seek(-1, 2)
                if target.read(1) != b"\n":
                    target.write(b"\n")
            target.write(line + b"\n")

    def record(self, run_id, schedule, ppc, voltage_profile):
        position = schedule.active_position()
        with self._lock:
            now = datetime.now(timezone.utc)
            slot = int(now.timestamp()) // SAMPLE_INTERVAL_SECONDS
            self._roll_day(now.astimezone(IST).date())
            if position is None:
                self._finish_active("completed")
                return
            event_id, interval_index, simulation_time, row = position
            interval = (run_id, event_id, interval_index)
            if self._active_event != event_id:
                self._finish_active("completed")
                self._reports[event_id] = EventFeasibility(schedule.event_window(interval_index))
                self._active_event = event_id
            save_history = self._last_interval != interval or self._last_slot != slot
            tags = ppc.snapshot(None if save_history else CHECK_TAGS)
            self._reports[event_id].record(tags, voltage_profile, row)
            if not save_history:
                return
            values = {}
            for name, tag in tags.items():
                value = tag["value"]
                values[name] = None if isinstance(value, float) and not isfinite(value) else value
            sample = {
                "timestamp": now.isoformat().replace("+00:00", "Z"),
                "simulation_time": simulation_time.isoformat(),
                "interval_index": interval_index,
                "run_id": run_id,
                "values": values,
            }
            try:
                self._append_sample(event_id, sample)
            except (OSError, ValueError, TypeError):
                logger.exception("Could not persist event history sample for %s", event_id)
            self._events.setdefault(event_id, []).append(sample)
            self._last_interval, self._last_slot = interval, slot

    def _finish_active(self, status):
        if self._active_event is not None:
            self._reports[self._active_event].status = status
            self._active_event = None

    def stop(self):
        with self._lock:
            self._finish_active("interrupted")

    def feasibility(self, event_id=None):
        """Read the selected event report, defaulting to the active event."""
        with self._lock:
            self._roll_day(datetime.now(IST).date())
            if event_id is None:
                event_id = self._active_event
            report = self._reports.get(event_id)
            return {"event_id": event_id, **report.response()} if report is not None else None

    def read(self, event_id=None):
        with self._lock:
            today = datetime.now(IST).date()
            self._roll_day(today)
            result = {"date": today.isoformat(), "device_id": "PPC",
                      "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS}
            if event_id is None:
                return {**result, "events": [
                    {"event_id": key, "sample_count": len(samples),
                     "first_timestamp": samples[0]["timestamp"],
                     "last_timestamp": samples[-1]["timestamp"]}
                    for key, samples in self._events.items()
                ]}
            samples = self._events.get(event_id, [])
            return {**result, "event_id": event_id, "samples": list(samples)}
