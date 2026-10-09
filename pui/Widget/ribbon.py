from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
)


class RibbonItem(QWidget):

    def __init__(
        self,
        icon,
        title,
        value,
        sub="",
        valueColor="#111827",
    ):
        super().__init__()

        self.setMinimumWidth(185)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(10)

        self.iconLbl = QLabel(icon)
        self.iconLbl.setAlignment(Qt.AlignCenter)
        self.iconLbl.setFixedWidth(34)
        self.iconLbl.setStyleSheet("""
        border:none;
        font-size:22px;
        """)

        root.addWidget(self.iconLbl)

        text = QVBoxLayout()
        text.setSpacing(0)

        self.titleLbl = QLabel(title)
        self.titleLbl.setStyleSheet("""
        border:none;
        color:#6B7280;
        font-size:10px;
        """)

        self.valueLbl = QLabel(value)
        self.valueLbl.setStyleSheet(f"""
        border:none;
        color:{valueColor};
        font-size:18px;
        font-weight:700;
        """)

        self.subLbl = QLabel(sub)
        self.subLbl.setStyleSheet("""
        border:none;
        color:#64748B;
        font-size:10px;
        """)

        text.addWidget(self.titleLbl)
        text.addWidget(self.valueLbl)
        text.addWidget(self.subLbl)

        root.addLayout(text)


class Divider(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(1)

        self.setStyleSheet("""
        background:#D7DEE8;
        """)


class Ribbon(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(84)

        self.setStyleSheet("""
        QWidget{
            background:#FFFFFF;
        }
        """)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        # --------------------------------------------------
        # ITEMS
        # --------------------------------------------------

        self.total_load = RibbonItem(
            "🏭",
            "Total Load",
            "0.00 MW",
            "0.00 MVAr",
            "#111827",
        )

        self.solar_generation = RibbonItem(
            "☀",
            "Solar Generation",
            "0.00 MW",
            "0.00 MVAr",
            "#111827",
        )

        self.bess_power = RibbonItem(
            "🔋",
            "BESS Power (Total)",
            "0.00 MW",
            "(Idle)",
            "#16A34A",
        )

        self.grid_import = RibbonItem(
            "⚡",
            "Grid Import",
            "0.00 MW",
            "0.00 MVAr",
            "#111827",
        )

        self.system_losses = RibbonItem(
            "⚡",
            "System Losses",
            "0.00 MW",
            "0.00 %",
            "#111827",
        )

        self.bess_soc = RibbonItem(
            "🟢",
            "Total BESS SOC (Avg.)",
            "0 %",
            "",
            "#111827",
        )

        self.frequency = RibbonItem(
            "🌐",
            "Frequency",
            "0.00 Hz",
            "Voltage (PCC)   0.00 kV",
            "#111827",
        )

        items = [
            self.total_load,
            self.solar_generation,
            self.bess_power,
            self.grid_import,
            self.system_losses,
            self.bess_soc,
            self.frequency,
        ]

        for i, item in enumerate(items):

            layout.addWidget(item, 1)

            if i != len(items) - 1:
                layout.addWidget(Divider())

    # ======================================================
    # LIVE DATA UPDATE
    # ======================================================

    def update_data(
        self,
        grid_data,
        pcs_data,
    ):

        # --------------------------------------------------
        # GRID DATA
        # --------------------------------------------------

        load_power = grid_data.get(
            "load_power",
            0,
        )

        import_power = grid_data.get(
            "import_power",
            0,
        )

        frequency = grid_data.get(
            "frequency",
            0,
        )

        ac_voltage = grid_data.get(
            "ac_voltage",
            0,
        )

        losses = grid_data.get(
            "network_losses",
            0,
        )

        # --------------------------------------------------
        # BESS DATA
        # --------------------------------------------------

        total_bess_power = 0
        total_soc = 0

        if pcs_data:

            for pcs in pcs_data:

                total_bess_power += pcs.get(
                    "active_power",
                    0,
                )

                total_soc += pcs.get(
                    "soc",
                    0,
                )

            avg_soc = total_soc / len(pcs_data)

        else:

            avg_soc = 0

        # --------------------------------------------------
        # LOAD
        # Modbus value = kW
        # --------------------------------------------------

        self.total_load.valueLbl.setText(
            f"{load_power / 1000:.2f} MW"
        )

        # --------------------------------------------------
        # BESS POWER
        # Modbus value = kW
        # --------------------------------------------------

        bess_mw = total_bess_power / 1000

        self.bess_power.valueLbl.setText(
            f"{bess_mw:.2f} MW"
        )

        if bess_mw > 0:
            self.bess_power.subLbl.setText(
                "(Charging)"
            )
        elif bess_mw < 0:
            self.bess_power.subLbl.setText(
                "(Discharging)"
            )
        else:
            self.bess_power.subLbl.setText(
                "(Idle)"
            )

        # --------------------------------------------------
        # GRID IMPORT
        # Modbus value = kW
        # --------------------------------------------------

        self.grid_import.valueLbl.setText(
            f"{import_power / 1000:.2f} MW"
        )

        # --------------------------------------------------
        # SYSTEM LOSSES
        # --------------------------------------------------

        self.system_losses.valueLbl.setText(
            f"{losses / 1000:.2f} MW"
        )

        # --------------------------------------------------
        # BESS SOC
        # --------------------------------------------------

        self.bess_soc.valueLbl.setText(
            f"{avg_soc:.0f} %"
        )

        # --------------------------------------------------
        # FREQUENCY
        # --------------------------------------------------

        self.frequency.valueLbl.setText(
            f"{frequency:.2f} Hz"
        )

        # --------------------------------------------------
        # PCC VOLTAGE
        # --------------------------------------------------

        self.frequency.subLbl.setText(
            f"Voltage (PCC)   {ac_voltage / 100:.2f} kV"
        )