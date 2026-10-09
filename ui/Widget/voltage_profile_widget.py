from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QFrame,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QSizePolicy,
)

from ui.Widget.time_series_widget import TimeSeriesWidget


class VoltageProfileCanvas(QWidget):
    """
    QPainter-based spatial per-unit voltage profile chart across all main buses.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bus_names = []
        self.voltage_data = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_voltage_data(self, bus_voltages):
        self.bus_names = []
        self.voltage_data = []

        for bus_name, voltage in bus_voltages.items():
            self.bus_names.append(bus_name)
            self.voltage_data.append(float(voltage))

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # BACKGROUND
        p.fillRect(self.rect(), QColor("#FFFFFF"))

        # CHART AREA
        left = 38
        top = 34
        right = self.width() - 10
        bottom = self.height() - 55

        chart_width = max(10, right - left)
        chart_height = max(10, bottom - top)

        # TITLE
        title_font = QFont()
        title_font.setPointSize(9)
        title_font.setBold(True)
        p.setFont(title_font)
        p.setPen(QColor("#111827"))
        p.drawText(10, 18, "VOLTAGE PROFILE (p.u.)")

        # NO DATA
        if not self.voltage_data:
            p.setPen(QColor("#6B7280"))
            p.drawText(left, top + 40, "Waiting for voltage data...")
            return

        # DYNAMIC Y-AXIS
        data_min = min(self.voltage_data)
        data_max = max(self.voltage_data)

        if data_min == data_max:
            padding = max(abs(data_min) * 0.05, 0.01)
        else:
            data_range = data_max - data_min
            padding = max(data_range * 0.20, 0.01)

        min_voltage = min(data_min - padding, 0.90)
        max_voltage = max(data_max + padding, 1.10)

        # DYNAMIC TICK COUNT
        tick_count = 6
        step = (max_voltage - min_voltage) / (tick_count - 1)
        y_axis_values = [min_voltage + (step * i) for i in range(tick_count)]

        # HORIZONTAL GRID
        p.setPen(QPen(QColor("#E5E7EB"), 1))
        for value in y_axis_values:
            y = bottom - ((value - min_voltage) / (max_voltage - min_voltage)) * chart_height
            p.drawLine(left, int(y), right, int(y))

        # Y AXIS LABELS
        axis_font = QFont()
        axis_font.setPointSize(7)
        p.setFont(axis_font)
        p.setPen(QColor("#4B5563"))

        for value in reversed(y_axis_values):
            y = bottom - ((value - min_voltage) / (max_voltage - min_voltage)) * chart_height
            p.drawText(3, int(y + 3), f"{value:.3f}")

        # VOLTAGE LIMIT LINES
        limits = [
            (1.10, "#E53935"),   # RED - High limit
            (1.05, "#D99A00"),   # ORANGE - High warning
            (0.94, "#D99A00"),   # ORANGE - Low warning
            (0.90, "#E53935"),   # RED - Low limit
        ]

        for value, color in limits:
            y = bottom - ((value - min_voltage) / (max_voltage - min_voltage)) * chart_height
            p.setPen(QPen(QColor(color), 1, Qt.DashLine))
            p.drawLine(left, int(y), right, int(y))

        # X GRID
        for i in range(len(self.voltage_data)):
            if len(self.voltage_data) == 1:
                x = left
            else:
                x = left + (i / (len(self.voltage_data) - 1)) * chart_width
            p.setPen(QPen(QColor("#E5E7EB"), 1))
            p.drawLine(int(x), top, int(x), bottom)

        # VOLTAGE POINTS
        points = []
        for i, value in enumerate(self.voltage_data):
            if len(self.voltage_data) == 1:
                x = left
            else:
                x = left + (i / (len(self.voltage_data) - 1)) * chart_width
            y = bottom - ((value - min_voltage) / (max_voltage - min_voltage)) * chart_height
            points.append(QPoint(int(x), int(y)))

        # VOLTAGE LINE
        p.setPen(QPen(QColor("#4F8FEF"), 2))
        for i in range(len(points) - 1):
            p.drawLine(points[i], points[i + 1])

        # POINTS AND VALUES
        font_point = QFont()
        font_point.setPointSize(6)
        font_point.setBold(True)
        p.setFont(font_point)

        for i, point in enumerate(points):
            value = self.voltage_data[i]
            if value > 1.10 or value < 0.90:
                point_color = QColor("#E53935")
            elif value > 1.05 or value < 0.94:
                point_color = QColor("#D99A00")
            else:
                point_color = QColor("#4F8FEF")

            p.setBrush(point_color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(point, 3, 3)

            p.setPen(point_color)
            p.drawText(point.x() - 12, point.y() - 7, f"{value:.3f}")

        # X AXIS LABEL
        p.setPen(QColor("#4B5563"))
        p.drawText(int(left + chart_width / 2 - 10), self.height() - 6, "Bus")

        # BUS LABELS
        label_font = QFont()
        label_font.setPointSize(6)
        label_font.setBold(False)
        p.setFont(label_font)
        p.setPen(QColor("#4B5563"))

        for i, bus_name in enumerate(self.bus_names):
            if len(self.bus_names) == 1:
                x = left
            else:
                x = left + (i / (len(self.bus_names) - 1)) * chart_width

            label = bus_name.replace("_", " ")
            label_width = p.fontMetrics().horizontalAdvance(label)

            p.save()
            p.translate(int(x), bottom + 24)
            p.rotate(-45)
            p.drawText(-label_width // 2, 0, label)
            p.restore()


class VoltageProfileWidget(QFrame):
    """
    Row 1 Voltage Widget (Width: 330, Height: 300):
    Dual-mode presentation featuring:
    1. 1-Hour Time Series Historical Trends (Active by default - maps Voltage Profile buses + Load Demand)
    2. Per-Unit Bus Voltage Profile spatial chart
    3. Fullscreen expansion (⛶)
    """

    def __init__(self, simulator=None, parent=None):
        super().__init__(parent)
        self.simulator = simulator

        self.setFixedWidth(330)
        self.setFixedHeight(300)

        self.setStyleSheet("""
            VoltageProfileWidget {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Tab switch header
        tab_row = QHBoxLayout()
        tab_row.setSpacing(4)

        self.btn_trends = QPushButton("1-Hr Trends")
        self.btn_profile = QPushButton("Bus Profile (p.u.)")

        for btn in (self.btn_trends, self.btn_profile):
            btn.setCheckable(True)
            btn.setFixedHeight(22)
            btn.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9;
                    color: #475569;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background: #E2E8F0;
                    color: #0F172A;
                }
                QPushButton:checked {
                    background: #2563EB;
                    color: #FFFFFF;
                    border: 1px solid #2563EB;
                    font-weight: 700;
                }
            """)

        self.btn_trends.setChecked(True)
        self.btn_trends.clicked.connect(lambda: self.switch_view(0))
        self.btn_profile.clicked.connect(lambda: self.switch_view(1))

        tab_row.addWidget(self.btn_trends)
        tab_row.addWidget(self.btn_profile)
        tab_row.addStretch()

        layout.addLayout(tab_row)

        # Stacked pages
        self.stack = QStackedWidget(self)

        # Page 0: 1-Hour Rolling Trends (Active by default)
        self.time_series = TimeSeriesWidget(simulator=self.simulator, compact=True)
        self.stack.addWidget(self.time_series)

        # Page 1: Per-unit Bus Voltage Profile
        self.bus_canvas = VoltageProfileCanvas(self)
        self.stack.addWidget(self.bus_canvas)

        layout.addWidget(self.stack, 1)

    def switch_view(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_trends.setChecked(index == 0)
        self.btn_profile.setChecked(index == 1)

    def update_voltage_data(self, bus_voltages):
        self.bus_canvas.update_voltage_data(bus_voltages)
        self.time_series.update_from_simulator(self.simulator)

    def set_simulator(self, simulator):
        self.simulator = simulator
        self.time_series.simulator = simulator
        self.time_series.update_from_simulator(simulator)