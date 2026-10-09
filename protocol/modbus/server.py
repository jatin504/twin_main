import asyncio

from protocol.modbus.dispatcher import ModbusDispatcher
from protocol.modbus.encoder import ResponseEncoder
from protocol.modbus.mbap import MBAPDecoder
from protocol.modbus.pdu import PDUParser
from protocol.modbus.service import ModbusService


class ModbusTCPServer:

    """
    Async TCP server.

    Protocol parsing will be added later.
    """

    def __init__(self,
                 dispatcher: ModbusDispatcher,
                 host="0.0.0.0",
                 port=5020):

        self.dispatcher = dispatcher

        self.host = host

        self.port = port

        self.server = None

    async def start(self):

        self.server = await asyncio.start_server(

            self.handle_client,

            host=self.host,

            port=self.port,

        )

        print()

        print("=" * 60)

        print(" Modbus TCP Server Started")

        print(f" Listening : {self.host}:{self.port}")

        print("=" * 60)

        print()

        async with self.server:

            await self.server.serve_forever()

    async def handle_client(

        self,

        reader: asyncio.StreamReader,

        writer: asyncio.StreamWriter,

    ):

        address = writer.get_extra_info("peername")

        print(f"Client Connected : {address}")

        try:

            while True:

                data = await reader.read(1024)

                if not data:

                    break

                # print()

                # print("Received Bytes")

                header, pdu = MBAPDecoder.decode(data)

                # print()

                # print(header)

                request = PDUParser.parse(pdu, header)
                # print(request)

                response = self.dispatcher.dispatch(
                    request
                )

                # print(response)

                frame = ResponseEncoder.encode_frame(
                    header,
                    response,
                )

                writer.write(frame)

                await writer.drain()

                #
                # Protocol parser
                # will be added
                #

        except Exception as ex:

            print(ex)

        finally:

            print(f"Client Disconnected : {address}")

            writer.close()

            await writer.wait_closed()