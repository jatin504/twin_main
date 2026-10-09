from network.elements.base import ElectricalElement
from state.tags import Tags


class PlantLoad(ElectricalElement):

    def __init__(

        self,

        db,

        bus,

    ):

        self.db = db

        self.bus = bus

    def update(self, backend):

        backend.set_load(

            self.bus,

            self.db.value(
                Tags.Load.ACTIVE_POWER
            ),

            self.db.value(
                Tags.Load.REACTIVE_POWER
            ),
        )