"""Read and save the desktop custom configuration fields."""
import os
from math import isfinite
from tempfile import NamedTemporaryFile

import yaml

from state.tags import Tags

class InvalidConfiguration(ValueError):
    """The request contains unsupported settings."""


FIELDS = {
    "banks": ("pcs", "initial_condition", {
        "soc": (Tags.Battery.SOC, 0, 100),
        "soh": (Tags.Battery.SOH, 0, 100),
        "temperature_k": ("Initial_Temperature_K", 0, None),
    }),
    "transformers": ("transformers", "impedance", {
        "r_pu": ("r_pu", 0, 10),
        "x_pu": ("x_pu", 0, 10),
    }),
}


def _load(path):
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source)


def _save(path, config):
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as output:
            temporary = output.name
            yaml.safe_dump(config, output, sort_keys=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def _view(config):
    result = {
        "grid_available": config["plant"]["utility"].get("available", True),
    }
    for section, (yaml_list, group, fields) in FIELDS.items():
        result[section] = {
            item["id"]: {
                name: item.get(group, {}).get(yaml_key)
                for name, (yaml_key, _, _) in fields.items()
            }
            for item in config.get(yaml_list, [])
        }
    return result


def read_configuration(path):
    return _view(_load(path))


def save_configuration(path, body):
    if not isinstance(body, dict) or not body or set(body) - FIELDS.keys():
        raise InvalidConfiguration("Send a banks or transformers object, or both")
    config = _load(path)
    for section, updates in body.items():
        yaml_list, group, fields = FIELDS[section]
        if not isinstance(updates, dict) or not updates:
            raise InvalidConfiguration(f"{section} must contain device IDs and their settings")
        items = {item["id"]: item for item in config.get(yaml_list, [])}
        for device_id, settings in updates.items():
            if device_id not in items:
                raise InvalidConfiguration(f"Unknown {section} ID: {device_id}")
            if not isinstance(settings, dict) or not settings or set(settings) - fields.keys():
                raise InvalidConfiguration(f"Invalid settings for {device_id}")
            target = items[device_id].setdefault(group, {})
            for name, value in settings.items():
                yaml_key, low, high = fields[name]
                if (
                    type(value) not in (int, float) or not isfinite(value)
                    or value < low or (high is not None and value > high)
                    or (name == "temperature_k" and value == 0)
                ):
                    raise InvalidConfiguration(f"Invalid value for {device_id}.{name}")
                target[yaml_key] = float(value)
    _save(path, config)
    return _view(config)


def save_grid_availability(path, available):
    config = _load(path)
    config["plant"]["utility"]["available"] = available
    _save(path, config)
