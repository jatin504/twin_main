from state.database import StateDatabase
from state.tags import Tags


class CommandManager:

    def __init__(self, database: StateDatabase):

        self.db = database

    # -----------------------------------------------------

    def start(self):

        self.db.set(Tags.EMS.START, True)

    # -----------------------------------------------------

    def stop(self):

        self.db.set(Tags.EMS.STOP, True)

    # -----------------------------------------------------

    def reset(self):

        self.db.set(Tags.EMS.RESET, True)

    # -----------------------------------------------------

    def clear_commands(self):

        self.db.set(Tags.EMS.START, False)

        self.db.set(Tags.EMS.STOP, False)

        self.db.set(Tags.EMS.RESET, False)

    # -----------------------------------------------------

    def set_active_power(self, kw: float):

        self.db.set(
            Tags.EMS.ACTIVE_POWER_COMMAND,
            kw,
        )

    # -----------------------------------------------------

    def set_reactive_power(self, kvar: float):

        self.db.set(
            Tags.EMS.REACTIVE_POWER_COMMAND,
            kvar,
        )

    # -----------------------------------------------------

    def set_power_factor(self, pf: float):

        self.db.set(
            Tags.EMS.POWER_FACTOR_COMMAND,
            pf,
        )