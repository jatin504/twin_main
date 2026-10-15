from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from ui.Widget.icons.solar_panel_icon import SolarPanelIcon


class SolarPlantWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(150, 70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon = SolarPanelIcon()
        layout.addWidget(icon)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(2)

        self.title_label = QLabel("SOLAR PLANT")
        self.title_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 9px;
                font-weight: 700;
                color: #2F3640;
            }
        """)

        self.kw_label = QLabel("2.15 MW")
        self.kw_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        self.kvar_label = QLabel("0.05 MVAr")
        self.kvar_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        self.pf_label = QLabel("PF 0.99 Lag")
        self.pf_label.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        right.addWidget(self.title_label)
        right.addWidget(self.kw_label)
        right.addWidget(self.kvar_label)
        right.addWidget(self.pf_label)

        layout.addLayout(right)

    def update_data(self, active_power_mw=None, reactive_power_mvar=None, power_factor=None):
        """Update solar plant live readings from mapped tags."""
        if active_power_mw is not None:
            self.kw_label.setText(f"{float(active_power_mw):.2f} MW")
        if reactive_power_mvar is not None:
            self.kvar_label.setText(f"{float(reactive_power_mvar):.2f} MVAr")
        if power_factor is not None:
            pf_val = float(power_factor)
            suffix = " Lag" if pf_val >= 0 else " Lead"
            self.pf_label.setText(f"PF {abs(pf_val):.2f}{suffix}")
