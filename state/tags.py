"""
Engineering Tag Definitions

This module contains every engineering variable
name used inside the simulator.

The simulator MUST never use raw strings.

Always use Tags.
"""

from __future__ import annotations


class Tags:

    class PCS:

        STATE = "PCS.State"

        STATE_ELAPSED = "PCS.StateElapsed"

        MODE = "PCS.Mode"

        ACTIVE_POWER_REFERENCE = "PCS.ActivePowerReference"

        ACTIVE_POWER_OUTPUT = "PCS.ActivePowerOutput"

        ACTIVE_POWER = "PCS.ActivePower"

        REACTIVE_POWER = "PCS.ReactivePower"

        APPARENT_POWER = "PCS.ApparentPower"

        POWER_FACTOR = "PCS.PowerFactor"

        DC_VOLTAGE = "PCS.DCVoltage"

        DC_CURRENT = "PCS.DCCurrent"

        AC_VOLTAGE = "PCS.ACVoltage"

        AC_CURRENT = "PCS.ACCurrent"

        FREQUENCY = "PCS.Frequency"

        EFFICIENCY = "PCS.Efficiency"

        AVAILABLE_POWER = "PCS.AvailablePower"

        START_COMMAND = "PCS.StartCommand"

        STOP_COMMAND = "PCS.StopCommand"

        RESET_COMMAND = "PCS.ResetCommand"

        ENABLE = "PCS.Enable"

        OPERATING_MODE = "PCS.OperatingMode"

    # ---------------------------------------------

    class Battery:

        #
        # State
        #

        SOC = "SOC"

        SOH = "SOH"

        READY = "Battery.Ready"

        FAULT = "Battery.Fault"

        CONTACTOR = "Battery.Contactor"

        # 
        # AH Capacity
        # 

        AH_CAPACITY = "Battery.AHCapacity"

        #
        # Energy
        #

        CAPACITY = "Battery.Capacity"

        AVAILABLE_ENERGY = "Battery.AvailableEnergy"

        STORED_ENERGY = "Battery.StoredEnergy"

        #
        # Electrical
        #

        VOLTAGE = "Battery.Voltage"

        CURRENT = "Battery.Current"

        POWER = "Battery.Power"

        TERMINAL_VOLTAGE = "Battery.TerminalVoltage"

        OCV = "Battery.OCV"

        DISCHARGE_AH = "Battery.DischargeAh"

        #
        # Limits
        #

        MAX_CHARGE_POWER = "Battery.MaxChargePower"

        MAX_DISCHARGE_POWER = "Battery.MaxDischargePower"

        #
        # Thermal
        #

        TEMPERATURE = "Battery.Temperature"

    # ---------------------------------------------

    class BMS:

        READY = "BMS.Ready"

        FAULT = "BMS.Fault"

        CHARGE_ENABLE = "BMS.ChargeEnable"

        DISCHARGE_ENABLE = "BMS.DischargeEnable"

        MAX_CHARGE_POWER = "BMS.MaxChargePower"

        MAX_DISCHARGE_POWER = "BMS.MaxDischargePower"
    
    # ---------------------------------------------

    class Grid:

        AVAILABLE = "Grid.Available"

        VOLTAGE = "Grid.Voltage"

        BUS_VOLTAGE_A = "Grid.BUS_A_Voltage"
        BUS_VOLTAGE_B = "Grid.BUS_B_Voltage"
        BUS_VOLTAGE_C = "Grid.BUS_C_Voltage"

        CURRENT = "Grid.Current"

        FREQUENCY = "Grid.Frequency"

        PHASE_ANGLE = "Grid.PhaseAngle"

        ROCOF = "Grid.ROCOF"

        SYNCHRONIZED = "Grid.Synchronized"

        PLL_LOCKED = "Grid.PLL_Locked"

        SYNC_PROGRESS = "Grid.SyncProgress"

        IMPORT_POWER = "Grid.ImportPower"

        EXPORT_POWER = "Grid.ExportPower"

        SOURCE = "Grid.Source"

    # ---------------------------------------------

    class GFM:

        DROOP_ENABLE = "GFM.DroopEnable"

        DROOP_GAIN = "GFM.DroopGain"

        NOMINAL_FREQUENCY = "GFM.DroopFrequency"

    # ---------------------------------------------

    class Network:

        GENERATION_POWER = "Network.GenerationPower"

        LOAD_POWER = "Network.LoadPower"
        
        LOAD_VOLTAGE = "Network.LoadVoltage"

        POWER_IMBALANCE = "Network.PowerImbalance"

        NETWORK_LOSSES = "Network.NetworkLoss"

    class Load:

        CHILLERS_POWER = "Load.ChillersPower"
        COOLING_TOWER_POWER = "Load.CoolingTowerPower"
        EV_STACK_POWER = "Load.EV_StackPower"
        SERVICE_BLOCK_POWER = "Load.ServiceBlockPower"

        CHILLERS_VOLTAGE = "Load.ChillersVoltage"
        COOLING_TOWER_VOLTAGE = "Load.CoolingTowerVoltage"
        EV_STACK_VOLTAGE = "Load.EV_StackVoltage"
        SERVICE_BLOCK_VOLTAGE = "Load.ServiceBlockVoltage"

    # ---------------------------------------------

    class Transformer:

        T1_LOADING = "Transformer.T1Loading"
        T2_LOADING = "Transformer.T2Loading"
        T3_LOADING = "Transformer.T3Loading"

        T1_LV_CURRENT = "Transformer.T1LVCurrent"
        T2_LV_CURRENT = "Transformer.T2LVCurrent"
        T3_LV_CURRENT = "Transformer.T3LVCurrent"

    # ---------------------------------------------

    class Thermal:

        IGBT = "Thermal.IGBT"

        REACTOR = "Thermal.Reactor"

        CABINET = "Thermal.Cabinet"

        AMBIENT = "Thermal.Ambient"

        COOLANT = "Thermal.Coolant"

    # ---------------------------------------------

    class Protection:

        ALARM = "Protection.Alarm"

        FAULT = "Protection.Fault"

        TRIP = "Protection.Trip"

        ESTOP = "Protection.EStop"

    # ---------------------------------------------

    class Fault:

        ACTIVE = "Fault.ACTIVE"
        
        CODE = "Fault.CODE"
        
        LEVEL = "Fault.LEVEL"
        
        OVERVOLTAGE = "Fault.OVERVOLTAGE"
        
        UNDERVOLTAGE = "Fault.UNDERVOLTAGE"
        
        OVERFREQUENCY = "Fault.OVERFREQUENCY"
        
        UNDERFREQUENCY = "Fault.UNDERFREQUENCY"
        
        GRID_LOSS = "Fault.GRID_LOSS"
        
        BMS = "Fault.BMS"
        
        EMERGENCY_STOP = "Fault.EMERGENCY_STOP"
        
        OVERTEMPERATURE = "Fault.OVERTEMPERATURE"
        

    # ---------------------------------------------

    class EMS:

        ACTIVE_POWER_COMMAND = "EMS.ActivePowerCommand"

        REACTIVE_POWER_COMMAND = "EMS.ReactivePowerCommand"

        POWER_FACTOR_COMMAND = "EMS.PowerFactorCommand"

        START = "EMS.Start"

        STOP = "EMS.Stop"

        RESET = "EMS.Reset"