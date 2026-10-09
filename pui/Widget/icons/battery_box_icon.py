# ui/Widget/icons/battery_box_icon.py

from PySide6.QtCore import Qt, QRectF, QPoint
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPolygon,
)
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout

from pui.Widget.icons.battery_icon import BatteryIcon


class BatteryBoxIcon(QWidget):

    def __init__(
        self,
        title="BESS BANK-1",
        soc=0,
        energy="0.00 kWh",
        voltage=0.0,
        temperature=0.0,
        pf="1.00",
        loading=42,
    ):
        super().__init__()

        self.loading = loading
        self.temperature = temperature

        self.setFixedSize(180, 130)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.icon = BatteryIcon(soc)
        layout.addWidget(self.icon)

        right = QVBoxLayout()
        right.setSpacing(2)

        lbl1 = QLabel(title)
        lbl1.setStyleSheet(
            "font-size:10px;font-weight:700;color:#2F343B;"
        )

        self.lbl2 = QLabel("SOC  0 %")
        self.lbl2.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl3 = QLabel("0.00 kWh")
        self.lbl3.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl_power = QLabel("0.00 kW")
        self.lbl_power.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl_voltage = QLabel("0.00 V")
        self.lbl_voltage.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl_temperature = QLabel("0.0 °C")
        self.lbl_temperature.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl_pf = QLabel(f"PF  {pf}")
        self.lbl_pf.setStyleSheet(
            "font-size:9px;color:#444;"
        )

        self.lbl_loading = QLabel("Loading: 0 %")
        self.lbl_loading.setStyleSheet("""
        QLabel{
            color:#58B52A;
            font-size:10px;
            font-weight:700;
        }
        """)

        right.addWidget(lbl1)
        right.addWidget(self.lbl2)
        right.addWidget(self.lbl3)
        right.addWidget(self.lbl_power)
        right.addWidget(self.lbl_voltage)
        right.addWidget(self.lbl_temperature)
        right.addWidget(self.lbl_pf)
        right.addStretch()
        right.addWidget(self.lbl_loading)

        layout.addLayout(right)

    def update_data(
        self,
        soc,
        stored_energy_kwh,
        battery_voltage,
        temperature=None,
        power_kw=0.0,
    ):
        # SOC
        soc = float(soc or 0)
        self.lbl2.setText(f"SOC  {soc:.0f} %")

        # Battery fill = SOC
        self.icon.set_soc(soc)

        # Stored Energy
        stored_energy_kwh = float(stored_energy_kwh or 0)

        self.lbl3.setText(
            f"{stored_energy_kwh:.2f} kWh"
        )

        power_kw = float(power_kw or 0)
        self.lbl_power.setText(
            f"{power_kw:.2f} kW"
        )

        # Battery Voltage
        battery_voltage = float(battery_voltage or 0)

        self.lbl_voltage.setText(
            f"{battery_voltage:.2f} V"
        )

        # Temperature
        if temperature is not None:
            self.temperature = float(temperature)

        self.lbl_temperature.setText(
            f"{self.temperature:.2f} °C"
        )