import asyncio

from core.simulator import Simulator

from protocol.mapper import RegisterMapper

from protocol.modbus.server import ModbusTCPServer


class Runtime:

    def __init__(self):

        self.simulator: Simulator | None = None

        self.mapper: RegisterMapper | None = None

        self.server: ModbusTCPServer | None = None

    async def simulation_loop(self):

        while True:

            #
            # Execute one simulator cycle
            #
            self.simulator.step()

            #
            # Copy Engineering Values
            # to Modbus Registers
            #
            self.mapper.synchronize()

            #
            # Run at simulator frequency
            #
            await asyncio.sleep(
                self.simulator.dt
            )

    async def start(self):

        #
        # Start simulator
        #
        asyncio.create_task(
            self.simulation_loop()
        )

        #
        # Start Modbus Server
        #
        await self.server.start()