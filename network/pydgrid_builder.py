from pydgrid.pydgrid import grid

import numpy as np


class PyDGridBuilder:

    def __init__(self):

        self.network = grid()

    def build_data(self, topology):

        return {

            "buses": self.build_buses(topology),

            "grid_formers": self.build_grid(topology),

            "transformers": self.build_transformers(topology),

            "lines": self.build_lines(topology),

            "loads": self.build_loads(topology),

            "grid_feeders": self.build_grid_feeders(topology),

            # "bess_vsc": self.build_converters(topology),

            # "pv_vsc": self.build_pv(topology),

            "line_codes": self.build_line_codes(topology),

            "shunts": self.build_shunts(topology),
        }

    def build_buses(self, topology):

        buses = []

        utility = topology["plant"]["utility"]

        buses.append({
            "bus": utility["bus"],
            "U_kV": utility["voltage_kv"],
            "N_nodes": 3,
            "pos_x": 0,
            "pos_y": 0,
            "units": "m",
        })

        for bus in topology["lv_buses"]:

            buses.append({
                "bus": bus["id"],
                "U_kV": bus["voltage_kv"],
                "N_nodes": 4,
                "pos_x": 0,
                "pos_y": 0,
                "units": "m",
            })

        return buses

    def build_transformers(self, topology):

        transformers = []

        for tx in topology["transformers"]:

            transformers.append({

                "bus_j": tx["hv_bus"],

                "bus_k": tx["lv_bus"],

                "S_n_kVA": tx["rating_kva"],

                "U_j_kV": tx["hv_kv"],

                "U_k_kV": tx["lv_kv"],

                "R_cc_pu": tx["impedance"]["r_pu"],

                "X_cc_pu": tx["impedance"]["x_pu"],

                "connection": tx["connection"],

                "conductors_j": 3,

                "conductors_k": 4,

                "bus_j_nodes": [1, 2, 3],

                "bus_k_nodes": [1, 2, 3, 4],
            })

        return transformers

    def build_grid(self, topology):

        utility = topology["plant"]["utility"]

        v_phase = utility["voltage_kv"] / np.sqrt(3)

        return [{
            "bus": utility["bus"],
            "bus_nodes": [1, 2, 3],
            "deg": [0, -120, -240],
            "kV": [float(v_phase)] * 3, #[4.04145, 4.04145, 4.04145]
        }]

    def build_lines(self, topology):

        lines = []

        for feeder in topology["feeders"]:

            lines.append({
                "bus_j": feeder["from"],
                "bus_k": feeder["to"],
                "code": feeder["id"],
                "m": feeder.get("length_m", 1.0),
                "type": "z",
                "bus_j_nodes": [1,2,3,4],
                "bus_k_nodes": [1,2,3,4],
            })

        return lines

    def build_converters(self, topology):

        converters = {}

        for pcs in topology["pcs"]:

            template = topology["templates"][pcs["template"]]

            converters[
                f"gfeeder.{pcs['bus']}"
            ] = {

                "ctrl_type": 12,

                "s_n_kVA":
                    template["rated_power_kw"],

                "V_dc":
                    template["converter"]["dc_voltage"],

                "R":
                    template["converter"]["filter"]["r"],

                "L":
                    template["converter"]["filter"]["l"],

                "C_ac":
                    template["converter"]["filter"]["c"],

                "soc_ini_kWh":
                    template["battery"]["initial_soc_percent"],

                "soc_max_kWh":
                    template["battery"]["capacity_kwh"],
            }

        return converters

    def build_grid_feeders(self, topology):

        feeders = []

        for pcs in topology.get("pcs", []):

            template = topology["templates"][pcs["template"]]
            p_kw = 0#template["rated_power_kw"]

            feeders.append(
                {
                    "bus": pcs["bus"],
                    "bus_nodes": [1,2,3,4],
                    "kW": [
                        p_kw/3,
                        p_kw/3,
                        p_kw/3,
                        0
                    ],
                    "kvar": [0,0,0,0],
                    "kA": [0,0,0,0],
                    "phi_deg": [0,0,0,0],
                    "code": pcs["id"]
                }
            )


        for pv in topology.get("pv", []):

            template = topology["templates"][pv["template"]]
            p_kw = 0#template["rated_power_kw"]

            feeders.append(
                {
                    "bus": pv["bus"],
                    "bus_nodes": [1,2,3,4],
                    "kW": [
                        p_kw/3,
                        p_kw/3,
                        p_kw/3,
                        0
                    ],
                    "kvar": [0,0,0,0],
                    "kA": [0,0,0,0],
                    "phi_deg": [0,0,0,0],
                    "code": pv["id"]
                }
            )

        return feeders

    def build_loads(self, topology):

        loads = []

        for load in topology["loads"]:

            loads.append(
                {
                    "bus": load["bus"],
                    "kVA": load["default_kw"],
                    "pf": load.get("pf", 1.0),
                    "type": "3P+N",
                    "bus_nodes": [1, 2, 3, 4],
                }
            )

        return loads

    def build_line_codes(self, topology):

        codes = {}

        for feeder in topology["feeders"]:

            cable = feeder["cable"]

            codes[feeder["id"]] = {

                "Rph": cable["r"],
                "Xph": cable["x"],
                "Rn": cable["r"],
                "Xn": cable["x"],

            }

        return codes

    def build_shunts(self, topology):

        shunts = []

        for tx in topology["transformers"]:

            if tx["connection"].startswith("Dyn"):

                shunts.append({

                    "bus": tx["lv_bus"],

                    "R": 0.001,

                    "X": 0.0,

                    "bus_nodes": [4, 0],

                })

        return shunts

    def build_pv(self, topology):

        pv = {}

        for plant in topology["pv"]:

            template = topology["templates"][plant["template"]]

            pv[
                f"gfeeder.{plant['bus']}"
            ] = {

                "ctrl_type":12,

                "s_n_kVA":
                    template["rated_power_kw"],

                "V_dc":1000,

                "R":0.0002,

                "L":0.001,

                "C_ac":1e-5,
            }

        return pv