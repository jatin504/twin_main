# class PlantValidator:

#     def validate(self, topology):

#         bus_names = {
#             bus.name
#             for bus in topology.buses
#         }

#         for line in topology.lines:

#             if line.from_bus not in bus_names:

#                 raise ValueError(
#                     f"Unknown bus {line.from_bus}"
#                 )

#             if line.to_bus not in bus_names:

#                 raise ValueError(
#                     f"Unknown bus {line.to_bus}"
#                 )

#         for transformer in topology.transformers:

#             if transformer.hv_bus not in bus_names:

#                 raise ValueError(
#                     f"Unknown bus {transformer.hv_bus}"
#                 )

#             if transformer.lv_bus not in bus_names:

#                 raise ValueError(
#                     f"Unknown bus {transformer.lv_bus}"
#                 )

#         converter_ids = {

#             c.id

#             for c in topology.converters

#         }
        
#         for feeder in topology.grid_feeders:

#             if feeder.converter not in converter_ids:

#                 raise ValueError(

#                     f"Unknown converter '{feeder.converter}'"

#                 )


class PlantValidator:

    def validate(self, topology):

        self.validate_buses(topology)

        self.validate_transformers(topology)

        self.validate_feeders(topology)

        self.validate_pcs(topology)

        self.validate_loads(topology)

    def validate_buses(self, topology):

        buses = {
            bus["id"]
            for bus in topology["lv_buses"]
        }

        if not buses:
            raise ValueError("No buses defined.")


    def validate_transformers(self, topology):

        buses = self.bus_lookup(topology)

        for tx in topology["transformers"]:

            if tx["hv_bus"] not in buses:
                raise ValueError(tx["hv_bus"])

            if tx["lv_bus"] not in buses:
                raise ValueError(tx["lv_bus"])

    def validate_feeders(self, topology):

        buses = self.bus_lookup(topology)

        for feeder in topology["feeders"]:

            if feeder["from"] not in buses:
                raise ValueError(
                    f"Unknown bus '{feeder['from']}'"
                )

            if feeder["to"] not in buses:
                raise ValueError(
                    f"Unknown bus '{feeder['to']}'"
                )


    def validate_pcs(self, topology):

        buses = self.bus_lookup(topology)

        ids = set()

        for pcs in topology["pcs"]:

            if pcs["id"] in ids:

                raise ValueError(
                    f"Duplicate PCS '{pcs['id']}'"
                )

            ids.add(pcs["id"])

            if pcs["bus"] not in buses:

                raise ValueError(
                    f"Unknown PCS bus '{pcs['bus']}'"
                )

    def bus_lookup(self, topology):

        buses = set()

        buses.update(
            bus["id"]
            for bus in topology["lv_buses"]
        )

        return buses

    def validate_loads(self, topology):

        buses = self.bus_lookup(topology)

        for load in topology["loads"]:

            bus = load["bus"]

            if bus not in buses:

                raise ValueError(
                    f"Unknown load bus '{bus}'"
                )

            if load["default_kw"] < 0:

                raise ValueError(
                    f"Load '{load['name']}' cannot be negative."
                )