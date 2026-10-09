from network.elements.base import ElectricalElement


class GridFormingPCS(ElectricalElement):

    def update(self, backend):

        backend.inject_voltage_source(

            self.bus,

            self.voltage,

            self.frequency,

            self.angle,

        )