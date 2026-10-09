from network.elements.base import ElectricalElement
from state.tags import Tags


class UtilitySource(ElectricalElement):

    def __init__(

        self,

        db,

        bus,

    ):

        self.db = db

        self.bus = bus

    def update(self, backend):

        if not self.db.value(
            Tags.Grid.AVAILABLE
        ):

            return

        backend.set_voltage_source(

            name=self.bus,

            voltage=self.db.value(
                Tags.Grid.VOLTAGE
            ),

            frequency=self.db.value(
                Tags.Grid.FREQUENCY
            ),

            angle=self.db.value(
                Tags.Grid.PHASE_ANGLE
            ),
        )