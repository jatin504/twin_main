from threading import Lock

from common.enums import FaultCode
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class ProtectionManager(BaseSimulationModel):

    BASE_VOLTAGE = 433.0
    MIN_VOLTAGE_PU = 0.95
    MAX_VOLTAGE_PU = 1.05
    MIN_FREQUENCY_HZ = 48
    MAX_FREQUENCY_HZ = 52
    MAX_TEMPERATURE_C = 55

    def __init__(self, context):
        super().__init__(context)
        self._test_lock = Lock()
        self._test_measurements = {}

    def set_test_measurement(self, kind, value):
        """Set or clear a simulated input used only by this device's protection."""
        with self._test_lock:
            if value is None:
                self._test_measurements.pop(kind, None)
            else:
                self._test_measurements[kind] = value

    def update(self, dt):

        self.ppc_db = self.plant_database.device("PPC")

        self.clear_fault()

        self.check_grid()

        with self._test_lock:
            measurements = self._test_measurements.copy()
        self.check_voltage(measurements.get("voltage"))
        self.check_frequency(measurements.get("frequency"))
        self.check_temperature(measurements.get("temperature"))


    def clear_fault(self):

        self.db.set(
            Tags.Fault.ACTIVE,
            False,
        )

        self.db.set(
            Tags.Fault.CODE,
            int(FaultCode.NONE),
        )

    def raise_fault(self, code):

        self.db.set(
            Tags.Fault.ACTIVE,
            True,
        )

        self.db.set(
            Tags.Fault.CODE,
            int(code),
        )

    def check_grid(self):

        mode = self.db.value(
            Tags.PCS.OPERATING_MODE
        )

        #
        # Only meaningful in Grid Following.
        #
        if mode != OperatingMode.GRID_FOLLOWING:
            return

        if not self.ppc_db.value(
            Tags.Grid.AVAILABLE
        ):

            self.raise_fault(
                FaultCode.GRID_LOSS
            )

    def check_voltage(self, voltage=None):

        if voltage is None:
            voltage = self.db.value(Tags.PCS.AC_VOLTAGE)
        voltage_pu = voltage / self.BASE_VOLTAGE

        # Keep the same protection logic:
        # Over-voltage  > 1.05 pu
        # Under-voltage < 0.95 pu

        if voltage_pu > self.MAX_VOLTAGE_PU:

            self.raise_fault(
                FaultCode.OVER_VOLTAGE
            )

        elif voltage_pu < self.MIN_VOLTAGE_PU:

            self.raise_fault(
                FaultCode.UNDER_VOLTAGE
            )


    def check_frequency(self, frequency=None):

        if frequency is None:
            frequency = self.ppc_db.value(Tags.Grid.FREQUENCY)
        if frequency > self.MAX_FREQUENCY_HZ:

            self.raise_fault(
                FaultCode.OVER_FREQUENCY
            )

        elif frequency < self.MIN_FREQUENCY_HZ:

            self.raise_fault(
                FaultCode.UNDER_FREQUENCY
            )

    def check_temperature(self, temp=None):

        if temp is None:
            temp = self.db.value(Tags.Battery.TEMPERATURE)
        if temp > self.MAX_TEMPERATURE_C:
        
            self.raise_fault(
                FaultCode.OVER_TEMPERATURE
            )
