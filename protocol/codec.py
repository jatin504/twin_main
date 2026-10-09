import struct

from protocol.datatypes import RegisterType


class Codec:

    @staticmethod
    def encode(
        value,
        datatype,
        scale=1,
    ):

        match datatype:

            case RegisterType.BOOL:
                return Codec.encode_bool(value)

            case RegisterType.UINT16:
                return Codec.encode_uint16(value, scale)

            case RegisterType.INT16:
                return Codec.encode_int16(value, scale)

            case RegisterType.UINT32:
                return Codec.encode_uint32(value, scale)

            case RegisterType.INT32:
                return Codec.encode_int32(value, scale)

            case RegisterType.FLOAT32:
                return Codec.encode_float32(value)

            case _:
                raise NotImplementedError(datatype)

    @staticmethod
    def decode(
        registers,
        datatype,
        scale=1,
    ):

        match datatype:

            case RegisterType.BOOL:
                return Codec.decode_bool(registers)

            case RegisterType.UINT16:
                return Codec.decode_uint16(registers, scale)

            case RegisterType.INT16:
                return Codec.decode_int16(registers, scale)

            case RegisterType.UINT32:
                return Codec.decode_uint32(registers, scale)

            case RegisterType.INT32:
                return Codec.decode_int32(registers, scale)

            case RegisterType.FLOAT32:
                return Codec.decode_float32(registers)

            case _:
                raise NotImplementedError(datatype)


    @staticmethod
    def register_count(datatype):

        match datatype:

            case RegisterType.BOOL:
                return 1

            case RegisterType.UINT16:
                return 1

            case RegisterType.INT16:
                return 1

            case RegisterType.UINT32:
                return 2

            case RegisterType.INT32:
                return 2

            case RegisterType.FLOAT32:
                return 2

            case _:
                raise NotImplementedError(datatype)
            

    @staticmethod
    def encode_bool(value):

        return [1 if value > 0 else 0]


    @staticmethod
    def decode_bool(registers):

        return bool(registers[0])

    @staticmethod
    def encode_uint16(value, scale):

        return [
            int(value * scale)
        ]


    @staticmethod
    def decode_uint16(registers, scale):

        return registers[0] / scale

    @staticmethod
    def encode_int16(value, scale):

        value = int(value * scale)

        if value < 0:
            value += 65536

        return [value]


    @staticmethod
    def decode_int16(registers, scale):

        value = registers[0]

        if value >= 32768:
            value -= 65536

        return value / scale

    @staticmethod
    def encode_uint32(value, scale):

        value = int(value * scale)

        return [

            (value >> 16) & 0xFFFF,

            value & 0xFFFF,

        ]


    @staticmethod
    def decode_uint32(registers, scale):

        value = (

            (registers[0] << 16)

            |

            registers[1]

        )

        return value / scale


    @staticmethod
    def encode_int32(value, scale):

        value = int(value * scale)

        packed = struct.pack(">i", value)

        return list(
            struct.unpack(">HH", packed)
        )


    @staticmethod
    def decode_int32(registers, scale):

        packed = struct.pack(
            ">HH",
            registers[0],
            registers[1],
        )

        value = struct.unpack(
            ">i",
            packed,
        )[0]

        return value / scale

    @staticmethod
    def encode_float32(value):

        packed = struct.pack(
            ">f",
            float(value),
        )

        return list(
            struct.unpack(">HH", packed)
        )


    @staticmethod
    def decode_float32(registers):

        packed = struct.pack(
            ">HH",
            registers[0],
            registers[1],
        )

        return struct.unpack(
            ">f",
            packed,
        )[0]