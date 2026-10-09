from __future__ import annotations

from models.base import BaseSimulationModel
from state.tags import Tags


class BatteryModel(BaseSimulationModel):
    """
    Simple battery physics model.

    Phase-1:
        - SOC
        - Energy
        - Current
        - Power

    Future:
        - OCV curve
        - Internal resistance
        - Cell balancing
        - Temperature coupling
        - PyBaMM
    """

    def initialize(self):

        capacity = self.db.value(Tags.Battery.CAPACITY)
        soc = self.db.value(Tags.Battery.SOC)

        stored = capacity * soc / 100.0

        self.db.set(
            Tags.Battery.STORED_ENERGY,
            stored,
        )

        self.db.set(
            Tags.Battery.AVAILABLE_ENERGY,
            stored,
        )

    def update(self, dt: float):

        power = self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

        voltage = self.db.value(
            Tags.Battery.VOLTAGE
        )

        capacity = self.db.value(
            Tags.Battery.CAPACITY
        )

        stored = self.db.value(
            Tags.Battery.STORED_ENERGY
        )

        #
        # Battery power
        #
        self.db.set(
            Tags.Battery.POWER,
            power,
        )

        #
        # Battery current
        #
        if voltage > 1:

            current = (power * 1000.0) / voltage

        else:

            current = 0.0

        self.db.set(
            Tags.Battery.CURRENT,
            current,
        )

        #
        # Energy integration
        #
        delta_energy = power * dt / 3600.0

        stored -= delta_energy

        stored = max(
            0.0,
            min(stored, capacity),
        )

        self.db.set(
            Tags.Battery.STORED_ENERGY,
            stored,
        )

        self.db.set(
            Tags.Battery.AVAILABLE_ENERGY,
            stored,
        )

        soc = stored / capacity * 100.0

        self.db.set(
            Tags.Battery.SOC,
            soc,
        )

        # print(
        #     f"SOC = {self.db.value(Tags.Battery.SOC):.2f}%"
        # )

        # print(
        #     f"Energy = {self.db.value(Tags.Battery.STORED_ENERGY):.2f} kWh"
        # )

        # print(
        #     f"Current = {self.db.value(Tags.Battery.CURRENT):.1f} A"
        # )