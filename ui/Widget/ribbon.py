from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
)



# RIBBON ITEM


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

        self.setMinimumWidth(170)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(8)

        # --------------------------------------------------
        # ICON
        # --------------------------------------------------

        self.iconLbl = QLabel(icon)

        self.iconLbl.setAlignment(Qt.AlignCenter)
        self.iconLbl.setFixedWidth(30)

        self.iconLbl.setStyleSheet("""
            QLabel {
                border: none;
                font-size: 21px;
                background: transparent;
            }
        """)

        root.addWidget(self.iconLbl)

        # --------------------------------------------------
        # TEXT AREA
        # --------------------------------------------------

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)

        # TITLE
        self.titleLbl = QLabel(title)

        self.titleLbl.setStyleSheet("""
            QLabel {
                border: none;
                color: #6B7280;
                font-size: 10px;
                font-weight: 500;
                background: transparent;
            }
        """)

        # MAIN VALUE
        self.valueLbl = QLabel(value)

        self.valueLbl.setStyleSheet(f"""
            QLabel {{
                border: none;
                color: {valueColor};
                font-size: 17px;
                font-weight: 700;
                background: transparent;
            }}
        """)

        # SUB VALUE
        self.subLbl = QLabel(sub)

        self.subLbl.setStyleSheet("""
            QLabel {
                border: none;
                color: #64748B;
                font-size: 9px;
                background: transparent;
            }
        """)

        text.addWidget(self.titleLbl)
        text.addWidget(self.valueLbl)
        text.addWidget(self.subLbl)

        root.addLayout(text)


# DIVIDER

class Divider(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(1)

        self.setStyleSheet("""
            QFrame {
                background: #D7DEE8;
                border: none;
            }
        """)
        
# TOP RIBBON


class Ribbon(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(84)

        self.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
            }
        """)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        
        # 1. TOTAL LOAD
        

        self.total_load = RibbonItem(
            "🏭",
            "Total Load",
            "0.00 MW",
            "0.00 MVAr",
            "#111827",
        )

        
        # 2. SOLAR ENERGY
        

        self.solar_energy = RibbonItem(
            "☀",
            "Solar Energy",
            "0.00 MW",
            "0.00 MVAr",
            "#111827",
        )

        
        # 3. BESS CHARGE / DISCHARGE
        

        self.bess_charge_discharge = RibbonItem(
            "🔋",
            "BESS Charge / Discharge",
            "0.00 MW",
            "Charge  0.00 | Discharge  0.00",
            "#16A34A",
        )

        
        # 4. BESS USABLE / AVAILABLE
        

        self.bess_usable_available = RibbonItem(
            "🔋",
            "BESS Usable / Available",
            "0.00 MWh",
            "Available  0.00 MWh",
            "#111827",
        )

        
        # 5. SOC CHANGE
        

        self.soc_change = RibbonItem(
            "◉",
            "SOC Change",
            "0.00 %",
            "Δ SOC",
            "#111827",
        )

        
        # 6. GRID IMPORT / EXPORT
        

        self.grid_import_export = RibbonItem(
            "⚡",
            "Grid Import / Export",
            "0.00 MW",
            "Export  0.00 MW",
            "#111827",
        )

        
        # 7. SYSTEM LOSS
        

        self.system_loss = RibbonItem(
            "⚡",
            "System Loss",
            "0.00 MW",
            "0.00 %",
            "#111827",
        )

        
        # ADD ITEMS
        

        items = [
            self.total_load,
            self.solar_energy,
            self.bess_charge_discharge,
            self.bess_usable_available,
            self.soc_change,
            self.grid_import_export,
            self.system_loss,
        ]

        for i, item in enumerate(items):

            layout.addWidget(item, 1)

            if i != len(items) - 1:
                layout.addWidget(Divider())



    # LIVE DATA UPDATE
    

    def update_data(
        self,
        grid_data,
        pcs_data,
        solar_data=None,
        schedule_data=None,
    ):

        if grid_data is None:
            grid_data = {}

        if pcs_data is None:
            pcs_data = []

        if solar_data is None:
            solar_data = {}

        if schedule_data is None:
            schedule_data = {}

        
        # GRID DATA
        

        load_power = grid_data.get(
            "load_power",
            0,
        )

        import_power = grid_data.get(
            "import_power",
            0,
        )

        export_power = grid_data.get(
            "export_power",
            0,
        )

        network_losses = grid_data.get(
            "network_losses",
            0,
        )

        
        # SOLAR
        

        solar_power = solar_data.get(
            "active_power",
            solar_data.get(
                "solar_power",
                0,
            ),
        )

        
        # BESS
        

        total_discharge = 0

        total_usable_energy = 0
        total_available_energy = 0

        total_soc = 0

        for pcs in pcs_data:

            battery_power = pcs.get(
                "battery_power",
                0,
            )

            soc = pcs.get(
                "soc",
                0,
            )

            stored_energy_mwh = pcs.get(
                "stored_energy",
                0,
            ) / 1000

            # ------------------------------------------------
            # CHARGE / DISCHARGE
            # ------------------------------------------------

            if battery_power > 0:
                total_discharge += battery_power

            # ------------------------------------------------
            # ENERGY
            # ------------------------------------------------

            total_available_energy += stored_energy_mwh
            total_usable_energy += stored_energy_mwh * 0.80

            # ------------------------------------------------
            # SOC
            # ------------------------------------------------

            total_soc += soc

        
        # AVERAGE SOC
        

        if pcs_data:

            avg_soc = total_soc / len(pcs_data)

        else:

            avg_soc = 0

        
        # SOC CHANGE
        

        schedule_events = schedule_data.get(
            "schedule",
            [],
        )
        active_soc = avg_soc
        soc_delta = 0.0
        if isinstance(schedule_events, list) and schedule_events:
            active_event = schedule_events[-1]
            if isinstance(active_event, dict):
                active_soc = active_event.get(
                    "soc_percent",
                    avg_soc,
                )

            if len(schedule_events) >= 2:
                previous_event = schedule_events[-2]
                if (
                    isinstance(active_event, dict)
                    and isinstance(previous_event, dict)
                ):
                    active_soc = active_event.get(
                        "soc_percent",
                        avg_soc,
                    )
                    previous_soc = previous_event.get(
                        "soc_percent",
                        0.0,
                    )
                    soc_delta = active_soc - previous_soc

        
        # TOTAL LOAD
        # kW -> MW
        

        self.total_load.valueLbl.setText(
            f"{load_power / 1000:.3f} MW"
        )

        
        # SOLAR ENERGY
        

        self.solar_energy.valueLbl.setText(
            f"{solar_power / 1000:.2f} MW"
        )

        self.solar_energy.subLbl.setText(
            "Solar Generation"
        )

        
        # BESS CHARGE / DISCHARGE
        

        discharge_mw = total_discharge / 1000
        charge_energy_mwh = schedule_data.get(
            "target_charge_energy_mwh",
            0,
        )
        discharge_energy_mwh = schedule_data.get(
            "target_discharge_energy_mwh",
            0,
        )

        self.bess_charge_discharge.valueLbl.setText(
            f"{discharge_mw:.2f} MW"
        )

        self.bess_charge_discharge.subLbl.setText(
            f"Charge  {charge_energy_mwh:.2f} MWh | "
            f"Discharge  {discharge_energy_mwh:.2f} MWh"
        )

        
        # BESS USABLE / AVAILABLE
        

        self.bess_usable_available.valueLbl.setText(
            f"{total_usable_energy:.2f} MWh"
        )

        self.bess_usable_available.subLbl.setText(
            f"Available  {total_available_energy:.2f} MWh"
        )

        
        # SOC CHANGE
        

        sign = "+" if soc_delta >= 0 else ""

        self.soc_change.valueLbl.setText(
            f"{sign}{soc_delta:.2f} %"
        )

        self.soc_change.subLbl.setText(
            f"SOC {active_soc:.2f} %"
        )

        
        # GRID IMPORT / EXPORT
        

        import_mw = import_power / 1000
        export_mw = export_power / 1000

        self.grid_import_export.valueLbl.setText(
            f"{import_mw:.2f} MW"
        )

        self.grid_import_export.subLbl.setText(
            f"Export  {export_mw:.2f} MW"
        )

        
        # SYSTEM LOSS
        

        loss_mw = network_losses / 1000

        self.system_loss.valueLbl.setText(
            f"{loss_mw:.2f} MW"
        )

        load_mw = load_power / 1000

        if load_mw > 0:

            loss_percent = (
                loss_mw / load_mw
            ) * 100

        else:

            loss_percent = 0

        self.system_loss.subLbl.setText(
            f"{loss_percent:.2f} %"
        )