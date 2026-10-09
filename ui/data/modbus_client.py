import socket
class ModbusClient:

    def __init__(
        self,
        host="127.0.0.1",
        port=5020,
        timeout=2.0,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.transaction_id = 0
    
    # Transaction ID

    def _next_transaction_id(self):

        self.transaction_id += 1

        if self.transaction_id > 65535:
            self.transaction_id = 1

        return self.transaction_id
    
    # READ HOLDING REGISTERS - FUNCTION CODE 03

    def read_holding_registers(
        self,
        unit_id,
        address,
        quantity,
    ):

        transaction_id = self._next_transaction_id()

        
        # MBAP Header
        

        transaction = transaction_id.to_bytes(
            2,
            "big",
        )

        protocol = (0).to_bytes(
            2,
            "big",
        )

        # Length:
        # Unit ID       = 1 byte
        # Function      = 1 byte
        # Address       = 2 bytes
        # Quantity      = 2 bytes
        #
        # Total = 6 bytes
        length = (6).to_bytes(
            2,
            "big",
        )

        unit = bytes([unit_id])

        # PDU
        
        # Function Code 03
        function = bytes([3])

        start = address.to_bytes(
            2,
            "big",
        )

        count = quantity.to_bytes(
            2,
            "big",
        )

        frame = (
            transaction
            + protocol
            + length
            + unit
            + function
            + start
            + count
        )

        # TCP Connection
        
        with socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout,
        ) as sock:

            sock.sendall(frame)

            response = sock.recv(1024)

        # Parse Response
        
        return self._parse_response(
            response,
            transaction_id,
        )
    
    # PARSE MODBUS RESPONSE

    def _parse_response(
        self,
        response,
        transaction_id,
    ):

        if len(response) < 9:

            raise ValueError(
                "Invalid Modbus response"
            )
        
        # Transaction ID

        response_transaction = int.from_bytes(
            response[0:2],
            "big",
        )

        if response_transaction != transaction_id:

            raise ValueError(
                "Transaction ID mismatch"
            )
    
        # Unit ID
    
        unit_id = response[6]

        # Function Code
        
        function = response[7]

        # Function 03 = Read Holding Registers
        if function != 3:

            raise ValueError(
                f"Unsupported function: {function}"
            )

        # Byte Count
        
        byte_count = response[8]

        data = response[
            9:9 + byte_count
        ]

        if len(data) != byte_count:

            raise ValueError(
                "Incomplete Modbus response"
            )

        # Convert Registers
        
        values = []

        for i in range(
            0,
            byte_count,
            2,
        ):

            value = int.from_bytes(
                data[i:i + 2],
                byteorder="big",
                signed=False,
            )

            values.append(value)

        return {
            "unit_id": unit_id,
            "values": values,
        }

    
    # READ PCS DATA
    

    def read_pcs(
        self,
        unit_id,
    ):

        response = self.read_holding_registers(
            unit_id=unit_id,
            address=1,
            quantity=8,
        )

        values = response["values"]

        if len(values) != 8:

            raise ValueError(
                f"Expected 8 registers, got {len(values)}"
            )

        
        # Register 1
        # Tags.Battery.SOC
        # UINT16
        

        soc = values[0]

        
        # Registers 2-6
        #
        # All are INT16 according to small_mapping.py
        #
        # 2 = STORED_ENERGY
        # 3 = POWER
        # 4 = VOLTAGE
        # 5 = CURRENT
        # 6 = ACTIVE_POWER_OUTPUT
        

        signed_values = []

        # Registers 2-6 are INT16 and need signed conversion
        for value in values[1:6]:

            if value >= 32768:

                value -= 65536

            signed_values.append(value)

        # Registers 7 and 8 are UINT16 (frequency, grid voltage)
        frequency = values[6]
        grid_voltage = values[7]

        try:
            temperature_response = self.read_holding_registers(
                unit_id=unit_id,
                address=25,
                quantity=1,
            )
            temperature_value = temperature_response["values"][0]
            if temperature_value >= 32768:
                temperature_value -= 65536
        except Exception:
            temperature_value = 0

        return {
            "soc": soc,
            "stored_energy": signed_values[0],
            "battery_power": signed_values[1],
            "battery_voltage": signed_values[2],
            "battery_current": signed_values[3],
            "active_power": signed_values[4],
            "frequency": frequency,
            "grid_voltage": grid_voltage,
            "temperature": temperature_value,
            "battery_temperature": temperature_value,
        }

    # READ GRID DATA

    def read_grid(self):

        response = self.read_holding_registers(
            unit_id=50,
            address=1,
            quantity=24,
        )

        values = response["values"]

        if len(values) != 24:
            raise ValueError(
                f"Expected 24 registers, got {len(values)}"
            )

        # ------------------------------------------------------
        # Register 7 -> Tags.Grid.FREQUENCY
        # ------------------------------------------------------

        frequency = values[6]

        # ------------------------------------------------------
        # Register 8 -> Tags.PCS.AC_VOLTAGE
        # ------------------------------------------------------

        ac_voltage = values[7]

        # ------------------------------------------------------
        # Register 19 -> Tags.Grid.VOLTAGE
        # ------------------------------------------------------

        grid_voltage = values[18]

        if grid_voltage >= 32768:
            grid_voltage -= 65536

        # ------------------------------------------------------
        # Register 20 -> Tags.Grid.IMPORT_POWER
        # ------------------------------------------------------

        import_power = values[19]

        if import_power >= 32768:
            import_power -= 65536

        # ------------------------------------------------------
        # Register 21 -> Tags.Grid.EXPORT_POWER
        # ------------------------------------------------------

        export_power = values[20]

        if export_power >= 32768:
            export_power -= 65536

        # ------------------------------------------------------
        # Register 17 -> Tags.Network.LOAD_POWER
        # ------------------------------------------------------

        load_power = values[16]

        if load_power >= 32768:
            load_power -= 65536

        # ------------------------------------------------------
        # Register 18 -> Tags.Network.NETWORK_LOSSES
        # ------------------------------------------------------

        network_losses = values[17]

        if network_losses >= 32768:
            network_losses -= 65536

        # ------------------------------------------------------
        # Register 22 -> Tags.Grid.CURRENT
        # ------------------------------------------------------

        current = values[21]

        if current >= 32768:
            current -= 65536

        # ------------------------------------------------------
        # Register 23 -> Tags.Transformer.LOADING
        # ------------------------------------------------------

        loading = values[22]

        if loading >= 32768:
            loading -= 65536

        # ------------------------------------------------------
        # Register 24 -> Tags.Fault.CODE
        # ------------------------------------------------------

        fault_code = values[23]

        if fault_code >= 32768:
            fault_code -= 65536

        return {
            "frequency": frequency,
            "ac_voltage": ac_voltage,
            "grid_voltage": grid_voltage,
            "import_power": import_power,
            "export_power": export_power,
            "load_power": load_power,
            "network_losses": network_losses,
            "current": current,
            "loading": loading,
            "fault_code": fault_code,
        }