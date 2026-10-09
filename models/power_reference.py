from common.enums import PCSState
from models.base import BaseSimulationModel
from models.operating_mode import OperatingMode
from state.tags import Tags


class PowerReferenceModel(BaseSimulationModel):
    """
    Converts external EMS commands into an internal PCS
    active power reference.

    Future versions will apply:
      - Battery limits
      - Thermal derating
      - Protection limits
      - AGC
      - Frequency support
    """

    def update(self, dt: float):

        #
        # PCS must be running
        #

        mode = self.db.value(
            Tags.PCS.OPERATING_MODE
        )

        if mode == OperatingMode.GRID_FOLLOWING:

            if not self.db.value(Tags.Grid.SYNCHRONIZED):

                self.db.set(
                    Tags.PCS.ACTIVE_POWER_REFERENCE,
                    0.0,
                )

                return

        #
        # Battery ready?
        #
        if not self.db.value(Tags.BMS.READY):

            self.db.set(
                Tags.PCS.ACTIVE_POWER_REFERENCE,
                0.0,
            )
            return

        command = self.db.value(
            Tags.EMS.ACTIVE_POWER_COMMAND
        )

        #
        # Discharge
        #
        if command > 0:

            if not self.db.value(
                Tags.BMS.DISCHARGE_ENABLE
            ):

                command = 0.0

            else:

                limit = self.db.value(
                    Tags.BMS.MAX_DISCHARGE_POWER
                )

                command = min(
                    command,
                    limit,
                )

        #
        # Charge
        #
        elif command < 0:

            if not self.db.value(
                Tags.BMS.CHARGE_ENABLE
            ):

                command = 0.0

            else:

                limit = self.db.value(
                    Tags.BMS.MAX_CHARGE_POWER
                )

                command = max(
                    command,
                    -limit,
                )

        self.db.set(
            Tags.PCS.ACTIVE_POWER_REFERENCE,
            command,
        )