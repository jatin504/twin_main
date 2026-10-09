from __future__ import annotations

from common.constants import DEFAULT_RAMP_RATE_KW_PER_SEC
from common.enums import PCSState
from models.base import BaseSimulationModel
from models.controllers.ramp_limiter import RampLimiter
from state.tags import Tags


class PowerFlowEngine(BaseSimulationModel):
    """
    Simulates the PCS active power controller.

    Phase-1 implementation:
        - State validation
        - Active power ramp
        - Output generation

    Future:
        - Battery limits
        - Thermal derating
        - Protection limits
        - Efficiency
    """

    DEFAULT_RAMP_RATE = DEFAULT_RAMP_RATE_KW_PER_SEC

    def __init__(self, context):

        super().__init__(context)

        self.ramp = RampLimiter(
            self.DEFAULT_RAMP_RATE
        )

    def initialize(self):

        self.db.set(
            Tags.PCS.ACTIVE_POWER_OUTPUT,
            0.0,
        )

    def update(self, dt: float):

        state = PCSState(
            self.db.value(Tags.PCS.STATE)
        )

        current_output = self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

        # Only produce power while running
        if state not in (
            PCSState.GRID_FOLLOWING,
            PCSState.GRID_FORMING,
        ):

            target = 0.0

        else:

            target = self.db.value(
                Tags.PCS.ACTIVE_POWER_REFERENCE
            )

        output = self.ramp.update(
            current=current_output,
            target=target,
            dt=dt,
        )

        self.db.set(
            Tags.PCS.ACTIVE_POWER_OUTPUT,
            output,
        )

        #
        # Temporary debug
        #
        # print(
        #     f"Reference={target:8.1f} kW | "
        #     f"Output={output:8.1f} kW"
        # )