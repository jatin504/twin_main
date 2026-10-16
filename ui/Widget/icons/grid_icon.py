from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from common.enums import FaultCode


class GridIcon(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(145, 140)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.grid_voltage = 0.0
        self.import_power = 0.0
        self.export_power = 0.0
        self.frequency = 0.0
        self.fault_code = "None"
        self.grid_available = True

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#9CA3AF"), 2)
        p.setPen(pen)

        # Tower
        p.drawLine(25,20,10,110)
        p.drawLine(25,20,40,110)

        p.drawLine(8,32,42,32)
        p.drawLine(5,52,45,52)
        p.drawLine(2,72,48,72)
        p.drawLine(0,92,50,92)

        p.drawLine(25,20,25,110)

        p.drawLine(25,32,10,45)
        p.drawLine(25,32,40,45)

        p.drawLine(25,52,10,65)
        p.drawLine(25,52,40,65)

        p.drawLine(25,72,10,85)
        p.drawLine(25,72,40,85)

        p.drawLine(10,110,40,110)

        # Grid text
        font = p.font()
        font.setPointSize(7)
        p.setFont(font)

        p.setPen(QColor("#111827"))

        # GRID title bold
        font.setBold(True)
        p.setFont(font)
        p.drawText(70, 20, "GRID")

        # Baaki text normal + small
        font.setBold(False)
        p.setFont(font)

        p.drawText(55, 38, f"Grid: {self.grid_voltage:.2f} kV")
        import_text = f"Import: {self.import_power:.2f} kW"
        export_text = f"Export: {self.export_power:.2f} kW"

        p.setPen(QColor("#111827"))
        p.drawText(55, 54, import_text)
        if self.import_power > 0:
            arrow_x = 58 + p.fontMetrics().horizontalAdvance(import_text)
            p.setPen(QColor("#00ff00"))
            p.drawLine(arrow_x, 51, arrow_x + 7, 51)
            p.drawLine(arrow_x + 3, 48, arrow_x + 7, 51)
            p.drawLine(arrow_x + 3, 54, arrow_x + 7, 51)

        export_text_x = 55
        p.setPen(QColor("#111827"))
        p.drawText(export_text_x, 70, export_text)
        if self.export_power > 0:
            arrow_x = (
                export_text_x
                + p.fontMetrics().horizontalAdvance(export_text)
                + 3
            )
            p.setPen(QColor("#00ff00"))
            p.drawLine(arrow_x + 7, 67, arrow_x, 67)
            p.drawLine(arrow_x + 3, 64, arrow_x, 67)
            p.drawLine(arrow_x + 3, 70, arrow_x, 67)

        p.setPen(QColor("#111827"))
        p.drawText(55, 86, f"Freq: {self.frequency:.2f} Hz")

        # Fault text rendering (multiline word wrap & alert coloring so long fault text never hides)
        is_fault_active = (self.fault_code not in ("None", "NONE", "N/A"))
        if is_fault_active:
            p.setPen(QColor("#DC2626"))  # Bold alert RED for active fault
            font.setBold(True)
            p.setFont(font)
        else:
            p.setPen(QColor("#111827"))
            font.setBold(False)
            p.setFont(font)

        fault_rect = QRect(55, 92, 90, 26)
        p.drawText(
            fault_rect,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            f"Fault: {self.fault_code}",
        )
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor("#111827"))
        p.drawText(55, 118, f"State: {str(self.grid_available).lower()}")

    def update_data(
        self,
        grid_voltage,
        import_power,
        export_power,
        frequency,
        fault_code,
        grid_available=True,
    ):
        self.grid_voltage = grid_voltage
        self.import_power = import_power
        self.export_power = export_power
        self.frequency = frequency
        self.grid_available = bool(grid_available)
        if fault_code is None:
            self.fault_code = "N/A"
        else:
            try:
                self.fault_code = FaultCode(int(fault_code)).name.replace(
                    "_", " "
                ).title()
            except (TypeError, ValueError):
                self.fault_code = f"Unknown ({fault_code})"

        self.setToolTip(f"Grid Status | Voltage: {self.grid_voltage:.2f} kV | Fault: {self.fault_code}")
        self.update()