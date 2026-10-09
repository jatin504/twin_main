from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class GridFormingReferenceModel(BaseSimulationModel):

    def update(self, dt):

        if self.db.value(
            Tags.PCS.OPERATING_MODE
        ) != OperatingMode.GRID_FORMING:

            return

        #
        # Battery ready?
        #
        if not self.db.value(Tags.BMS.READY):

            self.db.set(
                Tags.PCS.ACTIVE_POWER_REFERENCE,
                0.0,
            )
            return

        command = self.db.value(
            Tags.EMS.ACTIVE_POWER_COMMAND
        )

        self.db.set(
            Tags.PCS.ACTIVE_POWER_REFERENCE,
            command,
        )