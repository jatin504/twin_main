"""Evaluate the available operating limits during dispatch replay."""
from math import isfinite

from state.quality import Quality
from state.tags import Tags


TRANSFORMER_TAGS = {
    Tags.Transformer.T1_LOADING: "T1",
    Tags.Transformer.T2_LOADING: "T2",
    Tags.Transformer.T3_LOADING: "T3",
}
CHECK_TAGS = {*TRANSFORMER_TAGS, Tags.Grid.FREQUENCY, Tags.Grid.IMPORT_POWER}


def _number(value):
    return float(value) if isinstance(value, (int, float)) and isfinite(value) else None


def _reading(tags, name):
    tag = tags.get(name, {})
    return _number(tag.get("value")) if tag.get("quality") == Quality.GOOD.name else None


def _check(values, lower, upper, unit):
    valid = [value for value in values if value is not None]
    low, high = (min(valid), max(valid)) if valid else (None, None)
    if valid and ((lower is not None and low < lower) or high > upper):
        status = "fail"
    elif not valid or len(valid) < len(values):
        status = "unavailable"
    else:
        status = "pass"
    return {"status": status, "min": low, "max": high, "unit": unit,
            "limits": {"min": lower, "max": upper}}


class EventFeasibility:
    """Keep the latest checks and an incremental summary for one event run."""

    def __init__(self, window):
        self.window = window
        self.status = "running"
        self.latest = {}
        self.summary = {}

    def record(self, tags, profile, interval):
        limit = _number(interval.get("grid_import_limit_kw"))
        grid = _reading(tags, Tags.Grid.IMPORT_POWER)
        transformer_loadings = {
            transformer: _reading(tags, tag)
            for tag, transformer in TRANSFORMER_TAGS.items()
        }
        transformer_check = _check(transformer_loadings.values(), 0, 100, "%")
        transformer_check["transformer_id"] = next(
            (name for name, value in transformer_loadings.items()
             if value is not None and value == transformer_check["max"]),
            None,
        )
        self.latest = {
            "voltage": _check([_number(value) for value in profile.values()], .95, 1.05, "p.u."),
            "frequency": _check([_reading(tags, Tags.Grid.FREQUENCY)], 48, 52, "Hz"),
            "transformer_loading": transformer_check,
            "grid_import": (
                _check([grid], None, limit, "kW") if limit is not None and limit >= 0
                else {"status": "unavailable", "min": grid, "max": grid, "unit": "kW",
                      "limits": {"min": None, "max": None}}
            ),
        }
        for name, check in self.latest.items():
            summary = self.summary.setdefault(name, {
                "unit": check["unit"], "min": None, "max": None,
                "failed_samples": 0, "unavailable_samples": 0,
            })
            summary["failed_samples"] += check["status"] == "fail"
            summary["unavailable_samples"] += check["status"] == "unavailable"
            if name != "grid_import":
                summary["limits"] = check["limits"]
            if name == "transformer_loading" and check["max"] is not None and (
                summary["max"] is None or check["max"] > summary["max"]
            ):
                summary["transformer_id"] = check["transformer_id"]
            for key, combine in (("min", min), ("max", max)):
                value = check[key]
                if value is not None:
                    summary[key] = value if summary[key] is None else combine(summary[key], value)

    def response(self):
        running = self.status == "running"
        readings = self.latest if running else self.summary
        checks = {}
        for name, reading in readings.items():
            if running:
                status = reading["status"]
            elif reading["failed_samples"]:
                status = "fail"
            else:
                status = "unavailable" if reading["unavailable_samples"] else "pass"
            if status == "unavailable":
                continue

            check = {"status": status, "unit": reading["unit"]}
            if name == "transformer_loading":
                check["transformer_id"] = reading["transformer_id"]
            if "limits" in reading:
                check["limits"] = reading["limits"]
            if running and name in {"frequency", "grid_import"}:
                check["value"] = reading["max"]
            elif running and name == "transformer_loading":
                check["max"] = reading["max"]
            else:
                check.update(min=reading["min"], max=reading["max"])
            if not running and status == "fail":
                check["failed_samples"] = reading["failed_samples"]
            checks[name] = check

        # statuses = {check["status"] for check in checks.values()}
        # result = "fail" if "fail" in statuses else (
        #     "partial_pass" if checks and len(checks) == len(readings) else "insufficient_data"
        # )
        # return {
        #     "event_status": self.status,
        #     "window": self.window,
        #     "result": result,
        #     "display_status": "In Process" if running and result == "partial_pass" else {
        #         "partial_pass": "Partial Pass",
        #         "insufficient_data": "Insufficient Data",
        #         "fail": "Fail",
        #     }[result],
        #     "checks": checks,
        # }
        if running:
            statuses = {check["status"] for check in checks.values()}
            result = "fail" if "fail" in statuses else (
                "partial_pass" if checks and len(checks) == len(readings) else "insufficient_data"
            )
        else:
            transformer = self.summary.get("transformer_loading", {})
            peak = transformer.get("max")
            if peak is None:
                result = "insufficient_data"
            elif peak > transformer["limits"]["max"]:
                result = "fail"
            else:
                result = "pass"

        return {
            "event_status": self.status,
            "window": self.window,
            "result": result,
            "display_status": "In Process" if running and result == "partial_pass" else {
                "pass": "Pass",
                "partial_pass": "Partial Pass",
                "insufficient_data": "Insufficient Data",
                "fail": "Fail",
            }[result],
            "checks": checks,
        }