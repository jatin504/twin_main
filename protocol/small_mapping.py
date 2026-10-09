from protocol.mapping import RegisterMapping
from protocol.datatypes import RegisterType
from state.tags import Tags

MAPPINGS = [

    RegisterMapping(
        tag=Tags.Battery.SOC,
        address=1,
        datatype=RegisterType.UINT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.Battery.STORED_ENERGY,
        address=2,
        datatype=RegisterType.INT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.Battery.POWER,
        address=3,
        datatype=RegisterType.INT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.Battery.VOLTAGE,
        address=4,
        datatype=RegisterType.INT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.Battery.CURRENT,
        address=5,
        datatype=RegisterType.INT16,
        scale=1,
    ),
    
    RegisterMapping(
        tag=Tags.PCS.ACTIVE_POWER_OUTPUT,
        address=6,
        datatype=RegisterType.INT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.Grid.FREQUENCY,
        address=7,
        datatype=RegisterType.UINT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.PCS.AC_VOLTAGE,
        address=8,
        datatype=RegisterType.UINT16,
        scale=1,
    ),

    RegisterMapping(
        tag=Tags.EMS.START,
        address=13,
        datatype=RegisterType.BOOL,
        writable=True,
    ),

    RegisterMapping(
        tag=Tags.EMS.STOP,
        address=14,
        datatype=RegisterType.BOOL,
        writable=True,
    ),

    RegisterMapping(
        tag=Tags.EMS.ACTIVE_POWER_COMMAND,
        address=15,
        datatype=RegisterType.INT16,
        scale=1.0,
        writable=True,
    ),

    RegisterMapping(
        tag=Tags.Grid.AVAILABLE,
        address=16,
        datatype=RegisterType.BOOL,
        scale=1,
        writable=True,
    ),

    RegisterMapping(
        tag=Tags.Network.LOAD_POWER,
        address=17,
        datatype=RegisterType.INT16,
        scale=1,
        writable=True,
    ),

    RegisterMapping(
        tag=Tags.Network.NETWORK_LOSSES,
        address=18,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Grid.VOLTAGE,
        address=19,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Grid.IMPORT_POWER,
        address=20,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Grid.EXPORT_POWER,
        address=21,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Grid.CURRENT,
        address=22,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Transformer.T1_LOADING,
        address=23,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Fault.CODE,
        address=24,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.BMS.CHARGE_ENABLE,
        address=25,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.BMS.DISCHARGE_ENABLE,
        address=26,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),

    RegisterMapping(
        tag=Tags.Battery.TEMPERATURE,
        address=27,
        datatype=RegisterType.INT16,
        scale=1,
        writable=False,
    ),
]