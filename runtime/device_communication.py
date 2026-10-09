from protocol.mapper import RegisterMapper
from protocol.register_bank import RegisterBank
from protocol.reverse_mapper import ReverseRegisterMapper


class DeviceCommunication:

    def __init__(

        self,

        context,

        mappings,

    ):

        self.register_bank = RegisterBank()

        self.mapper = RegisterMapper(

            context,

            self.register_bank,

            mappings,

        )

        self.reverse_mapper = ReverseRegisterMapper(

            context,

            self.register_bank,

            mappings,

        )