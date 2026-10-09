from models.base import BaseSimulationModel
from state.tags import Tags


class NetworkModel(BaseSimulationModel):

    def initialize(self):

        #
        # Temporary fixed load
        #
        # self.db.set(
        #     Tags.Network.LOAD_POWER,
        #     2000.0,
        # )

        pass

    def update(self, dt):

        generation = self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

        load = self.db.value(
            Tags.Network.LOAD_POWER
        )

        imbalance = generation - load

        self.db.set(
            Tags.Network.GENERATION_POWER,
            generation,
        )

        self.db.set(
            Tags.Network.POWER_IMBALANCE,
            imbalance,
        )