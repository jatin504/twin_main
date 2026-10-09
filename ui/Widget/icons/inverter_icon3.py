from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QPainterPath,
)
from PySide6.QtWidgets import QWidget


class InverterIcon3(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(42, 42)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== Outer Border =====
        p.setPen(QPen(QColor("#9CA3AF"), 2.8))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(3, 3, 36, 36, 4, 4)

        # ===== Inner Border =====
        p.setPen(QPen(QColor("#D1D5DB"), 1.5))
        p.drawRoundedRect(4, 4, 34, 34, 4, 4)

        # ===== Diagonal =====
        p.setPen(QPen(QColor("#9CA3AF"), 2.2))
        p.drawLine(8, 34, 34, 8)

        # ===== Top Wave =====
        path = QPainterPath()
        path.moveTo(10, 17)

        path.cubicTo(
            11.5, 13,
            14, 13,
            15.5, 17
        )

        path.cubicTo(
            17, 21,
            19.5, 21,
            21, 17
        )

        p.drawPath(path)

        # ===== Bottom Wave =====
        path = QPainterPath()
        path.moveTo(20, 27)

        path.cubicTo(
            21.5, 23,
            24, 23,
            25.5, 27
        )

        path.cubicTo(
            27, 31,
            29.5, 31,
            31, 27
        )

        p.drawPath(path)