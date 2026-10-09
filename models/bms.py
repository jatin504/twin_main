from common.constants import DEFAULT_MAX_CHARGE_POWER_KW, DEFAULT_MAX_DISCHARGE_POWER_KW, MIN_SOC, MAX_SOC

from models.base import BaseSimulationModel
from state.tags import Tags


class BMSModel(BaseSimulationModel):
    """
    Converts battery state into operational limits
    exposed to the PCS.
    """

    MIN_SOC = MIN_SOC
    MAX_SOC = MAX_SOC

    MAX_CHARGE_POWER = DEFAULT_MAX_CHARGE_POWER_KW
    MAX_DISCHARGE_POWER = DEFAULT_MAX_DISCHARGE_POWER_KW

    def update(self, dt: float):

        soc = self.db.value(Tags.Battery.SOC)

        fault = self.db.value(Tags.Battery.FAULT)

        ready = not fault

        self.db.set(Tags.BMS.READY, ready)
        self.db.set(Tags.BMS.FAULT, fault)

        #
        # Charging enable
        #
        charge_enable = soc < self.MAX_SOC

        #
        # Discharging enable
        #
        discharge_enable = soc > self.MIN_SOC

        self.db.set(
            Tags.BMS.CHARGE_ENABLE,
            charge_enable,
        )

        self.db.set(
            Tags.BMS.DISCHARGE_ENABLE,
            discharge_enable,
        )

        #
        # Power limits
        #
        self.db.set(
            Tags.BMS.MAX_CHARGE_POWER,
            self.MAX_CHARGE_POWER if charge_enable else 0.0,
        )

        self.db.set(
            Tags.BMS.MAX_DISCHARGE_POWER,
            self.MAX_DISCHARGE_POWER if discharge_enable else 0.0,
        )