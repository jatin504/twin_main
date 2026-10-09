from protocol.modbus.requests import (
    ReadHoldingRegistersRequest,
    WriteSingleRegisterRequest,
    WriteMultipleRegistersRequest,
)

from protocol.modbus.responses import (
    ReadHoldingRegistersResponse,
    WriteSingleRegisterResponse,
    WriteMultipleRegistersResponse
)

from protocol.modbus.adapter import ModbusAdapter


class ModbusService:

    def __init__(self, adapter: ModbusAdapter):

        self.adapter = adapter

    def read_holding_registers(
        self,
        request: ReadHoldingRegistersRequest,
    ):

        values = self.adapter.read_holding(
            request.address,
            request.quantity,
            request.unit_id
        )

        return ReadHoldingRegistersResponse(
            values=values,
        )

    def write_register(
        self,
        request: WriteSingleRegisterRequest,
    ):

        self.adapter.write_holding(
            request.address,
            request.value,
            request.unit_id
        )

        return WriteSingleRegisterResponse(
            address=request.address,
            value=request.value,
        )
    
    def write_multiple_registers(
        self,
        request: WriteMultipleRegistersRequest,
    ):

        self.adapter.write_multiple_holding(
            request.address,
            request.values,
            request.unit_id
        )

        return WriteMultipleRegistersResponse(
            address=request.address,
            quantity=len(request.values)
        )