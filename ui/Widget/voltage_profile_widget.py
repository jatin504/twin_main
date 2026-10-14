from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QFrame,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
)


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
    Right-column spatial bus voltage profile (p.u.) chart.
    """

    def __init__(self, simulator=None, parent=None, width: int = 330, height: int = 300):
        super().__init__(parent)
        self.simulator = simulator

        if width > 0:
            self.setFixedWidth(width)
        if height > 0:
            self.setFixedHeight(height)

        self.setStyleSheet("""
            VoltageProfileWidget {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.bus_canvas = VoltageProfileCanvas(self)
        layout.addWidget(self.bus_canvas, 1)

    def update_voltage_data(self, bus_voltages):
        self.bus_canvas.update_voltage_data(bus_voltages)

    def set_simulator(self, simulator):
        self.simulator = simulator