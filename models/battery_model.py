from models.base import BaseSimulationModel
from models.battery_backend.pybamm_backend import PyBaMMBackend


class BatteryModel(BaseSimulationModel):

    def __init__(self, context):

        super().__init__(context)

        self.backend = PyBaMMBackend(
            context,
        )

    def initialize(self):

        self.backend.initialize()

    def update(self, dt):

        self.backend.update(dt)