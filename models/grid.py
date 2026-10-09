from common.constants import (
    DEFAULT_GRID_AVAILABLE,
    DEFAULT_GRID_FREQUENCY,
    DEFAULT_GRID_VOLTAGE,
)

from models.base import BaseSimulationModel

from models.operating_mode import OperatingMode

from state.tags import Tags


class GridModel(BaseSimulationModel):

    NOMINAL_VOLTAGE = DEFAULT_GRID_VOLTAGE
    NOMINAL_FREQUENCY = DEFAULT_GRID_FREQUENCY

    #
    # Simple island dynamics
    #
    INERTIA = 50000.0

    DAMPING = 0.05

    def __init__(self, database):

        super().__init__(database)

        self.phase = 0.0

        self.previous_frequency = self.NOMINAL_FREQUENCY

    def initialize(self):

        self.db.set(
            Tags.Grid.AVAILABLE,
            DEFAULT_GRID_AVAILABLE,
        )

        self.db.set(
            Tags.Grid.VOLTAGE,
            self.NOMINAL_VOLTAGE,
        )

        self.db.set(
            Tags.Grid.FREQUENCY,
            self.NOMINAL_FREQUENCY,
        )

        self.db.set(
            Tags.Grid.ROCOF,
            0.0,
        )

        self.db.set(
            Tags.Grid.PHASE_ANGLE,
            0.0,
        )

    def update(self, dt):

        mode = OperatingMode(
            self.db.value(
                Tags.PCS.OPERATING_MODE
            )
        )

        if mode == OperatingMode.GRID_FOLLOWING:

            self.update_infinite_bus(dt)

        elif mode == OperatingMode.GRID_FORMING:

            self.update_island_bus(dt)

        else:

            self.update_dead_bus(dt)

    def update_infinite_bus(self, dt):

        # self.db.set(
        #     Tags.Grid.VOLTAGE,
        #     self.NOMINAL_VOLTAGE,
        # )

        # self.db.set(
        #     Tags.Grid.FREQUENCY,
        #     self.NOMINAL_FREQUENCY,
        # )

        self.update_phase(dt)

        self.update_rocof(dt)

    def update_dead_bus(self, dt):

        grid = self.db.value(
                Tags.Grid.AVAILABLE
            )

        if grid:
            # self.db.set(
            #     Tags.Grid.VOLTAGE,
            #     self.NOMINAL_VOLTAGE,
            # )

            self.db.set(
                Tags.Grid.FREQUENCY,
                self.NOMINAL_FREQUENCY,
            )

            self.db.set(
                Tags.Grid.ROCOF,
                0.0,
            )

        else:

            self.db.set(
                Tags.Grid.VOLTAGE,
                0.0,
            )

            self.db.set(
                Tags.Grid.FREQUENCY,
                0.0,
            )

            self.db.set(
                Tags.Grid.ROCOF,
                0.0,
            )

    def update_island_bus(self, dt):

        frequency = self.db.value(
            Tags.Grid.FREQUENCY
        )

        power = self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

        #
        # Placeholder dynamics.
        #
        error = self.db.value(
            Tags.Network.POWER_IMBALANCE
        )

        frequency += (
            error / self.INERTIA
        ) * dt

        frequency += (
            self.NOMINAL_FREQUENCY
            - frequency
        ) * self.DAMPING * dt

        # self.db.set(
        #     Tags.Grid.FREQUENCY,
        #     frequency,
        # )

        # self.db.set(
        #     Tags.Grid.VOLTAGE,
        #     self.NOMINAL_VOLTAGE,
        # )

        self.update_phase(dt)

        self.update_rocof(dt)

    def update_phase(self, dt):

        frequency = self.db.value(
            Tags.Grid.FREQUENCY
        )

        self.phase += frequency * 360.0 * dt

        self.phase %= 360.0

        self.db.set(
            Tags.Grid.PHASE_ANGLE,
            self.phase,
        )


    def update_rocof(self, dt):

        frequency = self.db.value(
            Tags.Grid.FREQUENCY
        )

        rocof = (
            frequency
            - self.previous_frequency
        ) / max(dt, 1e-6)

        self.db.set(
            Tags.Grid.ROCOF,
            rocof,
        )

        self.previous_frequency = frequency