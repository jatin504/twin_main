from models.battery import BatteryModel
from models.battery_backend.pybamm_backend import PyBaMMBackend
from models.bms import BMSModel
from models.controllers.active_power_droop import ActivePowerDroopController
from models.grid import GridModel
from models.controllers.grid_following import GridFollowingController
from models.grid_following.reference import GridFollowingReferenceModel
from models.grid_forming.reference import GridFormingReferenceModel
from models.network import NetworkModel
from models.operating_mode_model import OperatingModeModel
from models.plant.dispatch_model import DispatchModel
from models.plant.plant_aggregator import PlantAggregatorModel
from models.power_flow import PowerFlowEngine
from models.power_reference import PowerReferenceModel
from models.protection import ProtectionManager
from models.plant_protection import PlantProtectionManager
from models.state_machine import PCSStateMachine


class ModelFactory:

    @staticmethod
    def register_global_models(
        simulator,
        context,
    ):
        # For Testing purpose
        simulator.add_model(
            BMSModel(context)
        )

        simulator.add_model(
            NetworkModel(context)
        )

        simulator.add_model(
            GridModel(context)
        )

        simulator.add_model(
            DispatchModel(context)
        )

        simulator.add_model(
            PlantAggregatorModel(context)
        )

        simulator.add_model(
            PlantProtectionManager(context)
        )

        # simulator.add_model(
        #     ActivePowerDroopController(context)
        # )

    @staticmethod
    def register_pcs_models(
        simulator,
        context,
        pcs_initial_condition
    ):
        simulator.add_model(
            PCSStateMachine(context)
        )

        simulator.add_model(
            OperatingModeModel(context)
        )

        simulator.add_model(
            GridFollowingController(context)
        )

        simulator.add_model(
            BMSModel(context)
        )

        simulator.add_model(
            GridFollowingReferenceModel(context)
        )

        simulator.add_model(
            GridFormingReferenceModel(context)
        )

        simulator.add_model(
            PowerReferenceModel(context)
        )

        simulator.add_model(
            PowerFlowEngine(context)
        )

        simulator.add_model(
            PyBaMMBackend(context, pcs_initial_condition)
        )

        # simulator.add_model(
        #     BatteryModel(context)
        # )
        
        simulator.add_model(
            ProtectionManager(context)
        )