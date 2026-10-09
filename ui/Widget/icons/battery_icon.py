from PySide6.QtCore import Qt, QPoint
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

        p.setPen(QPen(QColor("#6B7280"), 2))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRect(10, 13, 50, 102)

        charge = self.soc / 100.0
        fillHeight = int(92 * charge)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#66C94A"))
        p.drawRect(
            14,
            17 + (92 - fillHeight),
            42,
            fillHeight,
        )

        p.setPen(QPen(QColor("#F8FFF5"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(14, 17, 42, 92)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2D2D2D"))

        bolt = QPolygon([
            QPoint(38, 31),
            QPoint(30, 53),
            QPoint(37, 53),
            QPoint(32, 78),
            QPoint(46, 49),
            QPoint(40, 49),
        ])

        p.drawPolygon(bolt)

    def set_soc(self, soc):
        self.soc = max(0, min(100, float(soc)))
        self.update()
