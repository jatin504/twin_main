from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QFrame


class VoltageProfileWidget(QFrame):

    def __init__(self):
        super().__init__()

        # ==================================================
        # SIZE
        # ==================================================

        self.setFixedWidth(330)
        self.setFixedHeight(300)

        # ==================================================
        # VOLTAGE DATA
        # ==================================================

        self.bus_names = []
        self.voltage_data = []

        # ==================================================
        # LIGHT MODE
        # ==================================================

        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 3px;
            }
        """)

    
    # UPDATE VOLTAGE DATA
    

    def update_voltage_data(self, bus_voltages):

        self.bus_names = []
        self.voltage_data = []

        for bus_name, voltage in bus_voltages.items():

            self.bus_names.append(bus_name)
            self.voltage_data.append(float(voltage))

        self.update()

    
    # PAINT
    

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ==================================================
        # BACKGROUND
        # ==================================================

        p.fillRect(
            self.rect(),
            QColor("#FFFFFF")
        )

        # ==================================================
        # CHART AREA
        # ==================================================

        left = 38
        top = 38
        right = self.width() - 10
        bottom = self.height() - 40

        chart_width = right - left
        chart_height = bottom - top

        # ==================================================
        # TITLE
        # ==================================================

        title_font = QFont()
        title_font.setPointSize(9)
        title_font.setBold(True)

        p.setFont(title_font)
        p.setPen(QColor("#111827"))

        p.drawText(
            10,
            20,
            "VOLTAGE PROFILE (p.u.)"
        )

        # ==================================================
        # NO DATA
        # ==================================================

        if not self.voltage_data:

            p.setPen(QColor("#6B7280"))

            p.drawText(
                left,
                top + 40,
                "Waiting for voltage data..."
            )

            return

        # ==================================================
        # DYNAMIC Y-AXIS
        # ==================================================

        data_min = min(self.voltage_data)
        data_max = max(self.voltage_data)

        # Same value case
        if data_min == data_max:

            padding = max(
                abs(data_min) * 0.05,
                0.01
            )

        else:

            data_range = data_max - data_min

            padding = max(
                data_range * 0.20,
                0.01
            )

        min_voltage = min(
            data_min - padding,
            0.90
        )

        max_voltage = max(
            data_max + padding,
            1.10
        )

        # ==================================================
        # DYNAMIC TICK COUNT
        # ==================================================

        tick_count = 6

        step = (
            max_voltage - min_voltage
        ) / (tick_count - 1)

        y_axis_values = [
            min_voltage + (
                step * i
            )
            for i in range(tick_count)
        ]

        # ==================================================
        # HORIZONTAL GRID
        # ==================================================

        p.setPen(
            QPen(
                QColor("#E5E7EB"),
                1
            )
        )

        for value in y_axis_values:

            y = bottom - (
                (value - min_voltage)
                / (max_voltage - min_voltage)
            ) * chart_height

            p.drawLine(
                left,
                int(y),
                right,
                int(y)
            )

        # ==================================================
        # Y AXIS LABELS
        # ==================================================

        axis_font = QFont()
        axis_font.setPointSize(7)

        p.setFont(axis_font)
        p.setPen(QColor("#4B5563"))

        for value in reversed(y_axis_values):

            y = bottom - (
                (value - min_voltage)
                / (max_voltage - min_voltage)
            ) * chart_height

            p.drawText(
                3,
                int(y + 3),
                f"{value:.3f}"
            )

        # ==================================================
        # VOLTAGE LIMIT LINES
        # ==================================================

        limits = [
            (1.10, "#E53935"),   # RED - High limit
            (1.05, "#D99A00"),   # ORANGE - High warning
            (0.94, "#D99A00"),   # ORANGE - Low warning
            (0.90, "#E53935"),   # RED - Low limit
        ]

        for value, color in limits:

            y = bottom - (
                (value - min_voltage)
                / (max_voltage - min_voltage)
            ) * chart_height

            p.setPen(
                QPen(
                    QColor(color),
                    1,
                    Qt.DashLine
                )
            )

            p.drawLine(
                left,
                int(y),
                right,
                int(y)
            )

        # ==================================================
        # X GRID
        # ==================================================

        for i in range(len(self.voltage_data)):

            if len(self.voltage_data) == 1:

                x = left

            else:

                x = left + (
                    i / (len(self.voltage_data) - 1)
                ) * chart_width

            p.setPen(
                QPen(
                    QColor("#E5E7EB"),
                    1
                )
            )

            p.drawLine(
                int(x),
                top,
                int(x),
                bottom
            )

        # ==================================================
        # VOLTAGE POINTS
        # ==================================================

        points = []

        for i, value in enumerate(
            self.voltage_data
        ):

            if len(self.voltage_data) == 1:

                x = left

            else:

                x = left + (
                    i / (len(self.voltage_data) - 1)
                ) * chart_width

            y = bottom - (
                (value - min_voltage)
                / (max_voltage - min_voltage)
            ) * chart_height

            points.append(
                QPoint(
                    int(x),
                    int(y)
                )
            )

        # ==================================================
        # VOLTAGE LINE
        # ==================================================

        p.setPen(
            QPen(
                QColor("#4F8FEF"),
                2
            )
        )

        for i in range(
            len(points) - 1
        ):

            p.drawLine(
                points[i],
                points[i + 1]
            )

        # ==================================================
        # POINTS + VALUES
        # ==================================================

        value_font = QFont()
        value_font.setPointSize(6)

        p.setFont(value_font)

        for i, point in enumerate(points):

            value = self.voltage_data[i]

            # Dynamic point status
            if value < data_min + (
                data_max - data_min
            ) * 0.10:

                point_color = QColor("#E53935")

            else:

                point_color = QColor("#4F8FEF")

            # Point

            p.setBrush(point_color)
            p.setPen(Qt.NoPen)

            p.drawEllipse(
                point,
                3,
                3
            )

            # Value

            p.setPen(point_color)

            p.drawText(
                point.x() - 12,
                point.y() - 7,
                f"{value:.3f}"
            )

        # ==================================================
        # X AXIS LABEL
        # ==================================================

        p.setPen(
            QColor("#4B5563")
        )

        p.drawText(
            int(
                left
                + chart_width / 2
                - 10
            ),
            self.height() - 8,
            "Bus"
        )

        # ==================================================
        # BUS LABELS
        # ==================================================

        for i, bus_name in enumerate(
            self.bus_names
        ):

            if len(self.bus_names) == 1:

                x = left

            else:

                x = left + (
                    i / (len(self.bus_names) - 1)
                ) * chart_width

            # Short names

            if bus_name == "GRID_11KV":
                label = "Grid"

            elif bus_name == "BUS_690_A":
                label = "690A"

            elif bus_name == "PCS_BUS":
                label = "PCS"

            elif bus_name == "PV_BUS":
                label = "PV"

            elif bus_name == "LOAD_BUS":
                label = "Load"

            else:
                label = bus_name

            p.drawText(
                int(x - 15),
                bottom + 14,
                label
            )