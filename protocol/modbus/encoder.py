from protocol.modbus.function_codes import FunctionCode
from protocol.modbus.mbap import MBAPHeader
from protocol.modbus.responses import (
    ReadHoldingRegistersResponse,
    WriteSingleRegisterResponse,
)


class ResponseEncoder:

    @staticmethod
    def encode_pdu(response):

        #
        # Function Code 03
        #
        if isinstance(response, ReadHoldingRegistersResponse):

            byte_count = len(response.values) * 2

            pdu = bytearray()

            pdu.append(FunctionCode.READ_HOLDING_REGISTERS)

            pdu.append(byte_count)

            for value in response.values:

                pdu.extend(
                    value.to_bytes(2, "big")
                )

            return bytes(pdu)

        #
        # Function Code 06
        #
        if isinstance(response, WriteSingleRegisterResponse):

            pdu = bytearray()

            pdu.append(
                FunctionCode.WRITE_SINGLE_REGISTER
            )

            pdu.extend(
                response.address.to_bytes(2, "big")
            )

            pdu.extend(
                response.value.to_bytes(2, "big")
            )

            return bytes(pdu)

        raise NotImplementedError(type(response))
    

    @staticmethod
    def encode_frame(
        request_header: MBAPHeader,
        response,
    ):

        pdu = ResponseEncoder.encode_pdu(response)

        header = MBAPHeader(
            transaction_id=request_header.transaction_id,
            protocol_id=0,
            length=len(pdu) + 1,
            unit_id=request_header.unit_id,
        )

        return header.to_bytes() + pdu