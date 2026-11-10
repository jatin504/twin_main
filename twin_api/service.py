"""Own one built-in simulation and its Modbus listener per service process."""
import asyncio
import logging
import os
from math import isfinite
from pathlib import Path
from uuid import uuid4
from core.simulator import Simulator
from models.dispatch_schedule import DispatchSchedule
from runtime.build_simulation import build_simulation
from protocol.modbus.adapter import ModbusAdapter
from protocol.modbus.dispatcher import ModbusDispatcher
from protocol.modbus.server import ModbusTCPServer
from protocol.modbus.service import ModbusService
from twin_api.dashboard import feeder_load, transformer_loading
from twin_api.event_history import EventHistory

logger = logging.getLogger(__name__)


def build_backend():
    # Lazy imports keep app creation independent of the physics stack and Qt UI.
    simulator = Simulator()
    _, network, simulator = build_simulation(simulator, "plant/plant.yaml")
    dispatch_path = os.getenv("BESS_DISPATCH_RESULT_PATH")
    if dispatch_path:
        schedule = DispatchSchedule(
            simulator.context(simulator.plant_device_id), Path(dispatch_path)
        )
        simulator.dispatch_schedule = schedule
        simulator.add_model(schedule)
    return simulator, network


async def open_modbus(simulator):

    handler = ModbusTCPServer(
        ModbusDispatcher(ModbusService(ModbusAdapter(simulator.modbus_sessions))),
        host=os.getenv("DIGITAL_TWIN_MODBUS_HOST", "0.0.0.0"),
        port=int(os.getenv("DIGITAL_TWIN_MODBUS_PORT", "5020")),
    )
    # Bind before reporting success, so a port conflict becomes an HTTP failure.
    return await asyncio.start_server(handler.handle_client, handler.host, handler.port)


class SimulationService:
    """Serialize starts and preserve startup if an HTTP caller disconnects."""

    def __init__(self, builder=build_backend, listener=open_modbus):
        self._builder = builder
        self._listener = listener
        self._lock = asyncio.Lock()
        self._transition = None
        self._phase = "stopped"
        self._simulator = None
        self._server = None
        self._run_id = None
        history_dir = Path(os.getenv("BESS_EVENT_HISTORY_DIR") or "data/event_history")
        self.event_history = EventHistory(history_dir)

    async def start(self):
        """Accept startup without waiting for initialization to finish."""
        return await self._change_state("starting")

    async def restart(self):
        """Stop the previous run and wait until a fresh run is running."""
        return await self._change_state("restarting")

    async def _change_state(self, phase):
        while True:
            async with self._lock:
                status = self._status()
                if phase == "starting" and status == "running":
                    return "running", True
                if phase == "stopping" and status == "stopped":
                    return "stopped", True
                pending = self._transition
                if pending is None or pending.done():
                    self._phase = phase
                    pending = asyncio.create_task(self._run_transition(phase))
                    pending.add_done_callback(self._observe_transition)
                    self._transition = pending
                if phase == "starting":
                    return self._phase, False
                phase_pending = self._phase == phase
                if phase == "stopping" and phase_pending:
                    return "stopping", False

            if phase_pending:
                await asyncio.shield(pending)
                return "running", False
            # Wait outside the lock and retry after the earlier operation.
            await asyncio.gather(asyncio.shield(pending), return_exceptions=True)

    async def _run_transition(self, phase):
        try:
            if self._simulator is not None:
                await self._stop()
            if phase == "stopping":
                self._phase = "stopped"
                return
            await self._start()
            if not self._is_running():
                raise RuntimeError("Simulation thread did not reach running")
            self._phase = "running"
        except BaseException:
            self._phase = "failed"
            raise

    @staticmethod
    def _observe_transition(task):
        if not task.cancelled() and (error := task.exception()) is not None:
            logger.error("Simulation lifecycle operation failed",
                         exc_info=(type(error), error, error.__traceback__))

    def _status(self):
        if self._phase == "running" and not self._is_running():
            return "failed"
        return self._phase

    def _is_running(self):
        if self._simulator is None or not self._simulator.is_running:
            return False
        thread = self._simulator._simulation_thread
        return thread is not None and thread.is_alive()

    async def status(self):
        async with self._lock:
            return self._status()

    async def trend_frame(self, since=None, run_id=None):
        """Read the current run and ignore a cursor belonging to an older run."""
        async with self._lock:
            status = self._status()
            current_run = self._run_id if status == "running" else None
            devices = {}
            if status == "running":
                simulator = self._simulator
                devices = await asyncio.to_thread(
                    simulator.plant_database.get_all_history,
                    device_ids=simulator.history_devices,
                    last_seconds=3600,
                )
                if since is not None and (run_id is None or run_id == current_run):
                    devices = {
                        device_id: {
                            tag: [point for point in points if point["time"] > since]
                            for tag, points in series.items()
                        }
                        for device_id, series in devices.items()
                    }
            return current_run, {"status": status, "window_seconds": 3600, "devices": devices}

    async def snapshot(self):
        """Return the legacy snapshot with all devices and dashboard widgets."""
        async with self._lock:
            status = self._status()
            if status != "running":
                return {"status": status, "devices": {}, "voltage_profile": {},
                        "feeder_load": None, "transformer_loading": None}
            simulator = self._simulator
            devices = {
                device_id: database.snapshot()
                for device_id, database in simulator.plant_database.items()
            }
            ppc = devices[simulator.plant_device_id]
            return {
                "status": status,
                "devices": devices,
                "voltage_profile": {
                    bus: float(value) if value is not None and isfinite(value) else None
                    for bus, value in simulator.network.voltage_profile.items()
                },
                "feeder_load": feeder_load(ppc),
                "transformer_loading": transformer_loading(
                    ppc, simulator.network.topology["transformers"]
                ),
            }

    async def snapshot_v2(self, device_ids: set[str], tags: set[str] | None = None):
        """Read requested tags, or all devices and tags when both filters are empty."""
        async with self._lock:
            if self._status() != "running":
                return {}
            include_all = not device_ids and not tags
            return {
                device_id: database.snapshot(tags)
                for device_id, database in self._simulator.plant_database.items()
                if include_all or device_id in device_ids
            }

    async def dispatch(self):
        """Read the schedule and active interval from the current run."""
        async with self._lock:
            status = self._status()
            if status == "running":
                schedule = self._simulator.dispatch_schedule
                if schedule is not None:
                    return schedule.snapshot()
                status = "no_schedule"
            return {"status": status, "simulation_time": None, "active_event": None,
                    "current_interval": None, "rows": []}

    async def _start(self):
        simulator, network = await asyncio.to_thread(self._builder)
        schedule = simulator.dispatch_schedule
        run_id = uuid4().hex
        if schedule is not None:
            ppc = simulator.plant_database.device(simulator.plant_device_id)

            def record_event_history():
                self.event_history.record(run_id, schedule, ppc, network.voltage_profile)

            simulator.scheduler.after_network_update = record_event_history
        server = await self._listener(simulator)
        try:
            await asyncio.to_thread(simulator.start, simulator, network)
        except BaseException:
            server.close()
            await server.wait_closed()
            # Simulator.start sets its flag before model initialization.
            await asyncio.to_thread(simulator.stop)
            raise
        self._simulator = simulator
        self._server = server
        self._run_id = run_id

    async def stop(self):
        """Queue cleanup after any earlier lifecycle operation."""
        status, _ = await self._change_state("stopping")
        return status

    async def _stop(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        if self._simulator is not None:
            await asyncio.to_thread(self._simulator.stop)
        self.event_history.stop()
        self._server = None
        self._simulator = None
        self._run_id = None

    async def close(self):
        await self.stop()
        if self._transition is not None:
            await asyncio.shield(self._transition)
