from models.base import BaseSimulationModel
from state.tags import Tags


class PowerLimitModel(BaseSimulationModel):

    def update(self, dt):

        reference = self.db.value(
            Tags.PCS.ACTIVE_POWER_REFERENCE
        )

        # Apply BMS limits
        # Apply PCS limits
        # Apply SOH derating
        # Apply Temperature derating

        self.db.set(
            Tags.PCS.ACTIVE_POWER_REFERENCE,
            reference,
        )