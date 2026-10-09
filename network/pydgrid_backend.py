import numpy as np
from common.enums import GridSource
from network.pydgrid_builder import PyDGridBuilder
from state.tags import Tags
import math


class PyDGridBackend:

    def __init__(self):

        self.grid = None

        self.data = None

        self.topology = None

        self.converter_lookup = {}

        self.bus_lookup = {}

        self.load_lookup = {}
        self.generator_lookup = {}


        self.current_load_kw = {}
        self.current_generation_kw = {}

        self.bus_nodes = {}


    def initialize(
        self,
        topology,
        database
    ):

        self.topology = topology

        self.db = database

        builder = PyDGridBuilder()

        self.grid = builder.network

        self.data = builder.build_data(
            self.topology,
        )

        # print("Topology: ", self.topology)
        print("Built Data: ", self.data)

        self.grid.read(
            self.data,
        )

        # Enable VSC control
        for i in range(self.grid.N_gfeeds):
            self.grid.gfeed_ctrl_type[i] = 12

        print("\n========== BEFORE PF ==========")
        for f in self.data["grid_feeders"]:    
            print(        f["code"],        "BUS=", f["bus"],        "kW=", f["kW"],        "kvar=", f["kvar"]    )
        
        self.grid.pf()
        print("\n========== AFTER PF ==========")
        for f in self.data["grid_feeders"]:    
            print(        f["code"],        "BUS=", f["bus"],        "kW=", f["kW"],        "kvar=", f["kvar"]    )

        assert self.grid is not None

        assert self.grid.N_gfeeds == len(
            self.data["grid_feeders"]
        )

        self._build_lookup_tables()

        self._build_node_lookup()

        self.diagnostics()
    
    # Inputs

    def set_generator_power(self,name,p_kw):

        self.set_converter_power(
            name,
            p_kw
        )

    # def set_load_power(self, name, kw):

    #     if name not in self.load_lookup:
    #         raise ValueError(
    #             f"Unknown load {name}"
    #         )

    #     index = self.load_lookup[name]

    #     p_phase = kw * 1000 / 3


    #     self.grid.params_pf.pq_3pn[index,0,:] = [
    #         -p_phase,
    #         -p_phase,
    #         -p_phase
    #     ]

    def set_load_power(self, name, kw, kvar=0):
        if name not in self.load_lookup:
            raise ValueError(f"Unknown load {name}")

        index = self.load_lookup[name]

        load = self.data["loads"][index]

        s = math.sqrt(kw**2 + kvar**2)
        pf = 1.0 if s == 0 else kw / s

        load["kVA"] = s
        load["pf"] = pf

    def set_converter_power(self, name, kw, kvar=0):
        # Find the feeder by its code
        feeder = next(
            f for f in self.data["grid_feeders"]
            if f["code"] == name
        )

        # Balanced three-phase power (per phase)
        p_phase = kw / 3.0
        q_phase = kvar / 3.0

        feeder["kW"] = [p_phase, p_phase, p_phase, 0]
        feeder["kvar"] = [q_phase, q_phase, q_phase, 0]
        # print(f"Set converter {name} power: {kw} kW, {kvar} kvar")
        # print(f"Feeder {name} kW: {feeder['kW']}, kvar: {feeder['kvar']}")
        

    def set_grid_available(self, available: bool):

        self.grid_enabled = available

    # Solve

    def solve(self):

        # print(
        #     "Converter references:",
        #     self.grid.params_pf.gfeed_p_ref
        # )
        self.grid.read(
            self.data,
        )

        self.grid.pf()

        # print("CTRL")
        # print(self.grid.gfeed_ctrl_type)

        # print("REF")
        # print(self.grid.gfeed_p_ref)

        # print("CURRENT")
        # print(self.grid.gfeed_currents)

        # print("POWER")
        # print(self.grid.gfeed_powers)

        # self.diagnostics()

        return True

    def islanded_solver(self):

        voltage = self.db.value(
            Tags.PCS.AC_VOLTAGE
        )

        frequency = self.db.value(
            Tags.PCS.FREQUENCY
        )

        self.last_voltage = voltage

        self.last_frequency = frequency


    def select_source(self, source):

        self.source = source

    # Outputs
    def bus_voltage(self, bus):
        phase = self.bus_phase_voltages(bus)
        return np.mean(phase) * np.sqrt(3)

    def bus_phase_voltages(self, bus):

        indices = self.node_lookup[bus]


        voltages = []

        # print(f"\n{bus}")
        for i in indices[:3]:

            v = self.grid.V_node[i][0]

            # print(
            #     self.grid.nodes[i],
            #     abs(v),
            #     v,
            # )

            voltages.append(abs(v))

        return voltages

    def bus_phase_currents(self, bus):

        indices = self.node_lookup[bus]

        currents = []

        for i in indices[:3]:
            I = self.grid.I_node[i][0]
            currents.append(abs(I))

        return currents


    def bus_current(self, bus):

        phase = self.bus_phase_currents(bus)

        return np.mean(phase)


    def transformer_loading(self, transformer_index=0):
        trafo = self.grid.transformers[transformer_index]

        # Transformer ratings
        S_rated_kVA = trafo['S_n_kVA']
        V_lv_kV = trafo['U_k_kV']
        V_hv_kV = trafo['U_j_kV']

        # Currents from transformer results
        I_lv = np.array([
            trafo['i_2a_m'],
            trafo['i_2b_m'],
            trafo['i_2c_m']
        ])

        I_hv = np.array([
            trafo['i_1a_m'],
            trafo['i_1b_m'],
            trafo['i_1c_m']
        ])

        # Average phase current
        I_lv_avg = np.mean(I_lv)
        I_hv_avg = np.mean(I_hv)

        # Apparent power
        S_lv_kVA = np.sqrt(3) * V_lv_kV * I_lv_avg

        # Loading
        loading_percent = (S_lv_kVA / S_rated_kVA) * 100

        # Rated currents
        I_lv_rated = S_rated_kVA / (np.sqrt(3)*V_lv_kV)
        I_hv_rated = S_rated_kVA / (np.sqrt(3)*V_hv_kV)

        # Voltage current unbalance
        current_unbalance = (
            (np.max(I_lv)-np.min(I_lv)) / np.mean(I_lv)
        )*100

        # return {
        #     "S_rated_kVA": S_rated_kVA,
        #     "S_actual_kVA": S_lv_kVA,
        #     "loading_percent": loading_percent,
        #     "LV_current_A": I_lv_avg,
        #     "HV_current_A": I_hv_avg,
        #     "LV_rated_current_A": I_lv_rated,
        #     "HV_rated_current_A": I_hv_rated,
        #     "current_unbalance_percent": current_unbalance,
        #     "neutral_current_A": trafo['i_2n_m']
        # }
        # print("Transformer:", self.grid.transformers)
        # print("Transformer:", transformer_index)
        # print("S_n_kVA:", S_rated_kVA)
        # print("U_k_kV:", V_lv_kV)
        # print("U_j_kV:", V_hv_kV)
        # print("I_lv:", I_lv)
        # print("I_lv_avg:", I_lv_avg)
        # print("I_hv:", I_hv)
        # print("I_hv_avg:", I_hv_avg)

        return loading_percent

    def transformer_current(self, transformer_index=0):
        trafo = self.grid.transformers[transformer_index]

        # Transformer ratings
        S_rated_kVA = trafo['S_n_kVA']
        V_lv_kV = trafo['U_k_kV']
        V_hv_kV = trafo['U_j_kV']

        # Currents from transformer results
        I_lv = np.array([
            trafo['i_2a_m'],
            trafo['i_2b_m'],
            trafo['i_2c_m']
        ])

        I_hv = np.array([
            trafo['i_1a_m'],
            trafo['i_1b_m'],
            trafo['i_1c_m']
        ])

        # Average phase current
        I_lv_avg = np.mean(I_lv)
        I_hv_avg = np.mean(I_hv)

        return I_lv_avg

    def grid_power(self):

        return self.node_power(
            "GRID_33KV"
        )

    def grid_import(self):

        S = self.grid_power()

        P = S.real / 1000


        return max(P,0)
    
    def grid_export(self):

        S = self.grid_power()

        P = S.real /1000


        return max(-P,0)

    def network_losses(self):

        grid_p = self.grid_power().real / 1000.0

        # -------------------------
        # LOAD
        # -------------------------
        load_p = 0.0

        for load in self.data["loads"]:
            pf = load.get("pf", 1.0)
            load_p += load["kVA"] * pf

        # -------------------------
        # GENERATION
        # -------------------------
        pcs_p = 0.0
        pv_p = 0.0

        for feeder in self.data["grid_feeders"]:

            p_kw = sum(feeder["kW"])

            if feeder["code"].startswith("PCS"):
                pcs_p += p_kw

            elif feeder["code"].startswith("PV"):
                pv_p += p_kw

        generation_p = pcs_p + pv_p

        # -------------------------
        # POWER BALANCE
        # -------------------------
        losses = grid_p + generation_p - load_p

        # print("\n========== POWER BALANCE ==========")
        # print(f"GRID        = {grid_p:.2f} kW")
        # print(f"PCS         = {pcs_p:.2f} kW")
        # print(f"PV          = {pv_p:.2f} kW")
        # print(f"GENERATION  = {generation_p:.2f} kW")
        # print(f"LOAD        = {load_p:.2f} kW")
        # print(f"LOSSES      = {losses:.2f} kW")

        return losses


    def line_current(self,line):

        index = None

        for i,l in enumerate(self.data["lines"]):

            if l["code"] == line:
                index=i


        if index is None:
            raise ValueError(line)


        return self.grid.I_lines[index]

    def get_frequency(self):
        return self.grid.Freq

    def _build_node_lookup(self):

        self.node_lookup = {}

        for index, name in enumerate(self.grid.nodes):

            bus = name.split(".")[0]

            self.node_lookup.setdefault(
                bus,
                []
            ).append(index)

    def _build_lookup_tables(self):

        self.converter_lookup = {}
        self.load_lookup = {
            "PLANT_LOAD":0
        }
        self.generator_lookup = {}
        self.bus_lookup = {}
        self.bus_nodes = {}

        self.current_load_kw = {}
        self.current_generation_kw = {}


        #
        # Grid feeders (PCS + PV)
        #

        for index, feeder in enumerate(self.data["grid_feeders"]):

            self.converter_lookup[
                feeder["code"]
            ] = index



        #
        # Loads
        #

        for index, load in enumerate(self.data["loads"]):

            name = self.topology["loads"][index]["id"]

            self.load_lookup[name]=index


            # by bus
            self.load_lookup[
                load["bus"]
            ] = index


            self.current_load_kw[
                load["bus"]
            ] = load["kVA"]



        #
        # BESS PCS
        #

        for pcs in self.topology.get("pcs", []):

            self.generator_lookup[
                pcs["id"]
            ] = pcs


            self.current_generation_kw[
                pcs["bus"]
            ] = 0.0



        #
        # PV
        #

        for pv in self.topology.get("pv", []):

            self.generator_lookup[
                pv["id"]
            ] = pv


            self.current_generation_kw[
                pv["bus"]
            ] = 0.0



        #
        # Bus nodes
        #

        for line in self.data["lines"]:

            self.bus_nodes[
                line["bus_j"]
            ] = line["bus_j_nodes"]

            self.bus_nodes[
                line["bus_k"]
            ] = line["bus_k_nodes"]


        for tx in self.data["transformers"]:

            self.bus_nodes[
                tx["bus_j"]
            ] = tx["bus_j_nodes"]

            self.bus_nodes[
                tx["bus_k"]
            ] = tx["bus_k_nodes"]

    def node_power(self, node_prefix):

        S = 0 + 0j

        for name, V, I in zip(
            self.grid.nodes,
            self.grid.V_node.flatten(),
            self.grid.I_node.flatten()
        ):
            if name.startswith(node_prefix):
                S += V * np.conj(I)

        return S
    
    def diagnostics(self):

        print("=" * 70)

        # print(self.grid.__dict__.keys())

        # print(np.shape(self.grid.transformers))
        # print("transformer :",self.grid.transformers)

        # print("PyDGrid Diagnostics")

        # print()
        # print(self.converter_lookup)
        # print(self.grid.gfeed_id)

        # print("=== RES ===")
        # print(self.grid.res)

        print("=== Voltage Results ===")
        print(self.grid.V_results)

        # print("=== Current Results ===")
        # print(self.grid.I_results)

        # print("=== Grid Feeder Results ===")
        # print(self.grid.gfeed_powers)
        # print(self.grid.gformer_i_abcn)
        # print(self.grid.gformer_v_abcn)

        # print("Line Currents")
        # print(self.grid.I_lines)

        idx = 0

        for bus in self.data["buses"]:

            print(f"\n{bus['bus']}")

            for node in range(bus["N_nodes"]):

                v = self.grid.V_node[idx][0]

                print(
                    f"  Node {node+1}: "
                    f"{abs(v):8.2f} V   "
                    f"{np.angle(v, deg=True):7.2f}°"
                )

                idx += 1

        V = np.array(self.grid.gformer_v_abcn)
        I = np.array(self.grid.gformer_i_abcn)

        S = np.sum(V * np.conj(I))

        # print(f"P = {S.real/1000:.2f} kW")
        # print(f"Q = {S.imag/1000:.2f} kVAr")

        S_grid = self.node_power("GRID_11KV")
        S_load = self.node_power("LOAD_BUS")
        S_pcs  = self.node_power("PCS_BUS")
        S_pv   = self.node_power("PV_BUS")

        # print(f"Grid : {S_grid.real/1000:.1f} kW")
        # print(f"Load : {S_load.real/1000:.1f} kW")
        # print(f"PCS  : {S_pcs.real/1000:.1f} kW")
        # print(f"PV   : {S_pv.real/1000:.1f} kW")

        # print("Grid feeder powers:")
        # print(self.grid.gfeed_powers)

        # print("Grid feeder current:")
        # print(self.grid.gfeed_i_abcn)

        # print("Grid former current:")
        # print(self.grid.gformer_i_abcn)

        # print("Power-flow summary:")
        # print(self.grid.res)

        # print(
        #     "Buses:",
        #     len(self.data["buses"])
        # )

        # print(
        #     "Lines:",
        #     len(self.data["lines"])
        # )

        # print(
        #     "Transformers:",
        #     len(self.data["transformers"])
        # )

        # print(
        #     "Converters:",
        #     len(self.topology["converters"])
        # )

        # print(
        #     "Grid Feeders:",
        #     self.grid.N_gfeeds
        # )

        # print(
        #     "Params DF:",
        #     self.grid.params_pf
        # )

        print("=" * 70)