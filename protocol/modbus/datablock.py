from pymodbus.datastore import ModbusSequentialDataBlock


class RegisterDataBlock(ModbusSequentialDataBlock):
    """
    Modbus DataBlock backed directly by RegisterBank.
    """

    def __init__(self, register_bank):
        super().__init__(0, [0] * 65536)
        self.bank = register_bank

    def getValues(self, address, count=1):
        return self.bank.read_block(address, count)

    def setValues(self, address, values):
        self.bank.write_block(address, values)