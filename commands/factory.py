from datetime import datetime

from commands.pcs import (
    StartCommand,
    StopCommand,
    ResetCommand,
    ActivePowerCommand,
)

from state.tags import Tags


class CommandFactory:

    @staticmethod
    def create(
        tag,
        value,
        source="EMS",
    ):

        timestamp = datetime.now()

        #
        # Start
        #
        if tag == Tags.EMS.START and value:

            return StartCommand(
                timestamp=timestamp,
                source=source,
            )

        #
        # Stop
        #
        if tag == Tags.EMS.STOP and value:

            return StopCommand(
                timestamp=timestamp,
                source=source,
            )

        #
        # Reset
        #
        if tag == Tags.EMS.RESET and value:

            return ResetCommand(
                timestamp=timestamp,
                source=source,
            )

        #
        # Active Power
        #
        if tag == Tags.EMS.ACTIVE_POWER_COMMAND:

            return ActivePowerCommand(
                timestamp=timestamp,
                source=source,
                power=value,
            )

        return None