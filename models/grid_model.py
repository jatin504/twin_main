from models.base import BaseSimulationModel

from models.operating_mode import OperatingMode

from state.tags import Tags


class GridModel(BaseSimulationModel):

    NOMINAL_FREQUENCY = 50.0

    NOMINAL_VOLTAGE = 690.0

    def update(self, dt):

        mode = self.db.value(
            Tags.PCS.OPERATING_MODE
        )

        #
        # Grid Following
        #
        if mode == OperatingMode.GRID_FOLLOWING:

            self.db.set(
                Tags.Grid.FREQUENCY,
                self.NOMINAL_FREQUENCY,
            )

            self.db.set(
                Tags.Grid.VOLTAGE,
                self.NOMINAL_VOLTAGE,
            )

            return

        #
        # Grid Forming
        #
        if mode == OperatingMode.GRID_FORMING:

            self.db.set(
                Tags.Grid.FREQUENCY,
                self.NOMINAL_FREQUENCY,
            )

            self.db.set(
                Tags.Grid.VOLTAGE,
                self.NOMINAL_VOLTAGE,
            )