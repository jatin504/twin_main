"""
Simulation clock.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SimulationClock:

    dt: float

    time_sec: float = 0.0

    cycle: int = 0

    running: bool = False

    def start(self):

        self.running = True

    def stop(self):

        self.running = False

    def reset(self):

        self.time_sec = 0.0

        self.cycle = 0

    def tick(self):

        if not self.running:
            return

        self.time_sec += self.dt

        self.cycle += 1