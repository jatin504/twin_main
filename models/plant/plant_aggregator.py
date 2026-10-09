from models.base import BaseSimulationModel
from state.tags import Tags


class PlantAggregatorModel(BaseSimulationModel):

    def update(self, dt):

        pcs_list = list(self.context.simulator.pcs())

        if not pcs_list:
            return

        total_power = 0.0
        total_energy = 0.0
        total_current = 0.0
        total_voltage = 0.0

        total_soc = 0.0

        for pcs in pcs_list:

            db = pcs.database

            power = db.value(Tags.Battery.POWER)
            energy = db.value(Tags.Battery.STORED_ENERGY)
            current = db.value(Tags.Battery.CURRENT)
            voltage = db.value(Tags.Battery.VOLTAGE)
            soc = db.value(Tags.Battery.SOC)

            total_power += power
            total_energy += energy
            total_current += current
            total_voltage += voltage

            total_soc += soc


        self.db.set(
            Tags.Battery.SOC,
            total_soc / len(pcs_list),
        )

        self.db.set(
            Tags.Battery.STORED_ENERGY,
            total_energy,
        )

        self.db.set(
            Tags.Battery.POWER,
            total_power,
        )

        self.db.set(
            Tags.Battery.CURRENT,
            total_current,
        )

        self.db.set(
            Tags.Battery.VOLTAGE,
            total_voltage / len(pcs_list),
        )

        self.db.set(
            Tags.PCS.ACTIVE_POWER_OUTPUT,
            total_power,
        )