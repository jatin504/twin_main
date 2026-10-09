from network.interface import NetworkInterface
from network.manager import NetworkManager
from network.pydgrid_backend import PyDGridBackend

from plant.parser import PlantParser

from runtime.load_forecast import start_forecast_thread
from runtime.model_factory import ModelFactory

def build_simulation(simulator, yaml_path):

    # Parse YAML
    parser = PlantParser()

    topology = parser.load(yaml_path)

    # Populate PCS Models
    for pcs in topology["pcs"]:

        context = simulator.create_device(
            pcs["id"],
            initial_values=pcs.get("initial_condition"),
        )

        simulator.create_modbus_session(
            pcs["id"],
            pcs["slave_id"],
        )

        ModelFactory.register_pcs_models(
            simulator,
            context,
            pcs.get("initial_condition")
        )

    # Plant / PPC
    ppc = simulator.create_device(
        simulator.plant_device_id
    )

    # Register Global Models
    ModelFactory.register_global_models(
        simulator,
        ppc,
    )

    # Grid Network
    net = NetworkManager(
        PyDGridBackend(),
        NetworkInterface,
        ppc.database,
        topology,
        simulator.plant_database,
    )

    net.initialize()

    # PPC Modbus
    simulator.create_modbus_session(
        simulator.plant_device_id,
        slave_id=simulator.plant_slave_id,
    )

    #Load Forecast
    # start_forecast_thread(simulator)

    return topology, net, simulator