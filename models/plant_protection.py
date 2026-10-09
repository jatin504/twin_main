from common.constants import BASE_HV_VOLTAGE, BASE_LV_VOLTAGE
from common.enums import FaultCode
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class PlantProtectionManager(BaseSimulationModel):

    def update(self, dt):

        self.ppc_db = self.plant_database.device("PPC")

        self.clear_fault()

        self.check_grid()

        self.check_voltage()

        self.check_transformer_loading()

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

        OVER_VOLTAGE_LIMIT_PU = 1.05
        UNDER_VOLTAGE_LIMIT_PU = 0.95

        # Tag -> nominal/base voltage
        voltage_tags = {
            Tags.Grid.VOLTAGE: BASE_HV_VOLTAGE,

            Tags.Grid.BUS_VOLTAGE_A: BASE_LV_VOLTAGE,
            Tags.Grid.BUS_VOLTAGE_B: BASE_LV_VOLTAGE,
            Tags.Grid.BUS_VOLTAGE_C: BASE_LV_VOLTAGE,

            Tags.PCS.AC_VOLTAGE: BASE_LV_VOLTAGE,

            Tags.Network.LOAD_VOLTAGE: BASE_LV_VOLTAGE
        }

        for tag, base_voltage in voltage_tags.items():

            voltage = self.ppc_db.value(tag)

            if voltage is None:
                continue

            # Grid voltage is stored in kV
            if tag == Tags.Grid.VOLTAGE:
                voltage = float(voltage) * 1000.0

            else:
                voltage = float(voltage)

            # Convert to per-unit
            voltage_pu = voltage / base_voltage

            if voltage_pu > OVER_VOLTAGE_LIMIT_PU:

                self.raise_fault(
                    FaultCode.OVER_VOLTAGE
                )

                # print(
                #     f"OVER VOLTAGE: "
                #     f"{voltage_pu:.3f} pu "
                #     f"(tag={tag})"
                # )

            elif voltage_pu < UNDER_VOLTAGE_LIMIT_PU:

                self.raise_fault(
                    FaultCode.UNDER_VOLTAGE
                )

                # print(
                #     f"UNDER VOLTAGE: "
                #     f"{voltage_pu:.3f} pu "
                #     f"(tag={tag})"
                # )

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

    def check_transformer_loading(self):

        OVER_LOADING_LIMIT = 0.80
        UNDER_LOADING_LIMIT = 0

        # Tag -> nominal/base transformer_loading
        transformer_tags = {
            Tags.Transformer.T1_LOADING: 100.0,
            Tags.Transformer.T2_LOADING: 100.0,
            Tags.Transformer.T3_LOADING: 100.0,
        }

        for tag, base_transformer in transformer_tags.items():

            transformer = self.ppc_db.value(tag)

            if transformer is None:
                continue

            transformer = float(transformer)

            # Convert to per-unit
            transformer_pu = transformer / base_transformer

            if transformer_pu > OVER_LOADING_LIMIT:

                self.raise_fault(
                    FaultCode.TRANSFORMER_OVERLOADING
                )

                # print(
                #     f"TRANSFORMER_OVERLOADING: "
                #     f"{transformer_pu:.3f} pu "
                #     f"(tag={tag})"
                # )

            elif transformer_pu < UNDER_LOADING_LIMIT:

                self.raise_fault(
                    FaultCode.TRANSFORMER_UNDERLOADING
                )

                # print(
                #     f"TRANSFORMER_UNDERLOADING: "
                #     f"{transformer_pu:.3f} pu "
                #     f"(tag={tag})"
                # )