from network.pydgrid_backend import PyDGridBackend


class NetworkFactory:

    @staticmethod
    def create(config):

        solver = config.network.solver.lower()

        if solver == "pydgrid":

            return PyDGridBackend()

        raise ValueError(
            f"Unknown solver: {solver}"
        )