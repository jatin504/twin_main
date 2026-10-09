from common.enums import PCSState
from models.base import BaseSimulationModel
from state.tags import Tags


class SourceManager(BaseSimulationModel):

    def update(self, dt):

        state = PCSState(
            self.db.value(Tags.PCS.STATE)
        )

        #
        # Default
        #
        self.db.set(
            Tags.Grid.SOURCE,
            "UTILITY"
        )

        if state == PCSState.GRID_FORMING:

            self.db.set(
                Tags.Grid.SOURCE,
                "PCS"
            )