from protocol.register_bank import RegisterBank
from protocol.write_source import WriteSource


class ModbusAdapter:
    """
    Adapter between RegisterBank and any Modbus implementation.

    This class hides the internal RegisterBank implementation from
    the Modbus server.
    """

    def __init__(self, sessions):
        self.sessions = sessions

        # self._session_lookup()

    # ------------------------------------------------------------------
    # Holding Registers
    # ------------------------------------------------------------------

    def read_holding(
        self,
        address: int,
        count: int = 1,
        unit_id: int = 1,
    ) -> list[int]:
        """
        Read Holding Registers.
        """
        return self.bank(unit_id).read_block(
            address,
            count,
        )

    def write_holding(
        self,
        address: int,
        value: int,
        unit_id: int,
    ) -> None:
        """
        Write Single Holding Registers.
        """
        self.bank(unit_id).write(
            address,
            value,
            source=WriteSource.MODBUS,
        )

    def write_multiple_holding(
        self,
        address: int,
        values: list[int],
        unit_id: int,
    ) -> None:
        """
        Write Multiple Holding Registers.
        """
        self.bank(unit_id).write_block(
            address,
            values,
            source=WriteSource.MODBUS,
        )

    # ------------------------------------------------------------------
    # Single Register helpers
    # ------------------------------------------------------------------

    def read_register(
        self,
        address: int,
        unit_id: int,
    ) -> int:

        return self.bank(unit_id).read(address)

    def write_register(
        self,
        address: int,
        value: int,
        unit_id: int,
    ) -> None:

        self.bank(unit_id).write(
            address,
            value,
        )


    # ------------------------------------------------------------------
    # Session Register Bank
    # ------------------------------------------------------------------


    def bank(
        self,
        slave_id,
    ):
        # try:

        #     return self.sessions_by_slave[slave_id].register_bank

        # except Exception as e:
            
        return self.search_session_bank(slave_id)

    def search_session_bank(
        self,
        slave_id,
    ):

        for session in self.sessions.values():

            if session.slave_id == slave_id:

                return session.register_bank

        raise ValueError(
            f"Unknown slave {slave_id}"
        )

    def _session_lookup(self):
        self.sessions_by_slave = {
            session.slave_id: session
            for session in self.sessions.values()
        }