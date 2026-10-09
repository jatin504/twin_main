from common.enums import FaultCode
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class ProtectionManager(BaseSimulationModel):

    def update(self, dt):

        self.ppc_db = self.plant_database.device("PPC")

        self.clear_fault()

        self.check_grid()

        self.check_voltage()

        self.check_frequency()

        self.check_temperature()


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

    def check_voltage(self):

        voltage = self.db.value(
            Tags.PCS.AC_VOLTAGE
        )

        base_voltage = 433.0

        # Convert voltage to per-unit
        voltage_pu = voltage / base_voltage

        # Keep the same protection logic:
        # Over-voltage  > 1.05 pu
        # Under-voltage < 0.95 pu

        if voltage_pu > 1.05:

            self.raise_fault(
                FaultCode.OVER_VOLTAGE
            )

        elif voltage_pu < 0.95:

            self.raise_fault(
                FaultCode.UNDER_VOLTAGE
            )


    def check_frequency(self):

        frequency = self.ppc_db.value(
            Tags.Grid.FREQUENCY
        )

        if frequency > 52:

            self.raise_fault(
                FaultCode.OVER_FREQUENCY
            )

        elif frequency < 48:

            self.raise_fault(
                FaultCode.UNDER_FREQUENCY
            )

    def check_temperature(self):

        temp = self.db.value(
            Tags.Battery.TEMPERATURE
        )

        if temp > 55:
        
            self.raise_fault(
                FaultCode.OVER_TEMPERATURE
            )