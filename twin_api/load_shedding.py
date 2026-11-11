"""Summarize reported shedding signals without changing network loads."""
from bisect import bisect_left
from datetime import datetime, timedelta
from math import isfinite

from common.constants import IST
from state.tags import Tags
from twin_api.event_history import SAMPLE_INTERVAL_SECONDS


GROUPS = {
    "ev": ("EV Charging", "non_critical", (Tags.Load.EV_STACK_POWER, Tags.Load.EV_STACK_POWER_2)),
    "chiller": ("Chiller", "semi_critical", (Tags.Load.CHILLERS_POWER, Tags.Load.CHILLERS_POWER_2)),
    "cooling_tower": ("Cooling Tower", "critical", (Tags.Load.COOLING_TOWER_POWER, Tags.Load.COOLING_TOWER_POWER_2)),
}


def _number(value):
    if type(value) in (int, float) and isfinite(value) and value >= 0:
        return value
    return None


def _signals(records, event_id, date=None):
    signals = {}
    if not isinstance(records, list):
        return []
    for entry in records:
        if not isinstance(entry, dict) or entry.get("event_id") != event_id:
            continue
        groups = entry.get("load_groups")
        reductions = entry.get("reduced_kw_by_group")
        if (
            not isinstance(groups, list) or not groups
            or any(not isinstance(group, str) or group not in GROUPS for group in groups)
            or len(set(groups)) != len(groups)
            or not isinstance(reductions, dict) or set(reductions) != set(groups)
            or any(_number(value) is None for value in reductions.values())
        ):
            continue
        try:
            raw_timestamp = entry["timestamp"]
            timestamp = datetime.fromisoformat(raw_timestamp)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=IST)
            timestamp = timestamp.astimezone(IST)
            if date is not None and timestamp.date().isoformat() != date:
                continue
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        signals.setdefault(timestamp, (raw_timestamp, groups, reductions))
    return sorted(signals.items())


def _total(values):
    values = list(values)
    return sum(values) if all(value is not None for value in values) else None


def build_campus_trend(records, samples, start, end):
    """Build a rolling chart using PPC history and reported shedding markers."""
    points = []
    cooling_tags = GROUPS["cooling_tower"][2]
    for timestamp, event_id, values in samples:
        battery = values.get(Tags.Battery.POWER)
        if type(battery) not in (int, float) or not isfinite(battery):
            battery = None
        points.append({
            "timestamp": timestamp.astimezone(IST).isoformat(),
            "event_id": event_id,
            "total_load_kw": _number(values.get(Tags.Network.LOAD_POWER)),
            "available_supply_kw": _total((
                battery,
                _number(values.get(Tags.Grid.IMPORT_POWER)),
                _number(values.get(Tags.SOLAR.PV_POWER)),
            )),
            "essential_load_kw": _total(_number(values.get(tag)) for tag in cooling_tags),
        })
    event_ids = {
        entry["event_id"] for entry in records
        if isinstance(entry, dict) and isinstance(entry.get("event_id"), str)
    } if isinstance(records, list) else set()
    markers = [
        {"event_id": event_id, "timestamp": instant.isoformat(), "load_groups": groups}
        for event_id in sorted(event_ids)
        for instant, (_, groups, reductions) in _signals(records, event_id)
        if start <= instant <= end and any(reductions.values())
    ]
    markers.sort(key=lambda marker: marker["timestamp"])
    return {"window_minutes": 30, "points": points, "shedding_markers": markers}


def _delta(before, after):
    return before - after if before is not None and after is not None else None


def _action(delta):
    if delta is None:
        return None
    return "shed" if delta > 0 else "keep_on"


def _pct(value, total):
    return 100 * value / total if value is not None and total else None


def _balance(sample, timestamp):
    values = sample.get("values", {}) if sample else {}
    groups = {
        group: _total(_number(values.get(tag)) for tag in tags)
        for group, (_, _, tags) in GROUPS.items()
    }
    return {"timestamp": timestamp, "total_kw": _total(groups.values()), "groups_kw": groups}


def _build_stages(signals, samples):
    times = [datetime.fromisoformat(sample["timestamp"]) for sample in samples]
    snapshots = []
    stages = []
    reported_totals = dict.fromkeys(GROUPS, 0)
    for index, (instant, (timestamp, groups, reported)) in enumerate(signals):
        sample_index = bisect_left(times, instant)
        cutoff = instant + timedelta(seconds=2 * SAMPLE_INTERVAL_SECONDS)
        if index + 1 < len(signals):
            cutoff = min(cutoff, signals[index + 1][0])
        sample = samples[sample_index] if sample_index < len(times) and times[sample_index] < cutoff else None
        after = _balance(sample, timestamp)
        before = snapshots[-1] if snapshots else _balance(None, None)
        changes = []
        for group in groups:
            previous_kw = before["groups_kw"][group]
            current_kw = after["groups_kw"][group]
            delta = _delta(previous_kw, current_kw)
            changes.append({
                "load_group": group, "action": _action(delta), "before_kw": previous_kw,
                "after_kw": current_kw, "reduced_kw": delta,
            })
        reported_totals.update(reported)
        snapshots.append(after)
        stages.append({
            "stage": index + 1, "timestamp": timestamp, "load_groups": groups,
            "reduced_kw_by_group": reported, "changes": changes,
            "reduced_kw": _total(change["reduced_kw"] for change in changes),
            "cumulative_reduced_kw": sum(reported_totals.values()),
        })
    return stages, snapshots, reported_totals


def build_dashboard(event_id, records, samples):
    """Use PPC readings captured after each shedding signal for the event."""
    date = datetime.now(IST).date().isoformat()
    signals = _signals(records, event_id, date) if event_id else []
    samples = sorted(samples, key=lambda sample: datetime.fromisoformat(sample["timestamp"]))
    stages, snapshots, reported = _build_stages(signals, samples)
    before = snapshots[-2] if len(snapshots) >= 2 else _balance(None, None)
    latest_sample = samples[-1] if samples else None
    after = snapshots[-1] if snapshots else _balance(
        latest_sample, latest_sample["timestamp"] if latest_sample else None
    )
    baseline = snapshots[0] if snapshots else after
    total_kw = baseline["total_kw"]
    retained_kw = after["total_kw"]
    reduction_kw = _delta(total_kw, retained_kw)
    shed_kw = None if reduction_kw is None else sum(
        baseline["groups_kw"][group] for group, kw in after["groups_kw"].items() if kw == 0
    )
    reduced_kw = _delta(reduction_kw, shed_kw)
    latest_delta = _delta(before["total_kw"], retained_kw)
    performed_at = {
        group: timestamp
        for _, (timestamp, _, reductions) in signals
        for group, reduction in reductions.items()
        if reduction > 0
    }
    return {
        "event_id": event_id,
        "date": date,
        "next_actions": [
            {
                "load_group": group, "label": f"Shed {name}",
                "checked": group in performed_at, "performed_at": performed_at.get(group),
            }
            for group, (name, _, _) in GROUPS.items()
        ],
        "priority_matrix": [
            {
                "load_group": group, "name": name, "priority": priority, "type": priority,
                "units": len(tags), "capacity_per_unit_kw": None,
                "capacity_kw": baseline["groups_kw"][group],
                "contracted_load_kw": baseline["groups_kw"][group],
                "min_retain_kw": after["groups_kw"][group],
                "min_retain_pct": _pct(after["groups_kw"][group], baseline["groups_kw"][group]),
                "current_kw": after["groups_kw"][group], "reported_reduction_kw": reported[group],
                "action": _action(_delta(baseline["groups_kw"][group], after["groups_kw"][group])),
            }
            for group, (name, priority, tags) in GROUPS.items()
        ],
        "outcome": {
            "total_load_kw": total_kw, "retained_kw": retained_kw,
            "reported_reduction_kw": sum(reported.values()), "reduced_kw": reduced_kw, "shed_kw": shed_kw,
            "retained_pct": _pct(retained_kw, total_kw),
            "reduced_pct": _pct(reduced_kw, total_kw), "shed_pct": _pct(shed_kw, total_kw),
            "feasibility": "unknown",
        },
        "stages": stages,
        "power_balance": {
            "before": before, "after": after, "reduction_kw": latest_delta,
            "reduction_pct": _pct(latest_delta, before["total_kw"]),
        },
    }
