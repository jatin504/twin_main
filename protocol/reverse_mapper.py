from commands.command_target import CommandTarget
from protocol.mapping import RegisterMapping
from protocol.datatypes import RegisterType
from protocol.codec import Codec

from commands.factory import CommandFactory


class ReverseRegisterMapper:

    def __init__(
        self,
        database,
        register_bank,
        mappings: list[RegisterMapping],
        command_manager,
    ):

        self.database = database
        self.bank = register_bank
        self.command_manager = command_manager

        #
        # Address -> Mapping
        #
        self.mapping_lookup = {
            mapping.address: mapping
            for mapping in mappings
            if mapping.writable
        }

    def synchronize(self):

        changes = self.bank.consume_changes()

        for address in changes:

            mapping = self.mapping_lookup.get(address)

            if mapping is None:
                continue

            registers = self.bank.read_block(
                mapping.address,
                mapping.register_count,
            )

            value = Codec.decode(
                registers,
                mapping.datatype,
                mapping.scale,
            )

            # command = CommandFactory.create(
            #     mapping.tag,
            #     value,
            # )

            # if command is not None:

            #     self.command_manager.submit(
            #         CommandTarget.PCS,
            #         command,
            #     )

            # else:

            self.database.set(
                mapping.tag,
                value,
            )

            # print(
            #     mapping.tag,
            #     mapping.address,
            #     registers,
            #     value,
            # )
                # self.command_manager.next(CommandTarget.PCS)

            # while self.command_manager.has_command(CommandTarget.PCS):

            #     cmd = self.command_manager.next(CommandTarget.PCS)

            #     print(cmd)

            # print(
            #     "BANK:",
            #     mapping.address,
            #     self.bank.read(mapping.address),
            # )

    def decode(
        self,
        value,
        mapping,
    ):

        value = value / mapping.scale

        if mapping.datatype == RegisterType.BOOL:
            return bool(value)

        return value