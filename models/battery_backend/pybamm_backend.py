import time

from models.base import BaseSimulationModel
from models.battery_backend.battery_state import BatteryState
from state.tags import Tags

import pybamm

import numpy as np


# Delta terra mi2 config
# nominal AH = 314
# "Number of cells connected in series to make a battery": 416        ====>  52 cell * 8 modules = 416 cells
# "Number of electrodes connected in parallel to make a cell": 12,    ====> 2 cell * 6 strings = 12 electrodes


# Cell / Pack configuration  ===> hoymiles 5MWh
SERIES_CELLS = 416
PARALLEL_CELLS = 2
# PARALLEL_STRINGS = 6  ===> hoymiles
PARALLEL_STRINGS = 5   #===> Delta terra mi2 ==== rack = 5

TOTAL_PARALLEL = PARALLEL_CELLS * PARALLEL_STRINGS

Nominal_AH = 314.0
PACK_CAPACITY_KWH = 4179.96       # \[ E_{pack}=V_{pack}\times Ah_{pack} \]     Vpack = 166.4 V  ===>   PACK_CAPACITY_AH * 1331.2 -> (3.2*416)
PACK_CAPACITY_AH = TOTAL_PARALLEL * Nominal_AH     # \[ C_{pack}=C_{cell}\times N_P \]    ===== TOTAL_PARALLEL * Nominal_AH = 12 * 314 = 3768 Ah

MAX_POWER_KW = 1004#2508.0      based on c-rate

class PyBaMMBackend(BaseSimulationModel):

    def __init__(self, context, pcs_initial_condition):

        super().__init__(context)

        self.pcs_initial_condition = pcs_initial_condition

    def initialize(self):

        self.state = BatteryState()

        self.build_model()

        self.initial_soc = (
            self.db.value(Tags.Battery.SOC) / 100.0
        )

        self.soc_fraction = self.initial_soc

        # print("initial soc: ", self.initial_soc)

        self.battery_simulation = pybamm.Simulation(
            self.model,
            parameter_values=self.parameters,
        )

        self.solution = self.battery_simulation.solve(
            [0, 1],
            initial_soc=self.initial_soc,
            inputs={
                "Current [A]": 0.0,
            },
        )

        self.current_time = 1.0

    def build_model(self):

        self.model = pybamm.lithium_ion.SPMe(
            options={
                "thermal": "lumped",
            }
        )

        self.parameters = pybamm.ParameterValues("Prada2013")
        chen = pybamm.ParameterValues("Chen2020")

        # Copy only the missing parameters

        for key in chen.keys():

            if key not in self.parameters.keys():

                self.parameters.update(

                    {key: chen[key]},

                    check_already_exists=False

                )

        thermal_params = {
            # -----------------------------
            # Current collector geometry
            # -----------------------------
            "Negative current collector thickness [m]": 12e-6,
            "Positive current collector thickness [m]": 16e-6,
            # -----------------------------
            # Current collector density
            # -----------------------------
            "Negative current collector density [kg.m-3]": 8960,
            "Positive current collector density [kg.m-3]": 2700,
            # -----------------------------
            # Specific heat capacity
            # -----------------------------
            "Negative current collector specific heat capacity [J.kg-1.K-1]": 385,
            "Positive current collector specific heat capacity [J.kg-1.K-1]": 897,
            # -----------------------------
            # Thermal conductivity
            # -----------------------------
            "Negative current collector thermal conductivity [W.m-1.K-1]": 401,
            "Positive current collector thermal conductivity [W.m-1.K-1]": 237,

            "Negative current collector conductivity [S.m-1]": 5.96e7,   # Copper
            "Positive current collector conductivity [S.m-1]": 3.55e7,   # Aluminium
            # -----------------------------
            # Ambient conditions
            # -----------------------------
            "Reference temperature [K]": 298.15,
            "Ambient temperature [K]": self.pcs_initial_condition.get("Initial_Temperature_K", 298.15),
            "Initial temperature [K]": self.pcs_initial_condition.get("Initial_Temperature_K", 298.15),
            # -----------------------------
            # Heat transfer coefficients
            # -----------------------------
            "Negative current collector surface heat transfer coefficient [W.m-2.K-1]": 10,
            "Positive current collector surface heat transfer coefficient [W.m-2.K-1]": 10,
            "Edge heat transfer coefficient [W.m-2.K-1]": 5,
            "Total heat transfer coefficient [W.m-2.K-1]": 10.0,
            # -----------------------------
            # Effective cell properties
            # -----------------------------
            "Cell cooling surface area [m2]": 0.42,
            "Cell volume [m3]": 0.0028,
            # -----------------------------
            # Contact resistance
            # -----------------------------
            "Contact resistance [Ohm]": 0.0,
        }
        self.parameters.update(thermal_params, check_already_exists=False)

        self.parameters.update({
            "Current function [A]": pybamm.InputParameter("Current [A]")
        })

        #
        # Chen2020 cell nominal capacity
        #
        current = 314.0  # 3C
        old_width = self.parameters["Electrode width [m]"]
        self.parameters.update({
            "Nominal cell capacity [A.h]": current,
            "Electrode width [m]": old_width * current / 5,
            "Number of cells connected in series to make a battery": 416,  # 416 in hoymiles
            "Number of electrodes connected in parallel to make a cell": 12,    # 12 in hoymiles
        })
        self.cell_capacity_ah = self.parameters[
            "Nominal cell capacity [A.h]"
        ]

        # print(self.parameters["Nominal cell capacity [A.h]"])
        # print(self.parameters["Lower voltage cut-off [V]"])
        # print(self.parameters["Number of cells connected in series to make a battery"])
        # print(self.parameters["Number of electrodes connected in parallel to make a cell"])

    def update(self, dt):

        wall_start = time.perf_counter()

        #
        # Pack power command (kW)
        # +ve = discharge
        # -ve = charge
        #
        pack_power_kw = self.db.value(
            Tags.PCS.ACTIVE_POWER_OUTPUT
        )

        #
        # Clamp to inverter rating
        #
        pack_power_kw = max(
            -MAX_POWER_KW,
            min(MAX_POWER_KW, pack_power_kw),
        )

        #
        # Previous pack voltage
        #
        if self.state.terminal_voltage > 0:

            pack_voltage = self.state.terminal_voltage

        else:

            #
            # Initial nominal pack voltage
            #
            pack_voltage = self.state.terminal_voltage#3.2 * 416

        #
        # Convert pack power to C-rate
        #
        # 5016 kWh container
        #
        c_rate = pack_power_kw / PACK_CAPACITY_AH


        #
        # Convert C-rate to PyBaMM cell current
        #
        # Chen2020 cell = 5 Ah
        #
        cell_current = (
            c_rate *
            self.cell_capacity_ah
        )


        #
        # Limit to ±0.5C
        #
        max_cell_current = (
            0.5 *
            self.cell_capacity_ah
        )

        cell_current = max(
            -max_cell_current,
            min(
                max_cell_current,
                cell_current,
            ),
        )

        #
        # Advance simulation
        #
        old_time = self.current_time
        self.current_time += dt

        self.solution = self.battery_simulation.step(
            dt=dt,
            inputs={
                "Current [A]": cell_current,
            },
        )


        # print("termination: ",self.solution.termination)

        #
        # -------------------------
        # Cell quantities
        # -------------------------
        #
        cell_voltage = float(
            self.solution[
                "Battery voltage [V]"
            ].data[-1]
        )

        cell_ocv = float(
            self.solution[
                "Battery open-circuit voltage [V]"
            ].data[-1]
        )

        cell_current = float(
            self.solution[
                "Current [A]"
            ].data[-1]
        )

        cell_temperature = float(
            np.mean(
                self.solution[
                    "Cell temperature [C]"
                ].data[-1]
            )
        )

        discharged_cell_ah = float(
            self.solution[
                "Discharge capacity [A.h]"
            ].data[-1]
        )

        #
        # Cell SOC
        #
        # soc = self.initial_soc * 100 - (
        #     discharged_cell_ah / self.cell_capacity_ah * 100
        # )

        soc_delta = (
            cell_current * dt
            / (3600.0 * self.cell_capacity_ah)
        )
        
        self.soc_fraction -= soc_delta
        
        self.soc_fraction = max(
            0.0,
            min(1.0, self.soc_fraction)
        )
        
        soc = self.soc_fraction * 100.0

        # print(cell_ocv)
        # print(cell_voltage)
        # print(cell_current)

        #
        # -------------------------
        # Pack scaling
        # -------------------------
        #
        pack_voltage = cell_voltage #* 416.0

        pack_ocv = cell_ocv #* 416.0

        pack_current = cell_current# * 12.0

        pack_discharge_ah = (
            discharged_cell_ah #* 12.0
        )

        stored_energy = (
            PACK_CAPACITY_KWH *
            soc /
            100.0
        )

        stored_capacity_ah = (
            PACK_CAPACITY_AH *
            soc /
            100.0
        )

        #
        # Update state
        #
        self.state.soc = soc

        self.state.voltage = pack_voltage

        self.state.terminal_voltage = pack_voltage

        self.state.ocv = pack_ocv

        self.state.current = pack_current

        #
        # Keep EMS command as pack power
        #
        self.state.power = pack_power_kw

        self.state.temperature = cell_temperature

        self.state.discharge_ah = pack_discharge_ah

        self.state.capacity = PACK_CAPACITY_KWH

        self.state.stored_energy = stored_energy

        self.state.stored_capacity_ah = stored_capacity_ah

        self.state.available_energy = stored_energy

        #
        # Publish
        #
        self.publish_state()

        # -------------------------------------------------- 
        # Measure execution time 
        # -------------------------------------------------- 
        elapsed = time.perf_counter() - wall_start 
        # print( 
        #     f"update() execution time: " 
        #     f"{elapsed * 1000:.3f} ms " 
        #     f"(scheduled period: {dt * 1000:.1f} ms)" 
        # )
        
    def publish_state(self):

        s = self.state

        self.db.set(Tags.Battery.SOC, s.soc)
        self.db.set(Tags.Battery.POWER, s.power)
        self.db.set(Tags.Battery.CURRENT, s.current)

        self.db.set(
            Tags.Battery.VOLTAGE,
            s.terminal_voltage,
        )

        self.db.set(
            Tags.Battery.TERMINAL_VOLTAGE,
            s.terminal_voltage,
        )

        self.db.set(
            Tags.Battery.OCV,
            s.ocv,
        )

        self.db.set(
            Tags.Battery.TEMPERATURE,
            s.temperature,
        )

        self.db.set(
            Tags.Battery.DISCHARGE_AH,
            s.discharge_ah,
        )

        self.db.set(
            Tags.Battery.STORED_ENERGY,
            s.stored_energy,
        )

        self.db.set(
            Tags.Battery.AH_CAPACITY,
            s.stored_capacity_ah,
        )