from __future__ import annotations

import json
import os
from datetime import datetime

from state.database import StateDatabase
from common.constants import IST


class PlantDatabase:
    """
    Owns the engineering databases of every simulated device.

    This class is responsible only for managing device databases.
    It does not expose engineering variables directly.
    """

    def __init__(self):

        self._devices: dict[str, StateDatabase] = {}

    # -------------------------------------------------

    def add_device(
        self,
        device_id: str,
    ) -> StateDatabase:

        if device_id in self._devices:

            raise ValueError(
                f"Device '{device_id}' already exists."
            )

        database = StateDatabase()

        self._devices[device_id] = database

        return database

    # -------------------------------------------------

    def remove_device(
        self,
        device_id: str,
    ) -> None:

        self._devices.pop(device_id, None)

    # -------------------------------------------------

    def device(
        self,
        device_id: str,
    ) -> StateDatabase:

        try:

            return self._devices[device_id]

        except KeyError as ex:

            raise KeyError(
                f"Unknown device '{device_id}'."
            ) from ex

    # -------------------------------------------------

    def exists(
        self,
        device_id: str,
    ) -> bool:

        return device_id in self._devices

    # -------------------------------------------------

    def ids(self) -> list[str]:

        return list(self._devices.keys())

    # -------------------------------------------------

    def items(self):

        return self._devices.items()

    # -------------------------------------------------

    def record_history(
        self,
        device_ids: list[str] | str | None = None,
        timestamp: datetime | None = None,
    ) -> dict[str, dict]:
        """
        Record history for specified devices or all devices.
        If device_ids is None, records for all existing devices.
        """
        if isinstance(device_ids, str):
            target_ids = [device_ids]
        elif device_ids is not None:
            target_ids = list(device_ids)
        else:
            target_ids = list(self._devices.keys())

        recorded = {}
        for dev_id in target_ids:
            if dev_id in self._devices:
                dev_db = self._devices[dev_id]
                rec = dev_db.record_history(timestamp)
                if rec:
                    recorded[dev_id] = rec

        return recorded

    # -------------------------------------------------

    def get_history(
        self,
        device_id: str,
        tag_name: str | None = None,
        last_seconds: float | None = 3600.0,
    ) -> list[dict] | dict[str, list[dict]]:
        """
        Retrieve historical data for a specific device and tag.
        """
        if device_id not in self._devices:
            return [] if tag_name is not None else {}

        return self._devices[device_id].get_history(tag_name, last_seconds)

    # -------------------------------------------------

    def get_all_history(
        self,
        device_ids: list[str] | None = None,
        last_seconds: float | None = 3600.0,
    ) -> dict[str, dict[str, list[dict]]]:
        """
        Retrieve history across devices.
        """
        target_ids = device_ids if device_ids is not None else list(self._devices.keys())
        result = {}
        for dev_id in target_ids:
            if dev_id in self._devices:
                dev_hist = self._devices[dev_id].get_history(None, last_seconds)
                if dev_hist:
                    result[dev_id] = dev_hist
        return result

    # -------------------------------------------------

    def save_history_to_json(
        self,
        file_path: str = "data/history.json",
        device_ids: list[str] | None = None,
        last_seconds: float | None = 3600.0,
    ) -> str:
        """
        Export historical records to a JSON file (atomic write).
        """
        history_data = {
            "saved_at": datetime.now(IST).isoformat(),
            "window_seconds": last_seconds,
            "devices": self.get_all_history(device_ids, last_seconds),
        }

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        tmp_path = f"{file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)

        os.replace(tmp_path, file_path)
        return file_path

    # -------------------------------------------------

    def load_history_from_json(
        self,
        file_path: str = "data/history.json",
    ) -> dict:
        """
        Load historical records from a JSON file.
        """
        if not os.path.exists(file_path):
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------

    def enable_history(
        self,
        device_id: str,
        tag_name: str,
        enabled: bool = True,
    ) -> None:
        """
        Dynamically enable or disable history for a specific tag on a device.
        """
        if device_id in self._devices:
            self._devices[device_id].enable_history(tag_name, enabled)

    def set_history_window(
        self,
        window_sec: float,
        max_samples: int | None = None,
        device_ids: list[str] | None = None,
    ) -> None:
        """
        Configure history retention window (seconds) across devices.
        E.g. window_sec=900 for 15 minutes, 1800 for 30 minutes, 3600 for 1 hour.
        """
        target_ids = device_ids if device_ids is not None else list(self._devices.keys())
        for dev_id in target_ids:
            if dev_id in self._devices:
                self._devices[dev_id].set_history_window(window_sec, max_samples)

    # -------------------------------------------------

    def clear(self):

        self._devices.clear()

    # -------------------------------------------------

    def __contains__(self, device_id):

        return device_id in self._devices

    # -------------------------------------------------

    def __len__(self):

        return len(self._devices)

    # -------------------------------------------------

    def __repr__(self):

        return (
            f"PlantDatabase("
            f"devices={len(self)})"
        )