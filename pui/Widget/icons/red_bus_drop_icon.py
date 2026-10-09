from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class RedBusDropIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 40)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== Grey Arrow =====
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6F737A"))

        arrow = QPolygon([
            QPoint(8, 2),
            QPoint(3, 11),
            QPoint(13, 11),
        ])

        p.drawPolygon(arrow)

        # ===== Red Vertical Line =====
        p.setPen(QPen(QColor("#E53935"), 2))
        p.drawLine(8, 11, 8, 27)

        # ===== Red Square =====
        p.setPen(QPen(QColor("#B71C1C"), 1))
        p.setBrush(QColor("#F44336"))
        p.drawRect(3, 27, 10, 10)