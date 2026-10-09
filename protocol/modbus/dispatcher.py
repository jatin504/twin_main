from protocol.modbus.requests import (
    ReadHoldingRegistersRequest,
    WriteSingleRegisterRequest,
    WriteMultipleRegistersRequest,
)

from protocol.modbus.service import ModbusService

class ModbusDispatcher:
    """
    Dispatch typed Modbus requests to the service layer.
    """

    def __init__(self, service: ModbusService):

        self.service = service

    def dispatch(self, request):

        #
        # Read Holding Registers
        #
        if isinstance(request, ReadHoldingRegistersRequest):

            return self.service.read_holding_registers(
                request
            )

        #
        # Write Single Register
        #
        if isinstance(request, WriteSingleRegisterRequest):

            return self.service.write_register(
                request
            )

        #
        # Write Multiple Registers
        #
        if isinstance(request, WriteMultipleRegistersRequest):

            return self.service.write_multiple_registers(
                request
            )

        raise NotImplementedError(
            type(request)
        )