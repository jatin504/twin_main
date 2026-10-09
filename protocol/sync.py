from state.database import StateDatabase

from protocol.mapper import RegisterMapper

from protocol.register_bank import RegisterBank


class RegisterSynchronizer:
    """
    Copies engineering values from the simulator
    into the Modbus RegisterBank.
    """

    def __init__(
        self,
        database: StateDatabase,
        mapper: RegisterMapper,
        bank: RegisterBank,
    ):

        self.database = database
        self.mapper = mapper
        self.bank = bank

    def update(self):

        #
        # Convert engineering values
        # into Modbus register values
        #
        registers = self.mapper.export(
            self.database
        )

        #
        # Copy into RegisterBank
        #
        for address, value in registers.items():

            self.bank.write(
                address,
                value,
            )