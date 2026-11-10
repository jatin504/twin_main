"""File-driven schedule clock for the dashboard."""
import logging
from datetime import datetime
from pathlib import Path
from time import monotonic

from common.constants import IST
from models.dispatch_schedule import DispatchPlan

logger = logging.getLogger(__name__)


class DispatchView:
    """Reload the schedule when its input file changes, independently of Twin runs."""

    def __init__(self):
        self._source = None
        self._revision = None
        self._plan = None
        self._observed_at = None

    def snapshot(self, path):
        if path != self._source:
            self._source = path
            self._revision = self._plan = self._observed_at = None
        if not path:
            return self._empty()

        source = Path(path)
        try:
            stat = source.stat()
            revision = (stat.st_mtime_ns, stat.st_size)
            if revision != self._revision:
                plan = DispatchPlan(source)
                previous = self._plan
                if (
                    previous is None
                    or plan.running_event_id != previous.running_event_id
                    or plan.display_start != previous.display_start
                ):
                    self._observed_at = monotonic()
                self._plan = plan
                self._revision = revision
        except FileNotFoundError:
            self._revision = self._plan = self._observed_at = None
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            logger.warning("Could not read dispatch schedule from %s", source, exc_info=True)

        if self._plan is None:
            return self._empty()
        start = self._plan.display_start.astimezone(IST)
        now = datetime.now(IST)
        elapsed = (now - start).total_seconds() if start.date() == now.date() else (
            monotonic() - self._observed_at
        )
        return self._plan.display_snapshot(min(900, max(0, int(elapsed))))

    @staticmethod
    def _empty():
        return {"status": "no_schedule", "simulation_time": None, "active_event": None,
                "current_interval": None, "rows": []}
