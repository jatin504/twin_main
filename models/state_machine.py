from __future__ import annotations

from commands.status import CommandStatus
from models.base import BaseSimulationModel
from state.tags import Tags

from commands.command_target import CommandTarget
from common.enums import PCSState
from commands.pcs import (
    StartCommand,
    StopCommand,
    ResetCommand,
    ActivePowerCommand,
)


class PCSStateMachine(BaseSimulationModel):

    BOOT_TIME = 3.0
    PRECHARGE_TIME = 5.0

    def __init__(self, context):
        super().__init__(context)

        # self.command_manager = context.command_manager

        self._elapsed = 0.0

        self.start_requested = False
        self.stop_requested = False

    def initialize(self):

        self.db.set(Tags.PCS.STATE, PCSState.OFF.value)
        self.db.set(Tags.PCS.STATE_ELAPSED, 0.0)

    def update(self, dt):

        self.process_commands()

        # self.start_requested = self.db.value(Tags.EMS.START)
        # self.stop_requested = self.db.value(Tags.EMS.STOP)

        state = PCSState(self.db.value(Tags.PCS.STATE))

        self._elapsed += dt

        self.db.set(
            Tags.PCS.STATE_ELAPSED,
            self._elapsed,
        )

        grid = self.db.value(Tags.Grid.AVAILABLE)

        # OFF
        if state == PCSState.OFF:

            if self.start_requested:

                self.start_requested = False

                self._transition(
                    PCSState.BOOT
                )

            return

        # BOOT
        if state == PCSState.BOOT:

            if self._elapsed >= self.BOOT_TIME:

                self._transition(
                    PCSState.PRECHARGE
                )

            return

        # PRECHARGE
        if state == PCSState.PRECHARGE:

            if self._elapsed >= self.PRECHARGE_TIME:

                self._transition(
                    PCSState.READY
                )

            return

        # READY
        if state == PCSState.READY:

            if grid:

                self._transition(
                    PCSState.GRID_FOLLOWING
                )

            else:

                self._transition(
                    PCSState.GRID_FORMING
                )

            return

        # RUNNING

        if state in (
            PCSState.GRID_FOLLOWING,
            PCSState.GRID_FORMING,
        ):

            if self.stop_requested:

                self.stop_requested = False

                self._transition(
                    PCSState.SHUTDOWN
                )

                return

            if self.db.value(Tags.Fault.ACTIVE):

                print(f"Fault is Active. CODE: {self.db.value(Tags.Fault.CODE)}")

                self._transition(
                    PCSState.SHUTDOWN
                )

                return
            
            if grid:

                if state == PCSState.GRID_FOLLOWING:
                    return
            
                self._transition(
                    PCSState.GRID_FOLLOWING
                )

            else:

                if state == PCSState.GRID_FORMING:
                    return

                self._transition(
                    PCSState.GRID_FORMING
                )
    
            return

        # SHUTDOWN
        
        if state == PCSState.SHUTDOWN:

            # Wait until power reaches zero
            if abs(self.db.value(Tags.PCS.ACTIVE_POWER_OUTPUT)) < 1.0:
                self._transition(PCSState.OFF)

            return


    def _transition(self, new_state):

        self.db.set(
            Tags.PCS.STATE,
            new_state.value,
        )

        self._elapsed = 0.0

        self.db.set(
            Tags.PCS.STATE_ELAPSED,
            0.0,
        )

        print(f"STATE -> {new_state.name}")

    def process_commands(self):

        while self.command_manager.has_command(CommandTarget.PCS):

            command = self.command_manager.next(CommandTarget.PCS)

            command.status = CommandStatus.RUNNING

            self.dispatch_command(command)

            command.status = CommandStatus.COMPLETED

            self.command_manager.history.add(command)


    def dispatch_command(self, command):

        if isinstance(command, StartCommand):

            self.handle_start(command)

        elif isinstance(command, StopCommand):

            self.handle_stop(command)

        elif isinstance(command, ResetCommand):

            self.handle_reset(command)

        elif isinstance(command, ActivePowerCommand):

            self.handle_active_power(command)

    def handle_start(self, command):

        print("START COMMAND")

        self.start_requested = True
        self.stop_requested = False

    def handle_stop(self, command):

        print("STOP COMMAND")

        self.stop_requested = True
        self.start_requested = False

    def handle_active_power(self, command):

        print(
            "Power Command = ",
            command.power,
        )

        self.db.set(
            Tags.EMS.ACTIVE_POWER_COMMAND,
            command.power,
        )