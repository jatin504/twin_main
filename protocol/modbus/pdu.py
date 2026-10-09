from protocol.modbus.function_codes import FunctionCode

from protocol.modbus.mbap import MBAPHeader
from protocol.modbus.requests import (
    ReadHoldingRegistersRequest,
    WriteSingleRegisterRequest,
)


class PDUParser:

    @staticmethod
    def parse(pdu: bytes, header: MBAPHeader):

        function = FunctionCode(pdu[0])

        if function == FunctionCode.READ_HOLDING_REGISTERS:

            address = int.from_bytes(
                pdu[1:3],
                "big",
            )

            quantity = int.from_bytes(
                pdu[3:5],
                "big",
            )

            return ReadHoldingRegistersRequest(
                address=address,
                quantity=quantity,
                unit_id=header.unit_id
            )
        
        if function == FunctionCode.WRITE_SINGLE_REGISTER:

            address = int.from_bytes(
                pdu[1:3],
                "big",
            )

            value = int.from_bytes(
                pdu[3:5],
                "big",
            )

            return WriteSingleRegisterRequest(
                address=address,
                value=value,
                unit_id=header.unit_id
            )

        raise NotImplementedError(
            function
        )