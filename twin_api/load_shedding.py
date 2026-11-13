"""Summarize reported shedding signals without changing network loads."""
from bisect import bisect_left
from datetime import datetime, timedelta
from math import isfinite
from numbers import Real
import sys

from common.constants import IST
from state.tags import Tags
from twin_api.event_history import SAMPLE_INTERVAL_SECONDS

def parse_timestamp(value: str) -> datetime:
    if isinstance(value, str) and value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)

GROUPS = {
    "ev": ("EV Charging", "non_critical", (Tags.Load.EV_STACK_POWER, Tags.Load.EV_STACK_POWER_2)),
    "chiller": ("Chiller", "semi_critical", (Tags.Load.CHILLERS_POWER, Tags.Load.CHILLERS_POWER_2)),
    "cooling_tower": ("Cooling Tower", "critical", (Tags.Load.COOLING_TOWER_POWER, Tags.Load.COOLING_TOWER_POWER_2)),
}

def _number(value):
    if isinstance(value, Real) and not isinstance(value, bool) and isfinite(value) and value >= 0:
        return float(value)
    return None

def _total(values):
    valid = [v for v in values if v is not None]
    return sum(valid) if valid else None

def _action(before_kw, after_kw):
    if before_kw is None or after_kw is None:
        return None
    delta = before_kw - after_kw
    if delta == 0:
        return "keep_on"
    elif after_kw == 0:
        return "shed"
    else:
        return "reduce"

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
            timestamp = parse_timestamp(raw_timestamp)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=IST)
            timestamp = timestamp.astimezone(IST)
            if date is not None and timestamp.date().isoformat() != date:
                continue
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        signals.setdefault(timestamp, (raw_timestamp, groups, reductions))
    return sorted(signals.items())


def build_campus_trend(records, samples, start, end):
    """Build a rolling chart using PPC history and reported shedding markers."""
    points = []
    cooling_tags = GROUPS["cooling_tower"][2]
    for i, (timestamp, event_id, values) in enumerate(samples):
        battery = _number(values.get(Tags.Battery.POWER))
        grid = _number(values.get(Tags.Grid.IMPORT_POWER))
        solar = _number(values.get(Tags.SOLAR.PV_POWER))

        available_supply = _total((battery, grid, solar))

        if i < 3:
            print(
                f"[DEBUG][build_campus_trend] Sample {i} available_supply calculation: Battery({battery}) + Grid({grid}) + Solar({solar}) = {available_supply}",
                file=sys.stderr)

        points.append({
            "timestamp": timestamp.astimezone(IST).isoformat(),
            "event_id": event_id,
            "total_load_kw": _number(values.get(Tags.Network.LOAD_POWER)),
            "available_supply_kw": available_supply,
            "essential_load_kw": _total(_number(values.get(tag)) for tag in cooling_tags),
            "loads_kw": {
                group: _total(_number(values.get(tag)) for tag in tags)
                for group, (_, _, tags) in GROUPS.items()
            },
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

def _pct(value, total):
    return 100 * value / total if value is not None and total else None

def _balance(sample, timestamp):
    if sample is None:
        values = {}
        ts_str = None
    else:
        values = sample.get("values", sample)
        if isinstance(timestamp, datetime):
            ts_str = timestamp.isoformat()
        else:
            ts_str = str(timestamp) if timestamp else None
        
    groups = {}
    for group, (_, _, tags) in GROUPS.items():
        raw_vals = [values.get(tag) for tag in tags]
        parsed_vals = [_number(v) for v in raw_vals]
        groups[group] = _total(parsed_vals)
        
    total = _total(groups.values())
    return {"timestamp": ts_str, "total_kw": total, "groups_kw": groups}

def _build_stages(signals, samples):
    times = []
    for sample in samples:
        t = parse_timestamp(sample["timestamp"])
        if t.tzinfo is None:
            t = t.replace(tzinfo=IST)
        times.append(t.astimezone(IST))
        
    initial_before = _balance(None, None)
    best_before_idx_global = None
    if signals and times:
        first_instant = signals[0][0]
        idx = bisect_left(times, first_instant)
        best_before_idx_global = idx - 1 if idx > 0 else 0
        initial_before = _balance(samples[best_before_idx_global], times[best_before_idx_global])

    snapshots = []
    stages = []
    reported_totals = dict.fromkeys(GROUPS, 0)
    
    for index, (instant, (timestamp, groups, reported)) in enumerate(signals):
        idx = bisect_left(times, instant)
        
        best_after_idx = None
        min_diff_after = None
        next_instant = signals[index + 1][0] if index + 1 < len(signals) else None
        
        for i in range(idx, len(times)):
            if next_instant is not None and times[i] >= next_instant:
                break
            diff = abs((times[i] - instant).total_seconds())
            if min_diff_after is None or diff < min_diff_after:
                min_diff_after = diff
                best_after_idx = i
        
        is_estimated = (best_after_idx is None) or (best_before_idx_global is not None and best_after_idx <= best_before_idx_global)
        
        before = snapshots[-1] if snapshots else initial_before
        
        actual_after = None
        if not is_estimated and best_after_idx is not None:
            sample_after = samples[best_after_idx]
            actual_after = _balance(sample_after, timestamp)

        use_estimated = is_estimated
        if not use_estimated and actual_after is not None:
            for group in groups:
                before_val = before["groups_kw"].get(group)
                after_val = actual_after["groups_kw"].get(group)
                reduction = reported.get(group, 0)
                
                if before_val is not None and reduction is not None and reduction > 0:
                    if after_val is None or after_val >= before_val:
                        use_estimated = True
                        break

        if use_estimated:
            estimated_groups = dict(before["groups_kw"])
            for group in groups:
                before_val = estimated_groups.get(group)
                reduction = reported.get(group, 0)
                if before_val is not None and reduction is not None:
                    estimated_groups[group] = max(0.0, float(before_val) - float(reduction))
                elif reduction is not None:
                    estimated_groups[group] = 0.0
            
            after = {
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                "total_kw": _total(estimated_groups.values()),
                "groups_kw": estimated_groups
            }
        else:
            after = actual_after
            
        changes = []
        for group in groups:
            previous_kw = before["groups_kw"].get(group)
            current_kw = after["groups_kw"].get(group)
            delta = _delta(previous_kw, current_kw)
            changes.append({
                "load_group": group, 
                "action": _action(previous_kw, current_kw), 
                "before_kw": previous_kw,
                "after_kw": current_kw, 
                "reduced_kw": delta,
            })
        reported_totals.update(reported)
        snapshots.append(after)
        stages.append({
            "stage": index + 1, "timestamp": timestamp, "load_groups": groups,
            "reduced_kw_by_group": reported, "changes": changes,
            "reduced_kw": _total(change["reduced_kw"] for change in changes),
            "cumulative_reduced_kw": sum(reported_totals.values()),
        })
    
    return stages, snapshots, reported_totals, initial_before

def build_dashboard(event_id, records, samples):
    """Use PPC readings captured after each shedding signal for the event."""
    date = datetime.now(IST).date().isoformat()
    signals = _signals(records, event_id, date) if event_id else []
    samples = sorted(samples, key=lambda sample: parse_timestamp(sample["timestamp"]))
    stages, snapshots, reported, initial_before = _build_stages(signals, samples)
    
    before = snapshots[-2] if len(snapshots) >= 2 else initial_before
    
    latest_sample = samples[-1] if samples else None
    after = snapshots[-1] if snapshots else _balance(
        latest_sample, latest_sample["timestamp"] if latest_sample else None
    )
    
    # FIX: baseline must be the state BEFORE any shedding occurred (initial_before)
    # Previously it was snapshots[0], which was the "after" state of the first stage.
    baseline = initial_before 
    
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
                "action": _action(baseline["groups_kw"][group], after["groups_kw"][group]),
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
