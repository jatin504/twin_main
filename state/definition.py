from common.constants import (
    DEFAULT_BATTERY_CURRENT_A,
    DEFAULT_BATTERY_TEMPERATURE_C,
    DEFAULT_BATTERY_VOLTAGE_V,
    DEFAULT_CAPACITY_KWH,
    DEFAULT_GRID_AVAILABLE,
    DEFAULT_GRID_FREQUENCY,
    DEFAULT_GRID_VOLTAGE,
    DEFAULT_MAX_CHARGE_POWER_KW,
    DEFAULT_MAX_DISCHARGE_POWER_KW,
    DEFAULT_SOC,
    PACK_CAPACITY_AH,
)
from common.enums import FaultCode, GridSource, PCSState
from models.operating_mode import OperatingMode
from state.database import StateDatabase
from state.quality import Quality
from state.variable import Variable, VariableMetadata

from state.tags import Tags


from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class VariableDefinition:
    name: str
    datatype: type
    default: Any
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    writable: bool = False
    description: str = ""
    enable_store: bool = False

VARIABLE_DEFINITIONS = [

    # Aggregate PV generation; shared by the network, ribbon and history graph.
    VariableDefinition(
        name=Tags.SOLAR.PV_POWER,
        datatype=float,
        default=0.0,
        unit="kW",
        minimum=0.0,
        enable_store=True,
        description="Total three-phase solar active power supplied to the network",
    ),

    # Battery

    VariableDefinition(
        name=Tags.Battery.SOC,
        datatype=float,
        default=DEFAULT_SOC,
        unit="%",
        minimum=0,
        maximum=100,
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Battery.SOH,
        datatype=float,
        default=100.0,
        unit="%",
    ),

    VariableDefinition(
        name=Tags.Battery.READY,
        datatype=bool,
        default=True,
    ),

    VariableDefinition(
        name=Tags.Battery.FAULT,
        datatype=bool,
        default=False,
    ),

    VariableDefinition(
        name=Tags.Battery.CONTACTOR,
        datatype=bool,
        default=True,
    ),

    VariableDefinition(
        name=Tags.Battery.CAPACITY,
        datatype=float,
        default=DEFAULT_CAPACITY_KWH,
        unit="kWh",
    ),

    VariableDefinition(
        name=Tags.Battery.STORED_ENERGY,
        datatype=float,
        default=5250.0,
        unit="kWh",
    ),

    VariableDefinition(
        name=Tags.Battery.AH_CAPACITY,
        datatype=float,
        default=PACK_CAPACITY_AH,
        unit="Ah",
    ),

    VariableDefinition(
        name=Tags.Battery.AVAILABLE_ENERGY,
        datatype=float,
        default=5250.0,
        unit="kWh",
    ),

    VariableDefinition(
        name=Tags.Battery.VOLTAGE,
        datatype=float,
        default=DEFAULT_BATTERY_VOLTAGE_V,
        unit="V",
    ),

    VariableDefinition(
        name=Tags.Battery.CURRENT,
        datatype=float,
        default=DEFAULT_BATTERY_CURRENT_A,
        unit="A",
    ),

    VariableDefinition(
        name=Tags.Battery.POWER,
        datatype=float,
        default=0.0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Battery.TERMINAL_VOLTAGE,
        datatype=float,
        default=0.0,
        unit="V",
    ),

    VariableDefinition(
        name=Tags.Battery.OCV,
        datatype=float,
        default=0.0,
        unit="V",
    ),

    VariableDefinition(
        name=Tags.Battery.DISCHARGE_AH,
        datatype=float,
        default=0.0,
        unit="Ah",
    ),

    VariableDefinition(
        name=Tags.Battery.MAX_CHARGE_POWER,
        datatype=float,
        default=DEFAULT_MAX_CHARGE_POWER_KW,
        unit="kW",
    ),

    VariableDefinition(
        name=Tags.Battery.MAX_DISCHARGE_POWER,
        datatype=float,
        default=DEFAULT_MAX_DISCHARGE_POWER_KW,
        unit="kW",
    ),

    VariableDefinition(
        name=Tags.Battery.TEMPERATURE,
        datatype=float,
        default=DEFAULT_BATTERY_TEMPERATURE_C,
        unit="°C",
    ),

    # BMS

    VariableDefinition(
        name=Tags.BMS.READY,
        datatype=bool,
        default=True,
        writable=False,
    ),

    VariableDefinition(
        name=Tags.BMS.FAULT,
        datatype=bool,
        default=False,
        writable=False,
    ),

    VariableDefinition(
        name=Tags.BMS.CHARGE_ENABLE,
        datatype=bool,
        default=True,
    ),

    VariableDefinition(
        name=Tags.BMS.DISCHARGE_ENABLE,
        datatype=bool,
        default=True,
    ),

    VariableDefinition(
        name=Tags.BMS.MAX_CHARGE_POWER,
        datatype=float,
        default=DEFAULT_MAX_CHARGE_POWER_KW,
        unit="kW",
    ),

    VariableDefinition(
        name=Tags.BMS.MAX_DISCHARGE_POWER,
        datatype=float,
        default=DEFAULT_MAX_DISCHARGE_POWER_KW,
        unit="kW",
    ),


    # Grid

    VariableDefinition(
        name=Tags.Grid.AVAILABLE,
        datatype=bool,
        default=DEFAULT_GRID_AVAILABLE,
    ),

    VariableDefinition(
        name=Tags.Grid.VOLTAGE,
        datatype=float,
        default=DEFAULT_GRID_VOLTAGE,
        unit="kV",
        enable_store=True,
    ),
    
    VariableDefinition(
        name=Tags.Grid.BUS_VOLTAGE_A,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.BUS_VOLTAGE_B,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.BUS_VOLTAGE_C,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.CURRENT,
        datatype=float,
        default=0.0,
        unit="A",
    ),

    VariableDefinition(
        name=Tags.Grid.FREQUENCY,
        datatype=float,
        default=DEFAULT_GRID_FREQUENCY,
        unit="Hz",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.PHASE_ANGLE,
        datatype=float,
        default=0.0,
        unit="deg",
    ),

    VariableDefinition(
        name=Tags.Grid.ROCOF,
        datatype=float,
        default=0.0,
        unit="Hz/s",
    ),

    VariableDefinition(
        name=Tags.Grid.PLL_LOCKED,
        datatype=bool,
        default=False,
    ),

    VariableDefinition(
        name=Tags.Grid.SYNCHRONIZED,
        datatype=bool,
        default=False,
    ),

    VariableDefinition(
        name=Tags.Grid.SYNC_PROGRESS,
        datatype=float,
        default=0.0,
    ),

    VariableDefinition(
        name=Tags.Grid.IMPORT_POWER,
        datatype=float,
        default=0.0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.EXPORT_POWER,
        datatype=float,
        default=0.0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Grid.SOURCE,
        datatype=float,
        default=GridSource.UTILITY.value,
        unit="",
    ),

    # GFM

    VariableDefinition(
        name=Tags.GFM.DROOP_ENABLE,
        datatype=bool,
        default=True,
    ),

    VariableDefinition(
        name=Tags.GFM.DROOP_GAIN,
        datatype=float,
        default=500.0,
        unit="kW/Hz"
    ),

    VariableDefinition(
        name=Tags.GFM.NOMINAL_FREQUENCY,
        datatype=float,
        default=DEFAULT_GRID_FREQUENCY,
    ),

    # Netwrok

    VariableDefinition(
        name=Tags.Network.GENERATION_POWER,
        datatype=float,
        default=0.0,
    ),

    VariableDefinition(
        name=Tags.Network.LOAD_POWER,
        datatype=float,
        default=0.0,
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Network.LOAD_VOLTAGE,
        datatype=float,
        default=0.0,
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Network.POWER_IMBALANCE,
        datatype=float,
        default=0.0,
    ),

    VariableDefinition(
        name=Tags.Network.NETWORK_LOSSES,
        datatype=float,
        default=0.0,
        unit="kW",
    ),

    # Load

    VariableDefinition(
        name=Tags.Load.CHILLERS_VOLTAGE,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),
    
    VariableDefinition(
        name=Tags.Load.COOLING_TOWER_VOLTAGE,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Load.EV_STACK_VOLTAGE,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Load.SERVICE_BLOCK_VOLTAGE,
        datatype=float,
        default=0,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Load.CHILLERS_POWER,
        datatype=float,
        default=0,
        unit="kW",
        enable_store=True,
    ),
    
    VariableDefinition(
        name=Tags.Load.COOLING_TOWER_POWER,
        datatype=float,
        default=0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Load.EV_STACK_POWER,
        datatype=float,
        default=0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.Load.SERVICE_BLOCK_POWER,
        datatype=float,
        default=0,
        unit="kW",
        enable_store=True,
    ),

    # Transformer

    VariableDefinition(
        name=Tags.Transformer.T1_LOADING,
        datatype=float,
        default=0.0,
        unit="%"
    ),
    VariableDefinition(
        name=Tags.Transformer.T2_LOADING,
        datatype=float,
        default=0.0,
        unit="%"
    ),
    VariableDefinition(
        name=Tags.Transformer.T3_LOADING,
        datatype=float,
        default=0.0,
        unit="%"
    ),

    VariableDefinition(
        name=Tags.Transformer.T1_LV_CURRENT,
        datatype=float,
        default=0.0,
        unit="%"
    ),
    VariableDefinition(
        name=Tags.Transformer.T2_LV_CURRENT,
        datatype=float,
        default=0.0,
        unit="%"
    ),
    VariableDefinition(
        name=Tags.Transformer.T3_LV_CURRENT,
        datatype=float,
        default=0.0,
        unit="%"
    ),

    # PCS

    VariableDefinition(
        name=Tags.PCS.ACTIVE_POWER_REFERENCE,
        datatype=float,
        default=0.0,
        unit="kW",
    ),

    VariableDefinition(
        name=Tags.PCS.ACTIVE_POWER_OUTPUT,
        datatype=float,
        default=0.0,
        unit="kW",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.PCS.ACTIVE_POWER,
        datatype=float,
        default=0.0,
        unit="kW",
    ),

    VariableDefinition(
        name=Tags.PCS.AC_VOLTAGE,
        datatype=float,
        default=DEFAULT_GRID_VOLTAGE,
        unit="V",
        enable_store=True,
    ),

    VariableDefinition(
        name=Tags.PCS.STATE,
        datatype=int,
        default=PCSState.OFF.value,
    ),

    VariableDefinition(
        name=Tags.PCS.STATE_ELAPSED,
        datatype=float,
        default=0.0,
        unit="s",
    ),

    VariableDefinition(
        name=Tags.PCS.OPERATING_MODE,
        datatype=float,
        default=OperatingMode.OFF,
        unit="",
    ),

    # Fault

    VariableDefinition(
        name=Tags.Fault.ACTIVE,
        datatype=bool,
        default=False,
        unit="",
    ),

    VariableDefinition(
        name=Tags.Fault.CODE,
        datatype=float,
        default=FaultCode.NONE,
        unit="",
    ),

    # EMS

    VariableDefinition(
        name=Tags.EMS.START,
        datatype=bool,
        default=False,
        writable=True,
    ),

    VariableDefinition(
        name=Tags.EMS.STOP,
        datatype=bool,
        default=False,
        writable=True,
    ),

    VariableDefinition(
        name=Tags.EMS.RESET,
        datatype=bool,
        default=False,
        writable=True,
    ),

    VariableDefinition(
        name=Tags.EMS.ACTIVE_POWER_COMMAND,
        datatype=float,
        default=0.0,
        unit="kW",
        writable=True,
    ),

    VariableDefinition(
        name=Tags.EMS.REACTIVE_POWER_COMMAND,
        datatype=float,
        default=0.0,
        unit="kVar",
        writable=True,
    ),

    VariableDefinition(
        name=Tags.EMS.POWER_FACTOR_COMMAND,
        datatype=float,
        default=1.0,
        writable=True,
    ),
]


def populate_database(database: StateDatabase, initial_values: dict[str, Any] | None = None,) -> None:
    """
    Create all engineering variables in the database.
    """

    initial_values = initial_values or {}

    for definition in VARIABLE_DEFINITIONS:

        metadata = VariableMetadata(
            name=definition.name,
            datatype=definition.datatype,
            unit=definition.unit,
            writable=definition.writable,
            minimum=definition.minimum,
            maximum=definition.maximum,
            description=definition.description,
            enable_store=definition.enable_store,
        )

        database.add(
            Variable(
                metadata=metadata,
                quality=(Quality.NOT_INITIALIZED if definition.name == Tags.Battery.STORED_ENERGY
                         else Quality.GOOD),
                initial_value=initial_values.get(
                    definition.name,
                    definition.default,
                ),
            )
        )