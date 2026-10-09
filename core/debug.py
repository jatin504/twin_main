

from state.tags import Tags


class DebugConsole:
    """
        Denug console called in Grid Following Controller
    """

    def __init__(self, db):
        self.db = db

    def dump(self):

        print("=" * 70)

        print(f"State        : {self.db.value(Tags.PCS.STATE)}")
        print(f"Mode         : {self.db.value(Tags.PCS.OPERATING_MODE)}")

        print(f"Grid Avail   : {self.db.value(Tags.Grid.AVAILABLE)}")
        print(f"PLL Locked   : {self.db.value(Tags.Grid.PLL_LOCKED)}")
        print(f"Synchronized : {self.db.value(Tags.Grid.SYNCHRONIZED)}")
        print(f"Sync %       : {self.db.value(Tags.Grid.SYNC_PROGRESS):6.1f}")

        print(f"EMS Cmd      : {self.db.value(Tags.EMS.ACTIVE_POWER_COMMAND):8.1f}")
        print(f"PCS Ref      : {self.db.value(Tags.PCS.ACTIVE_POWER_REFERENCE):8.1f}")
        print(f"PCS Out      : {self.db.value(Tags.PCS.ACTIVE_POWER_OUTPUT):8.1f}")

        print(f"SoC %     : {self.db.value(Tags.Battery.SOC):8.1f}")
        print(f"Energy Stored      : {self.db.value(Tags.Battery.STORED_ENERGY):8.1f}")
        print(f"Voltage  : {self.db.value(Tags.Battery.VOLTAGE):8.3f}")
        print(f"Current  : {self.db.value(Tags.Battery.CURRENT):8.3f}")
        print(f"Power  : {self.db.value(Tags.Battery.POWER):8.3f}")
        print(f"Terminal Voltage  : {self.db.value(Tags.Battery.TERMINAL_VOLTAGE):8.3f}")
        print(f"OCV  : {self.db.value(Tags.Battery.OCV):8.3f}")
        print(f"Battery Temp  : {self.db.value(Tags.Battery.TEMPERATURE):8.3f}")
        print(f"Discharge Ah  : {self.db.value(Tags.Battery.DISCHARGE_AH):8.3f}")

        print(f"Generation : {self.db.value(Tags.Network.GENERATION_POWER):8.1f}")

        print(f"Load       : {self.db.value(Tags.Network.LOAD_POWER):8.1f}")

        print(f"Imbalance  : {self.db.value(Tags.Network.POWER_IMBALANCE):8.1f}")

        print(f"Frequency  : {self.db.value(Tags.Grid.FREQUENCY):8.3f}")

        print(f"Grid Voltage  : {self.db.value(Tags.PCS.AC_VOLTAGE):8.3f}")
        print(f"IMPORT_POWER  : {self.db.value(Tags.Grid.IMPORT_POWER):8.3f}")
        print(f"EXPORT_POWER  : {self.db.value(Tags.Grid.EXPORT_POWER):8.3f}")

        print(f"NETWORK_LOSSES  : {self.db.value(Tags.Network.NETWORK_LOSSES):8.3f}")


        print(f"Fault Active: {self.db.value(Tags.Fault.ACTIVE)}")
        print(f"Fault CODE: {self.db.value(Tags.Fault.CODE)}")

        print("=" * 70)