from PySide6.QtCore import Qt, QRectF, QPoint
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPolygon,
)
from PySide6.QtWidgets import QWidget


class BatteryIcon(QWidget):

    def __init__(self, soc=42):
        super().__init__()

        self.soc = max(0, min(100, float(soc)))
        self.setFixedSize(70, 130)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QPen(QColor("#C7CDD6"), 2))
        p.setBrush(QColor("#FFFFFF"))

        p.drawRoundedRect(
            QRectF(8, 10, 54, 110),
            5,
            5
        )

        p.setPen(QPen(QColor("#6B7280"), 2))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRect(22, 30, 30, 46)

        charge = self.soc / 100.0
        fillHeight = int(40 * charge)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#66C94A"))
        p.drawRect(
            25,
            33 + (40 - fillHeight),
            24,
            fillHeight,
        )

        p.setPen(QPen(QColor("#F8FFF5"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(25, 33, 24, 40)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2D2D2D"))

        bolt = QPolygon([
            QPoint(39, 39),
            QPoint(34, 50),
            QPoint(38, 50),
            QPoint(35, 62),
            QPoint(44, 48),
            QPoint(40, 48),
        ])

        p.drawPolygon(bolt)

    def set_soc(self, soc):
        self.soc = max(0, min(100, float(soc)))
        self.update()
