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

        title = QLabel("SOLAR PLANT")
        title.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 9px;
                font-weight: 700;
                color: #2F3640;
            }
        """)

        kw = QLabel("2.15 MW")
        kw.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        kvar = QLabel("0.05 MVAr")
        kvar.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        pf = QLabel("PF 0.99 Lag")
        pf.setStyleSheet("""
            QLabel {
                background: transparent;
                font-size: 8px;
                color: #404040;
            }
        """)

        right.addWidget(title)
        right.addWidget(kw)
        right.addWidget(kvar)
        right.addWidget(pf)

        layout.addLayout(right)