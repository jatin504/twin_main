"""
History Storage Configuration Loader from JSON
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HistoryConfig:
    history_window_seconds: float = 3600.0
    save_interval_seconds: float = 5.0
    export_file_path: str = "data/history.json"
    target_devices: list[str] = field(default_factory=lambda: ["PPC"])
    enabled_tags: list[str] | None = None

    @property
    def history_max_samples(self) -> int:
        return max(1, int(self.history_window_seconds / 0.5))


DEFAULT_CONFIG_PATHS = [
    "configs/history_config.json",
    "history_config.json",
]


def load_history_config(config_path: str | Path | None = None) -> HistoryConfig:
    """
    Load history config from a JSON file.
    If no path is provided, checks standard paths (configs/history_config.json, history_config.json).
    Falls back to environment variables or defaults if file not found.
    """
    target_path = None
    if config_path:
        p = Path(config_path)
        if p.exists():
            target_path = p
    else:
        for p_str in DEFAULT_CONFIG_PATHS:
            p = Path(p_str)
            if p.exists():
                target_path = p
                break

    if target_path:
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return HistoryConfig(
                history_window_seconds=float(data.get("history_window_seconds", 3600.0)),
                save_interval_seconds=float(data.get("save_interval_seconds", 5.0)),
                export_file_path=str(data.get("export_file_path", "data/history.json")),
                target_devices=list(data.get("target_devices", ["PPC"])),
                enabled_tags=data.get("enabled_tags"),
            )
        except Exception as e:
            print(f"Warning: Failed to parse history config JSON from {target_path}: {e}")

    # Fallback to environment variables or defaults
    env_sec = float(os.getenv("HISTORY_WINDOW_SECONDS", "3600.0"))
    return HistoryConfig(history_window_seconds=env_sec)
