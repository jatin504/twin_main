from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class GridIcon(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(140, 140)

        self.dragging = False
        self.offset = None
        self.grid_voltage = 0.0
        self.import_power = 0.0
        self.export_power = 0.0
        self.frequency = 0.0

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
        font.setPointSize(8)
        p.setFont(font)

        p.setPen(QColor("#111827"))

        # GRID title bold
        font.setBold(True)
        p.setFont(font)
        p.drawText(70, 20, "GRID")

        # Baaki text normal + small
        font.setBold(False)
        p.setFont(font)

        p.drawText(70, 45, f"{self.grid_voltage:.2f} V")
        p.drawText(70, 65, f"{self.import_power:.2f} kW")
        p.drawText(70, 85, f"{self.export_power:.2f} kW")
        p.drawText(70, 105, f"{self.frequency:.2f} Hz")

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            self.dragging=True
            self.offset=e.position().toPoint()

    def mouseMoveEvent(self,e):
        if self.dragging:
            p=self.mapToParent(e.position().toPoint()-self.offset)
            self.move(p)
            print(f"GRID x={self.x()} y={self.y()}")

    def mouseReleaseEvent(self,e):
        self.dragging=False
        print(f"FINAL GRID : ({self.x()},{self.y()})")

    def update_data(
        self,
        grid_voltage,
        import_power,
        export_power,
        frequency,
    ):
        self.grid_voltage = grid_voltage
        self.import_power = import_power
        self.export_power = export_power
        self.frequency = frequency

        self.update()