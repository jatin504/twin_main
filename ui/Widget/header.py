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
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(0)

        self.titleLbl = QLabel(title)
        self.titleLbl.setStyleSheet("""
        color:#6B7280;
        font-size:9px;
        font-weight:500;
        border:none;
        """)

        self.valueLbl = QLabel(value)
        self.valueLbl.setAlignment(Qt.AlignCenter)
        self.valueLbl.setStyleSheet(f"""
        color:{color};
        font-size:12px;
        font-weight:700;
        border:none;
        """)

        layout.addWidget(self.titleLbl)
        layout.addWidget(self.valueLbl)

    def set_value(self, value, color=None):
        self.valueLbl.setText(str(value))
        if color:
            self.valueLbl.setStyleSheet(f"""
            color:{color};
            font-size:12px;
            font-weight:700;
            border:none;
            """)


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
        layout.setContentsMargins(12, 5, 12, 5)
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

        self.status_box = InfoBox("Simulation Status", "RUNNING", "#16A34A")
        self.elapsed_box = InfoBox("Elapsed Time", "00:00 / 15m", "#D97706")
        self.time_box = InfoBox("Simulation Time", "--")
        self.step_box = InfoBox("Time Step", "15 min")
        self.scenario_box = InfoBox("Scenario", "Base Case")
        self.horizon_box = InfoBox("Forecast Horizon", "24 Hours")

        layout.addWidget(self.status_box)
        layout.addWidget(self.elapsed_box)
        layout.addWidget(self.time_box)
        layout.addWidget(self.step_box)
        layout.addWidget(self.scenario_box)
        layout.addWidget(self.horizon_box)

    def update_elapsed_time(self, elapsed_str):
        self.elapsed_box.set_value(elapsed_str, "#D97706")

    def update_simulation_time(self, time_str):
        self.time_box.set_value(time_str)

    def update_status(self, status, color="#16A34A"):
        self.status_box.set_value(status, color)
