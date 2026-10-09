from state.tags import Tags


class NetworkAdapter:

    def __init__(
        self,
        database,
    ):

        self.db = database

    def generator_power(self):

        return self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

    def load_power(self):

        return self.db.value(
            Tags.Network.LOAD_POWER
        )