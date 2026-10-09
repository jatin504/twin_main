class DeviceContext:

    """
    Runtime context of one simulated device.

    Every model receives this object instead of individual
    dependencies.

    The context may grow over time without changing every
    model constructor.
    """

    def __init__(
        self,
        device_id: str,
        simulator,
        database,
        command,
        plant_database,
        command_manager,
        register_bank=None,
        network=None,
    ):

        self.id = device_id

        self.simulator = simulator

        self.database = database

        self.plant_database = plant_database

        self.command = command

        self.command_manager = command_manager

        self.register_bank = register_bank

        self.network = network

    # @property
    # def database(self):
    #     return self._database

    # @property
    # def command_manager(self):
    #     return self._command_manager