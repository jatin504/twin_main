from common.constants import BASE_HV_VOLTAGE, BASE_LV_VOLTAGE
from common.enums import GridSource, PCSState
from state.tags import Tags


class NetworkManager:

    def __init__(
        self,
        backend,
        adapter,
        database,
        topology,
        plant_database,
    ):

        self.backend = backend

        self.adapter = adapter

        self.db = database

        self.plant_database = plant_database

        self.topology = topology

        # Latest voltage profile
        self.voltage_profile = {}

    def initialize(self):

        self.backend.initialize(self.topology, self.db)
        try:
            self.update_inputs()
            self.backend.solve()
            self.update_outputs()
            self.update_voltage_profile()
        except Exception:
            pass

    def update(self):

        #
        # 1. Push simulator values into the network
        #
        self.update_inputs()

        #
        # 2. Solve electrical network
        #
        self.backend.solve()

        #
        # 3. Read solved electrical quantities
        #
        self.update_outputs()

        # 4. Update voltage profile
        self.update_voltage_profile()


    def update_inputs(self):

        # 
        # Grid
        # 
        grid_available = self.db.value(
            Tags.Grid.AVAILABLE
        )

        self.backend.set_grid_available(
            grid_available
        )

        source = self.db.value(
            Tags.Grid.SOURCE
        )

        state = PCSState(
            self.db.value(Tags.PCS.STATE)
        )

        if state == PCSState.GRID_FORMING:
            self.db.set(
                Tags.Grid.SOURCE,
                GridSource.PCS.value
            )

        self.backend.select_source(
            source
        )

        #
        # Load
        #
        load = self.db.value(
            Tags.Network.LOAD_POWER
        )

        load_distribution = {
            "CHILLERS": 0.40,
            "COOLING_TOWER": 0.20,
            "EV_STACK": 0.25,
            "SERVICE_BLOCK": 0.15,
        }

        for load_id, percentage in load_distribution.items():
            self.backend.set_load_power(
                load_id,
                load * percentage,
            )
            if load_id == "CHILLERS":
                self.db.set(
                    Tags.Load.CHILLERS_POWER,
                    load * percentage,
                )
            if load_id == "COOLING_TOWER":
                self.db.set(
                    Tags.Load.COOLING_TOWER_POWER,
                    load * percentage,
                )
            if load_id == "EV_STACK":
                self.db.set(
                    Tags.Load.EV_STACK_POWER,
                    load * percentage,
                )
            
            if load_id == "SERVICE_BLOCK":
                self.db.set(
                    Tags.Load.SERVICE_BLOCK_POWER,
                    load * percentage,
                )

        
        #
        # PCS
        #
        # pcs_power = self.db.value(
        #     Tags.PCS.ACTIVE_POWER_OUTPUT
        # )


        for pcs in self.topology["pcs"]:

            # if pcs["id"] == "PCS1":

            db = self.plant_database.device(pcs["id"])

            pcs_power = db.value(
                Tags.PCS.ACTIVE_POWER_OUTPUT
            )

            self.backend.set_converter_power(
                pcs["id"],
                pcs_power,
            )

        self.backend.set_converter_power(
            "PV1",
            0,
        )
        # print("=" *70)
        # print("Load = ", load)
        # print("PCS Power = ", pcs_power)

    def update_outputs(self):

        # =========================================================
        # GRID
        # =========================================================

        self.db.set(
            Tags.Grid.VOLTAGE,
            float(self.backend.bus_voltage("GRID_33KV")/1000),
        )

        self.db.set(
            Tags.Grid.BUS_VOLTAGE_A,
            float(self.backend.bus_voltage("BUS_433_A")),
        )
        self.db.set(
            Tags.Grid.BUS_VOLTAGE_B,
            float(self.backend.bus_voltage("BUS_433_B")),
        )
        self.db.set(
            Tags.Grid.BUS_VOLTAGE_C,
            float(self.backend.bus_voltage("BUS_433_C")),
        )

        # print("BUS_433_A current = ", self.backend.bus_current("BUS_433_A"))
        # print("BUS_433_B current = ", self.backend.bus_current("BUS_433_B"))
        # print("BUS_433_C current = ", self.backend.bus_current("BUS_433_C"))

        self.db.set(
            Tags.Grid.FREQUENCY,
            self.backend.get_frequency(),
        )

        self.db.set(
            Tags.Grid.IMPORT_POWER,
            self.backend.grid_import(),
        )

        self.db.set(
            Tags.Grid.EXPORT_POWER,
            self.backend.grid_export(),
        )

        # =========================================================
        # Load Voltage Settigs
        # =========================================================

        load_voltage = float(self.backend.bus_voltage("LOAD_BUS"))
        self.db.set(
            Tags.Network.LOAD_VOLTAGE,
            load_voltage,
        )

        self.db.set(
            Tags.Load.CHILLERS_VOLTAGE,
            load_voltage,
        )
        self.db.set(
            Tags.Load.COOLING_TOWER_VOLTAGE,
            load_voltage,
        )
        self.db.set(
            Tags.Load.EV_STACK_VOLTAGE,
            load_voltage,
        )
        self.db.set(
            Tags.Load.SERVICE_BLOCK_VOLTAGE,
            load_voltage,
        )

        # =========================================================
        # PCS
        # =========================================================

        self.db.set(
            Tags.PCS.AC_VOLTAGE,
            float(self.backend.bus_voltage("PCS_BUS")),
        )

        for pcs in self.topology["pcs"]:

            db = self.plant_database.device(pcs["id"])

            db.set(
                Tags.PCS.AC_VOLTAGE,
                float(self.backend.bus_voltage("PCS_BUS")),
            )

        # =========================================================
        # NETWORK LOSSES
        # =========================================================

        self.db.set(
            Tags.Network.NETWORK_LOSSES,
            self.backend.network_losses(),
        )

        # =========================================================
        # NETWORK LOSSES
        # =========================================================

        self.db.set(
            Tags.Transformer.T1_LOADING,
            self.backend.transformer_loading(0),
        )
        self.db.set(
            Tags.Transformer.T2_LOADING,
            self.backend.transformer_loading(1),
        )
        self.db.set(
            Tags.Transformer.T3_LOADING,
            self.backend.transformer_loading(2),
        )

        self.db.set(
            Tags.Transformer.T1_LV_CURRENT,
            self.backend.transformer_current(0),
        )
        self.db.set(
            Tags.Transformer.T2_LV_CURRENT,
            self.backend.transformer_current(1),
        )
        self.db.set(
            Tags.Transformer.T3_LV_CURRENT,
            self.backend.transformer_current(2),
        )

        print("T1 Current = ", self.backend.transformer_current(0))
        print("T2 Current = ", self.backend.transformer_current(1))
        print("T3 Current = ", self.backend.transformer_current(2))


    def update_voltage_profile(self):

        print(
            ">>> update_voltage_profile CALLED"
        )

        # =========================================================
        # ALL MAIN BUSES
        # =========================================================

        buses = [
            "GRID_33KV",

            "BUS_433_A",
            "BUS_433_B",
            "BUS_433_C",

            "PCS_BUS",
            "PV_BUS",

            "LOAD_BUS",

            # "CHILLER_BUS",
            # "COOLING_TOWER_BUS",
            # "EV_STACK_BUS",
            # "SERVICE_BLOCK_BUS",
        ]

        profile = {}

        for bus in buses:

            voltage = self.backend.bus_voltage(bus)

            try:
                va = abs(voltage.v_ag)
                vb = abs(voltage.v_bg)
                vc = abs(voltage.v_cg)

                avg_voltage = (
                    va + vb + vc
                ) / 3

            except AttributeError:
                avg_voltage = float(voltage)

            # =====================================================
            # BASE VOLTAGE
            # =====================================================

            if bus == "GRID_33KV":

                base_voltage = BASE_HV_VOLTAGE

            else:

                base_voltage = BASE_LV_VOLTAGE

            # =====================================================
            # PER UNIT VOLTAGE
            # =====================================================

            profile[bus] = (
                avg_voltage / base_voltage
            )

        self.voltage_profile = profile


        # print(
        #     "VOLTAGE PROFILE:",
        #     self.voltage_profile
        # )