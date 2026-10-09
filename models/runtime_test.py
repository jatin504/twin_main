from models.base import BaseSimulationModel


class RuntimeTestModel(BaseSimulationModel):

    def __init__(self, database):

        super().__init__(database)

        self.counter = 0

    def initialize(self):

        print("Runtime initialized")

    def update(self, dt):

        self.counter += 1

        print(
            f"Cycle={self.counter} "
            f"dt={dt:.3f}s"
        )