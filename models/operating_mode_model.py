
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from models.state_machine import PCSState

from state.tags import Tags


class OperatingModeModel(BaseSimulationModel):

    def update(self, dt):

        state = PCSState(
            self.db.value(
                Tags.PCS.STATE
            )
        )

        mode = OperatingMode.OFF

        if state == PCSState.READY:

            mode = OperatingMode.STANDBY

        elif state == PCSState.GRID_FOLLOWING:

            mode = OperatingMode.GRID_FOLLOWING

        elif state == PCSState.GRID_FORMING:

            mode = OperatingMode.GRID_FORMING

        self.db.set(
            Tags.PCS.OPERATING_MODE,
            mode,
        )