from protocol.codec import Codec

from protocol.datatypes import RegisterType
from protocol.register_bank import RegisterBank
from protocol.mapping import RegisterMapping


class RegisterMapper:

    def __init__(
        self,
        database,
        register_bank: RegisterBank,
        mappings: list[RegisterMapping],
    ):

        self.database = database
        self.bank = register_bank
        self.mappings = mappings

    def synchronize(self):

        for mapping in self.mappings:

            # if mapping.writable:
            #     continue

            value = self.database.value(mapping.tag)

            registers = Codec.encode(
                value,
                mapping.datatype,
                mapping.scale,
            )


            # print(
            #     mapping.tag,
            #     mapping.address,
            #     value,
            #     register_value,
            # )

            self.bank.write_block(
                mapping.address,
                registers,
            )

            # print(
            #     "BANK:",
            #     mapping.address,
            #     self.bank.read(mapping.address),
            # )

    def encode(
        self,
        value,
        mapping: RegisterMapping,
    ):

        value *= mapping.scale

        if mapping.datatype == RegisterType.BOOL:

            return 1 if value else 0

        return int(value)