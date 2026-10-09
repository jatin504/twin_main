from __future__ import annotations

from models.base import BaseSimulationModel
from models.pv.state import PVInverter
from state.tags import Tags

import random

class PVModel(BaseSimulationModel):
    """
    Simple PV physics model.

    Phase-1:
        - SOC
        - Energy
        - Current
        - Power
    """

    def initialize(self):

        self.pv_state = PVInverter()

    def update(self, dt: float):

        # irradiance = 0 to 1000 W/m²

        self.active_power = self.pv_state.rated_power * 850 / 1000

        self.dc_current = self.active_power / self.pv_state.dc_voltage

        self.ac_current = self.active_power * 1000 / (1.732 * 415)

        self.energy_today += self.active_power / 3600


        self.ac_voltage = 415 + random.uniform(-2, 2)

        self.frequency = 50 + random.uniform(-0.02, 0.02)

        self.temperature += random.uniform(-0.05, 0.05)


    def start(self):
        self.status = "Running"

    def stop(self):
        self.status = "Stopped"
        self.active_power = 0

    def set_power_limit(self, percent):
        self.power_limit = percent

    def trip(self):

        self.status = "Fault"

        self.active_power = 0

        self.alarm = 101