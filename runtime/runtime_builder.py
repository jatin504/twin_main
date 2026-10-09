from runtime.model_factory import ModelFactory


class RuntimeBuilder:

    def build(
        self,
        simulator,
        topology,
    ):

        ModelFactory.register_global_models(
            simulator,
            context,
        )

        for pcs in topology["pcs"]:
            
            context = simulator.create_device(
                pcs["id"]
            )
    
            ModelFactory.register_pcs_models(
                simulator,
                context,
            )