from protocol.write_source import WriteSource


class RegisterBank:

    def __init__(self):

        #
        # Registers
        #
        self.holding = [0] * 65536

        self.input = [0] * 65536

        self.coils = [False] * 65536

        self.discrete = [False] * 65536

        #
        # Dirty registers
        #
        self.dirty = set()

        #
        # Commands written from Modbus
        #
        self.changed_registers = set()

    def write(
        self,
        address: int,
        value: int,
        source: WriteSource = WriteSource.SIMULATOR,
    ):

        previous = self.holding[address]

        if previous == value:
            return

        self.holding[address] = value

        #
        # Notify all protocols that the value changed
        #
        self.dirty.add(address)

        #
        # Only Modbus writes are commands.
        #
        if source == WriteSource.MODBUS:

            self.changed_registers.add(address)
        

    def read(self, address: int):

        return self.holding[address]

    def read_block(
        self,
        start: int,
        count: int,
    ):

        return self.holding[
            start:start + count
        ]

    def write_block(
        self,
        start: int,
        values,
        source: WriteSource = WriteSource.SIMULATOR,
    ):

        for offset, value in enumerate(values):

            self.write(
                start + offset,
                value,
                source,
            )

    def consume_changes(self):

        changed = self.changed_registers.copy()

        self.changed_registers.clear()

        return changed
    
    def consume_dirty(self):

        dirty = self.dirty.copy()

        self.dirty.clear()

        return dirty