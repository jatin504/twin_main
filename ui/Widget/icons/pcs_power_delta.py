from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPolygon, QFont
from PySide6.QtWidgets import QWidget


class PCSPowerDelta(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(85, 42)
        self.delta_power = 0.0

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

    def set_value(self, value_mw):

        self.delta_power = float(value_mw)
        self.update()

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        green = QColor("#39C84A")

        # -------------------------
        # TEXT
        # -------------------------

        p.setPen(green)

        font = QFont()
        font.setPointSize(9)
        p.setFont(font)

        if self.delta_power > 0:
            text = f"+{self.delta_power:.2f} MW"

        elif self.delta_power < 0:
            text = f"{self.delta_power:.2f} MW"

        else:
            text = "0.00 MW"

        p.drawText(24, 25, text)

        # -------------------------
        # ARROW
        # -------------------------

        p.setPen(Qt.NoPen)
        p.setBrush(green)

        # UP
        if self.delta_power > 0:

            arrow = QPolygon([
                QPoint(9, 3),
                QPoint(4, 12),
                QPoint(14, 12),
            ])

            p.drawPolygon(arrow)

        # DOWN
        elif self.delta_power < 0:

            arrow = QPolygon([
                QPoint(9, 39),
                QPoint(4, 30),
                QPoint(14, 30),
            ])

            p.drawPolygon(arrow)