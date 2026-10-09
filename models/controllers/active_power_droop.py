from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class ActivePowerDroopController(BaseSimulationModel):

    def update(self, dt):

        if self.db.value(
            Tags.PCS.OPERATING_MODE
        ) != OperatingMode.GRID_FORMING:

            return

        if not self.db.value(
            Tags.GFM.DROOP_ENABLE
        ):

            return

        frequency = self.db.value(
            Tags.Grid.FREQUENCY
        )

        nominal = self.db.value(
            Tags.GFM.NOMINAL_FREQUENCY
        )

        gain = self.db.value(
            Tags.GFM.DROOP_GAIN
        )

        delta_f = nominal - frequency

        correction = gain * delta_f

        base = self.db.value(
            Tags.EMS.ACTIVE_POWER_COMMAND
        )

        reference = base + correction

        # self.db.set(
        #     Tags.PCS.ACTIVE_POWER_REFERENCE,
        #     reference,
        # )

        self.db.set(
            Tags.EMS.ACTIVE_POWER_COMMAND,
            reference,
        )