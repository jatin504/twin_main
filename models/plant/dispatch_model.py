from models.base import BaseSimulationModel

from models.plant.equal_dispatch import EqualDispatchStrategy


class DispatchModel(BaseSimulationModel):

    def __init__(self, context):

        super().__init__(context)

        self.strategy = EqualDispatchStrategy()

    def update(self, dt):

        pcs = list(
            self.context.simulator.available_pcs()
        )

        self.strategy.dispatch(
            self.context,
            pcs,
        )