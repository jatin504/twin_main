"""Build legacy snapshot widget data from the live PPC tags."""
from math import isfinite

from state.quality import Quality
from state.tags import Tags


TRANSFORMER_LOADING_TAGS = (
    Tags.Transformer.T1_LOADING,
    Tags.Transformer.T2_LOADING,
    Tags.Transformer.T3_LOADING,
)


def _reading(tags, name, divisor=1):
    tag = tags.get(name, {})
    value = tag.get("value")
    if tag.get("quality") == Quality.GOOD.name and isinstance(value, (int, float)) and isfinite(value):
        return value / divisor
    return None


def feeder_load(tags):
    """Return feeder power in MW, with network losses reported separately."""
    chillers = _reading(tags, Tags.Load.CHILLERS_POWER, 1000)
    cooling_tower = _reading(tags, Tags.Load.COOLING_TOWER_POWER, 1000)
    return {
        "total_load_mw": _reading(tags, Tags.Network.LOAD_POWER, 1000),
        "hvac_cooling_mw": (
            chillers + cooling_tower if chillers is not None and cooling_tower is not None else None
        ),
        "ev_charging_mw": _reading(tags, Tags.Load.EV_STACK_POWER, 1000),
        "service_block_mw": _reading(tags, Tags.Load.SERVICE_BLOCK_POWER, 1000),
        "losses_mw": _reading(tags, Tags.Network.NETWORK_LOSSES, 1000),
    }


def transformer_loading(tags, transformers):
    """Weight each transformer's loading by its configured apparent-power rating."""
    rows = []
    for index, transformer in enumerate(transformers):
        loading = None
        if index < len(TRANSFORMER_LOADING_TAGS):
            loading = _reading(tags, TRANSFORMER_LOADING_TAGS[index])
        rows.append({
            "id": transformer["id"],
            "rated_capacity_mva": transformer["rating_kva"] / 1000,
            "loading_pct": loading,
        })

    capacity = sum(row["rated_capacity_mva"] for row in rows)
    combined = None
    if capacity > 0 and all(row["loading_pct"] is not None for row in rows):
        combined = sum(row["loading_pct"] * row["rated_capacity_mva"] for row in rows) / capacity
    return {
        "transformers": rows,
        "rated_capacity_mva": capacity,
        "combined_loading_pct": combined,
        "total_load_mw": _reading(tags, Tags.Network.LOAD_POWER, 1000),
    }
