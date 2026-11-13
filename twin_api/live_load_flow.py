"""Read-only projections and rolling chart samples for Live Load Flow."""
from collections import deque
from datetime import datetime, timedelta
from math import isfinite
from threading import Lock

from common.constants import IST
from state.tags import Tags
from twin_api.dashboard import TRANSFORMER_LOADING_TAGS, _reading, transformer_loading
from twin_api.event_history import SAMPLE_INTERVAL_SECONDS


SOURCE_POWER_TAGS = {
    "grid_import_mw": Tags.Grid.IMPORT_POWER,
    "solar_pv_mw": Tags.SOLAR.PV_POWER,
    "battery_power_mw": Tags.Battery.POWER,
}
POWER_TAGS = {"campus_load_mw": Tags.Network.LOAD_POWER, **SOURCE_POWER_TAGS}
LOAD_TAGS = {
    "chillers_mw": Tags.Load.CHILLERS_POWER,
    "cooling_tower_mw": Tags.Load.COOLING_TOWER_POWER,
    "ev_stack_mw": Tags.Load.EV_STACK_POWER,
    "service_block_mw": Tags.Load.SERVICE_BLOCK_POWER,
}
FEEDER_CAPACITY_KW = {
    "ev_stack": 1500,
    "chillers": 500,
    "cooling_tower": 300,
}
LIVE_TAGS = set(POWER_TAGS.values()) | set(LOAD_TAGS.values()) | set(TRANSFORMER_LOADING_TAGS)
HISTORY_TAGS = set(POWER_TAGS.values()) | set(LOAD_TAGS.values()) | {Tags.Network.NETWORK_LOSSES}
WINDOW = timedelta(hours=24)


def _power(tags, fields):
    return {field: _reading(tags, tag, 1000) for field, tag in fields.items()}


def grid_bess_solar_history(day, samples):
    """Project saved PPC samples onto the three historical power series."""
    points = []
    for timestamp, values in samples:
        point = {"timestamp": timestamp.isoformat()}
        for field, tag in SOURCE_POWER_TAGS.items():
            value = values.get(tag)
            point[field] = value / 1000 if type(value) in (int, float) and isfinite(value) else None
        points.append(point)
    return {"date": day.isoformat(), "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
            "points": points}


def live_payload(status, tags, transformers):
    """Expose available PPC measurements and configured transformer ratings."""
    rows = transformer_loading(tags, transformers)["transformers"]
    feeders = _power(tags, LOAD_TAGS)
    for feeder, capacity_kw in FEEDER_CAPACITY_KW.items():
        capacity_mw = capacity_kw / 1000
        load_mw = feeders[f"{feeder}_mw"]
        feeders[f"{feeder}_capacity_mw"] = capacity_mw
        feeders[f"{feeder}_loading_pct"] = (
            100 * load_mw / capacity_mw if load_mw is not None else None
        )
    return {
        "status": status,
        "power_balance": _power(tags, POWER_TAGS),
        "feeder_loading": feeders,
        "transformers": rows,
    }


def _grid_power_factor(apparent_power):
    magnitude = abs(apparent_power)
    if isfinite(magnitude) and magnitude > 0:
        return float(abs(apparent_power.real) / magnitude)
    return None


class LoadFlowHistory:
    """Keep one post-network sample per interval for the preceding 24 hours."""

    def __init__(self):
        self._lock = Lock()
        self._samples = deque(maxlen=int(WINDOW.total_seconds()) // SAMPLE_INTERVAL_SECONDS + 1)
        self._last_slot = None

    def record(self, ppc, run_id, grid_power):
        """Capture current readings once per interval on the simulation thread."""
        now = datetime.now(IST)
        slot = int(now.timestamp()) // SAMPLE_INTERVAL_SECONDS
        if self._last_slot == (run_id, slot):
            return
        tags = ppc.snapshot(HISTORY_TAGS)
        point = {
            "timestamp": now.isoformat(),
            "run_id": run_id,
            **_power(tags, POWER_TAGS),
            "system_loss_mw": _reading(tags, Tags.Network.NETWORK_LOSSES, 1000),
            "modeled_loads": _power(tags, LOAD_TAGS),
            "system_power_factor": _grid_power_factor(grid_power()),
        }
        with self._lock:
            self._samples.append((now, point))
            self._last_slot = (run_id, slot)

    def read(self):
        """Return the retained samples, leaving unsampled periods empty."""
        with self._lock:
            end = datetime.now(IST)
            start = end - WINDOW
            points = [point for instant, point in self._samples if start <= instant <= end]
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
            "power_factor_measurement_point": "GRID_33KV",
            "points": points,
        }
