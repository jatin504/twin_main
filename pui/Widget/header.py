from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
)


class InfoBox(QFrame):

    def __init__(self, title, value, color="#111827"):
        super().__init__()

        self.setFixedHeight(48)
        self.setStyleSheet("""
        QFrame{
            background:#F8FAFC;
            border:1px solid #D9E1EA;
            border-radius:2px;
        }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,4,10,4)
        layout.setSpacing(0)

        titleLbl = QLabel(title)
        titleLbl.setStyleSheet("""
        color:#6B7280;
        font-size:9px;
        font-weight:500;
        border:none;
        """)

        valueLbl = QLabel(value)
        valueLbl.setAlignment(Qt.AlignCenter)
        valueLbl.setStyleSheet(f"""
        color:{color};
        font-size:12px;
        font-weight:700;
        border:none;
        """)

        layout.addWidget(titleLbl)
        layout.addWidget(valueLbl)


class HeaderWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(58)

        self.setStyleSheet("""
        QWidget{
            background:#F5F7FA;
            border:none;
        }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12,5,12,5)
        layout.setSpacing(8)

        title = QLabel("DIGITAL TWIN SIMULATION")
        title.setStyleSheet("""
        color:#111827;
        font-size:18px;
        font-weight:700;
        border:none;
        """)

        layout.addWidget(title)
        layout.addStretch()

        layout.addWidget(InfoBox("Simulation Status","RUNNING","#16A34A"))
        layout.addWidget(InfoBox("Simulation Time","20-May-2025   10:15:30"))
        layout.addWidget(InfoBox("Time Step","15 min"))
        layout.addWidget(InfoBox("Scenario","Base Case"))
        layout.addWidget(InfoBox("Forecast Horizon","24 Hours"))
