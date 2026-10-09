import asyncio
import threading

from protocol.modbus.adapter import ModbusAdapter
from protocol.modbus.dispatcher import ModbusDispatcher
from protocol.modbus.server import ModbusTCPServer
from protocol.modbus.service import ModbusService


def start_modbus_server(simulator):
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            adapter = ModbusAdapter(simulator.modbus_sessions)
            service = ModbusService(adapter)
            dispatcher = ModbusDispatcher(service)
            server = ModbusTCPServer(dispatcher)

            await server.start()

            # Keep server alive
            await asyncio.Event().wait()

        try:
            loop.run_until_complete(run())
        finally:
            loop.close()

    thread = threading.Thread(
        target=run_server,
        daemon=True,
    )
    thread.start()

    return thread