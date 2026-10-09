from network.elements.base import ElectricalElement
from state.tags import Tags


class GridFollowingPCS(ElectricalElement):

    def __init__(

        self,

        db,

        bus,

    ):

        self.db = db

        self.bus = bus

    def update(self, backend):

        backend.set_generator(

            self.bus,

            self.db.value(
                Tags.PCS.ACTIVE_POWER_OUTPUT
            ),

            self.db.value(
                Tags.PCS.REACTIVE_POWER_OUTPUT
            ),
        )