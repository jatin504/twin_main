

from protocol.mapper import RegisterMapper
from protocol.register_bank import RegisterBank
from protocol.reverse_mapper import ReverseRegisterMapper


class ModbusSession:

    """
    Complete Modbus runtime of one device.
    """

    def __init__(
        self,
        context,
        mappings,
        slave_id: int,
    ):

        self.context = context

        self.device_id = context.id

        self.slave_id = slave_id

        self.register_bank = RegisterBank()

        self.mapper = RegisterMapper(
            context.database,
            self.register_bank,
            mappings,
        )

        self.reverse_mapper = ReverseRegisterMapper(
            context.database,
            self.register_bank,
            mappings,
            context.command_manager
        )

    def forward_synchronize(self):

        self.mapper.synchronize()


    def reverse_synchronize(self):
       
        self.reverse_mapper.synchronize()