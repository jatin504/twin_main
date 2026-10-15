from commands.manager import CommandManager
from common.enums import PCSState
from controllers.command_manager import CommandManager as Command
from common.constants import SIMULATION_STEP_SEC
from core.device_context import DeviceContext

from protocol.modbus.session import ModbusSession
from protocol.small_mapping import MAPPINGS

from core.scheduler import Scheduler
from runtime.build_simulation import build_simulation
from state.definition import populate_database
from state.device_database import DeviceDatabase
from state.plant_database import PlantDatabase
from state.tags import Tags

import threading

class Simulator:

    def __init__(self):

        self.plant_database = PlantDatabase()

        self.scheduler = Scheduler(cycle_time=SIMULATION_STEP_SEC)

        self.contexts = {}

        self.modbus_sessions = {}

        # PPC
        self.plant_device_id = "PPC"
        self.plant_slave_id = 50

        # Load history configuration from configs/history_config.json
        from common.history_config import load_history_config
        self.history_config = load_history_config()
        self.history_devices = list(self.history_config.target_devices)

        self._stop_event = threading.Event()

        self._simulation_thread = None

        self._network = None
        self._simulator = self

        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def network(self):
        return self._network

    @property
    def network_manager(self):
        return self._network

    def start(self, sim, net):

        if self._running:
            return

        self._network = net
        self._simulator = sim
        self._running = True

        self.scheduler.initialize()

        self._simulation_thread = threading.Thread(
            target=self.run,
            args=(sim, net),
            daemon=True,
        )

        self._simulation_thread.start()

    def stop(self):

        self.scheduler.stop()

        if (
            self._simulation_thread
            # and self._simulation_thread.is_alive()
        ):
            self._simulation_thread.join()

        self._simulation_thread = None
        self._running = False

    def reset(self, restart=True):
        was_running = self._running

        if was_running:
            self.stop()

        # Clear old simulation objects
        self.clear()

        # Read changed YAML and rebuild everything
        print("Reloading YAML and rebuilding simulation...")

        sim_target = getattr(self, "_simulator", self) or self
        topology, net, simulator = build_simulation(
            sim_target,
            "plant/plant.yaml",
        )

        self._simulator = simulator
        self._network = net

        if restart:
            self.start(simulator, net)

        return net

    def clear(self):

        # Make sure simulation is stopped
        self.stop()

        for model in self.scheduler.models:
            try:
                model.clear()
            except Exception:
                pass
        self.scheduler.models.clear()

        # Clear device contexts
        self.contexts.clear()

        # Clear Modbus sessions
        self.modbus_sessions.clear()

        # Reset plant database if required
        self.plant_database.clear()


    def add_model(self, model):

        self.scheduler.add_model(model)

    def record_history(self, device_ids: list[str] | str | None = None):
        """
        Record historical data for targeted devices (defaults to self.history_devices).
        """
        targets = device_ids if device_ids is not None else self.history_devices
        return self.plant_database.record_history(device_ids=targets)

    @property
    def history_window_sec(self) -> float:
        return self.history_config.history_window_seconds

    @property
    def history_save_interval(self) -> float:
        return self.history_config.save_interval_seconds

    def reload_history_config(self, config_path: str | None = None):
        """Reload configuration from JSON file."""
        from common.history_config import load_history_config
        self.history_config = load_history_config(config_path)
        self.history_devices = list(self.history_config.target_devices)
        self.set_history_window(self.history_config.history_window_seconds)

    def set_history_window(
        self,
        window_sec: float,
        max_samples: int | None = None,
        device_ids: list[str] | None = None,
    ) -> None:
        """
        Configure rolling history window duration in seconds.
        E.g. 900 for 15 minutes, 1800 for 30 minutes, 3600 for 1 hour.
        """
        self.history_config.history_window_seconds = float(window_sec)
        self.plant_database.set_history_window(
            window_sec=window_sec,
            max_samples=max_samples,
            device_ids=device_ids,
        )

    def save_history_to_json(
        self,
        file_path: str | None = None,
        device_ids: list[str] | None = None,
        last_seconds: float | None = None,
    ) -> str:
        """
        Export historical records to a JSON file.
        """
        out_path = file_path or self.history_config.export_file_path
        targets = device_ids if device_ids is not None else self.history_devices
        window = last_seconds if last_seconds is not None else self.history_window_sec
        return self.plant_database.save_history_to_json(
            file_path=out_path,
            device_ids=targets,
            last_seconds=window,
        )

    def get_history(
        self,
        device_id: str | None = None,
        tag_name: str | None = None,
        last_seconds: float | None = None,
    ):
        """
        Retrieve historical samples for a device (defaults to PPC).
        """
        target = device_id or self.plant_device_id
        window = last_seconds if last_seconds is not None else self.history_window_sec
        return self.plant_database.get_history(
            device_id=target,
            tag_name=tag_name,
            last_seconds=window,
        )

    def run(self, sim, network):
        try:
            self.scheduler.run(sim, network)
        finally:
            self._running = False

    def create_device(
        self,
        device_id,
        initial_values=None,
    ):

        self.plant_database.add_device(device_id)

        database = DeviceDatabase(
            self.plant_database,
            device_id,
        )

        populate_database(
            database,
            initial_values=initial_values,
        )

        context = DeviceContext(
            device_id=device_id,
            simulator=self,
            database=database,
            plant_database=self.plant_database,
            command=Command(database),
            command_manager=CommandManager(),
        )

        self.contexts[device_id] = context

        return context

    def context(
        self,
        device_id,
    ):

        return self.contexts[device_id]

    def devices(self):

        return self.contexts.values()

    def device(

        self,

        device_id,

    ):

        return self.contexts[device_id]


    def pcs(self):

        for context in self.contexts.values():

            if context.id == self.plant_device_id:

                continue

            yield context


    def create_modbus_session(

        self,

        device_id,

        slave_id,

    ):

        context = self.context(device_id)

        session = ModbusSession(

            context,

            MAPPINGS,

            slave_id,

        )

        self.modbus_sessions[device_id] = session

        return session

    def session(

        self,

        device_id,

    ):

        return self.modbus_sessions[device_id]

    def available_pcs(self):

        for context in self.pcs():

            db = context.database

            if ( db.value( Tags.PCS.STATE ) == PCSState.OFF ):

                continue

            yield context