from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPolygon, QFont
from PySide6.QtWidgets import QWidget


class GreenUpArrow(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(85, 42)

        # Transparent background
        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

        self.delta_power = 0.0

    def set_value(self, value_mw):
        self.delta_power = float(value_mw)
        self.update()

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # IMPORTANT:
        # Do not draw any background
        p.setCompositionMode(
            QPainter.CompositionMode_SourceOver
        )

        green = QColor("#39C84A")

        # =====================================
        # TEXT
        # =====================================

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

        p.drawText(
            24,
            25,
            text
        )

        # =====================================
        # ARROW
        # =====================================

        p.setPen(Qt.NoPen)
        p.setBrush(green)

        # UP
        if self.delta_power > 0:

            arrow = QPolygon([
                QPoint(9, 2),
                QPoint(4, 11),
                QPoint(14, 11),
            ])

            p.drawPolygon(arrow)

        # DOWN
        elif self.delta_power < 0:

            arrow = QPolygon([
                QPoint(9, 38),
                QPoint(4, 29),
                QPoint(14, 29),
            ])

            p.drawPolygon(arrow)