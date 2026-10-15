from __future__ import annotations

import threading
import time

from models.base import BaseSimulationModel


class Scheduler:

    def __init__(self, cycle_time: float = 0.1):
        self.cycle_time = cycle_time
        self.models: list[BaseSimulationModel] = []

        self.running = False
        self.reverse_thread = None

    def add_model(self, model: BaseSimulationModel):
        self.models.append(model)

    def initialize(self):
        for model in self.models:
            model.initialize()

    def _reverse_sync_loop(self, simulator):
        """Run external/server -> register synchronization independently."""
        while self.running:

            start = time.perf_counter()

            for session in simulator.modbus_sessions.values():
                try:
                    session.reverse_synchronize()
                except Exception as e:
                    print(f"Reverse sync error: {e}")

            elapsed = time.perf_counter() - start
            remaining = self.cycle_time - elapsed

            if remaining > 0:
                time.sleep(remaining)

    def run(self, simulator, network):

        self.running = True

        # Start reverse synchronization independently
        self.reverse_thread = threading.Thread(
            target=self._reverse_sync_loop,
            args=(simulator,),
            daemon=True,
        )
        self.reverse_thread.start()

        try:
            # previous = time.perf_counter()

            step_count = 0
            while self.running:
                step_count += 1
                dt = 0.5

                for model in self.models:
                    try:
                        if model.enabled:
                            model.update(dt)
                    except Exception as e:
                        print(f"Error in Model[{model.name}]: {e}")

                network.update()

                for session in simulator.modbus_sessions.values():
                    session.forward_synchronize()

                # Record historical time-series data for enabled tags
                try:
                    simulator.record_history()
                except Exception as e:
                    print(f"Error recording history: {e}")

                # Periodically save history to JSON file (configurable interval)
                save_interval_steps = max(
                    1,
                    int(getattr(simulator, "history_save_interval", 5.0) / 0.5),
                )
                if step_count % save_interval_steps == 0:
                    try:
                        simulator.save_history_to_json()
                    except Exception:
                        pass

                time.sleep(0.5)

        finally:
            self.running = False

            try:
                simulator.save_history_to_json()
            except Exception:
                pass

            if self.reverse_thread and self.reverse_thread.is_alive():
                try:
                    self.reverse_thread.join(timeout=1.0)
                except Exception:
                    pass
            self.reverse_thread = None

            for model in self.models:
                model.shutdown()

    def stop(self):
        self.running = False

        if self.reverse_thread and self.reverse_thread.is_alive():
            try:
                self.reverse_thread.join(timeout=1.0)
            except Exception:
                pass
        self.reverse_thread = None

        for model in self.models:
            model.shutdown()

    def clear(self):
        self.models.clear()

    def reset(self):
        self.running = False

        if self.reverse_thread and self.reverse_thread.is_alive():
            try:
                self.reverse_thread.join(timeout=1.0)
            except Exception:
                pass
        self.reverse_thread = None

        for model in self.models:
            model.initialize()
