from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class GreenDoubleArrow(QWidget):

    def __init__(self):
        super().__init__()

        # Overall height increase
        self.setFixedSize(18, 110)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== LONG VERTICAL LINE =====
        p.setPen(QPen(QColor("#39C84A"), 2))
        p.drawLine(9, 10, 9, 100)

        # ===== TOP ARROW =====
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#39C84A"))

        topArrow = QPolygon([
            QPoint(9, 2),
            QPoint(4, 10),
            QPoint(7, 10),
            QPoint(7, 16),
            QPoint(11, 16),
            QPoint(11, 10),
            QPoint(14, 10),
        ])

        p.drawPolygon(topArrow)

        # ===== BOTTOM ARROW =====
        bottomArrow = QPolygon([
            QPoint(9, 108),
            QPoint(4, 100),
            QPoint(7, 100),
            QPoint(7, 94),
            QPoint(11, 94),
            QPoint(11, 100),
            QPoint(14, 100),
        ])

        p.drawPolygon(bottomArrow)