from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MBAPHeader:
    """
    Modbus TCP MBAP Header
    """

    transaction_id: int

    protocol_id: int

    length: int

    unit_id: int

    @classmethod
    def from_bytes(cls, data: bytes):

        if len(data) < 7:
            raise ValueError("Incomplete MBAP Header")

        return cls(

            transaction_id=int.from_bytes(
                data[0:2],
                byteorder="big",
            ),

            protocol_id=int.from_bytes(
                data[2:4],
                byteorder="big",
            ),

            length=int.from_bytes(
                data[4:6],
                byteorder="big",
            ),

            unit_id=data[6],
        )

    def to_bytes(self):

        return (

            self.transaction_id.to_bytes(2, "big")

            + self.protocol_id.to_bytes(2, "big")

            + self.length.to_bytes(2, "big")

            + bytes([self.unit_id])

        )
    
class MBAPDecoder:

    @staticmethod
    def decode(frame: bytes):

        header = MBAPHeader.from_bytes(

            frame[:7]

        )

        pdu = frame[7:]

        return header, pdu