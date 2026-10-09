import asyncio
import threading
import time

from core.simulator import Simulator

from protocol.modbus.adapter import ModbusAdapter
from protocol.modbus.dispatcher import ModbusDispatcher
from protocol.modbus.server import ModbusTCPServer
from protocol.modbus.service import ModbusService

from runtime.build_simulation import build_simulation
from runtime.load_forecast import load_forecast

def test_simulation(simulator, net):

    # Start immediately
    print("Starting simulation...")
    simulator.start(simulator, net)

    # Wait 15 seconds
    time.sleep(10)

    # Stop simulation
    print("Stopping simulation...")
    simulator.stop()

    # Wait another 15 seconds
    # Total time from start = 30 seconds
    time.sleep(10)

    # Reset simulation
    print("Resetting simulation...")
    simulator.reset()

    print("Simulation reset complete")

def main():

    # Simuator
    simulator = Simulator()

    topology, net, simulator = build_simulation(
        simulator,
        "plant/plant.yaml",
    )

    # Start Simulation
    simulator.start(simulator,net)

    # Start the test sequence in background
    # threading.Thread(
    #     target=test_simulation,
    #     args=(simulator, net),
    #     daemon=True,
    # ).start()


    # Stop Simulation
    # simulator.stop()

    # Restart Simulation
    # simulator.reset()

    # Server
    adapter = ModbusAdapter(simulator.modbus_sessions)

    service = ModbusService(adapter)

    dispatcher = ModbusDispatcher(service)

    server = ModbusTCPServer(dispatcher)

    #Load Forecast
    load_forecast(simulator)

    asyncio.run(server.start())

if __name__ == "__main__":

    main()