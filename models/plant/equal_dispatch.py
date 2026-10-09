from commands.command_target import CommandTarget
from commands.factory import CommandFactory
from models.plant.dispatch_strategy import DispatchStrategy
from state.tags import Tags


class EqualDispatchStrategy(DispatchStrategy):

    def dispatch(
        self,
        plant_context,
        pcs_contexts,
    ):

        if not pcs_contexts:
            # print("No Context PPC")
            if(
                plant_context.database.value(
                    Tags.EMS.START
                )
            ):
                # if plant_context.database.value(
                #     Tags.Fault.ACTIVE
                # ):
                #     print("Fault Found ")
                #     return
                print("Starting ALL PCS")
                for pcs in plant_context.simulator.pcs():
                    if pcs.database.value(
                        Tags.Fault.ACTIVE
                    ):
                        print("Fault Found ")
                        return
                    self.register_pcs_command(pcs, Tags.EMS.START)
                    
            return

        if(
            plant_context.database.value(
                Tags.EMS.START
            ) == 0
        ):
            print("PPC is Closed !!")
            for pcs in pcs_contexts:
                self.register_pcs_command(pcs, Tags.EMS.STOP)
            
        reference = plant_context.database.value(
            Tags.EMS.ACTIVE_POWER_COMMAND
        )

        # print("PPC Reference: ", reference)

        share = reference / len(pcs_contexts)

        for pcs in pcs_contexts:

            pcs.command.set_active_power(
                share
            )

    def register_pcs_command(self, pcs, tag: str):
        command = CommandFactory.create(
            tag,
            1,
        )

        if command is not None:

            pcs.command_manager.submit(
                CommandTarget.PCS,
                command,
            )

        print(f"{tag} PCS: {pcs.id}")