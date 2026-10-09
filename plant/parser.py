# import yaml

# from plant.topology import *


# class PlantParser:

#     def load(self, filename):

#         with open(filename, "r") as f:

#             data = yaml.safe_load(f)

#         info = data["plant"]

#         topology = PlantTopology(

#             name=info["name"],

#             base_voltage=info["base_voltage"],

#             base_frequency=info["base_frequency"],

#             converters = [

#                 Converter(**item)

#                 for item in data.get(
#                     "converters",
#                     [],
#                 )

#             ],

#             grid_feeders = [

#                 GridFeeder(**item)

#                 for item in data.get(
#                     "grid_feeders",
#                     [],
#                 )

#             ],
#         )

#         for bus in data["buses"]:

#             topology.buses.append(
#                 Bus(**bus)
#             )

#         for transformer in data["transformers"]:

#             topology.transformers.append(
#                 Transformer(**transformer)
#             )

#         for line in data["lines"]:

#             topology.lines.append(
#                 Line(**line)
#             )

#         for generator in data["generators"]:

#             topology.generators.append(
#                 Generator(**generator)
#             )

#         for load in data["loads"]:

#             topology.loads.append(
#                 Load(**load)
#             )

#         return topology


# plant/parser.py

from pathlib import Path
import yaml


class PlantParser:

    def load(self, filename):

        with open(filename, "r") as f:
            data = yaml.safe_load(f)

        topology = {
            "plant": data.get("plant", {}),
            "switchyard": data.get("switchyard", {}),
            "transformers": data.get("transformers", []),
            "hv_buses": data.get("hv_buses", []),
            "lv_buses": data.get("lv_buses", []),
            "feeders": data.get("feeders", []),
            "pcs": data.get("pcs", []),
            "loads": data.get("loads", []),
            "pv": data.get("pv", []),
            "diesel": data.get("diesel", []),
            "svg": data.get("svg", []),
            "filters": data.get("filters", []),
            "protection": data.get("protection", []),
            "templates": data.get("templates", {}),
        }

        return topology