from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class BusDropIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 40)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== Dark Grey Arrow =====
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6F737A"))

        arrow = QPolygon([
            QPoint(8, 2),
            QPoint(3, 11),
            QPoint(13, 11),
        ])

        p.drawPolygon(arrow)

        # ===== Yellow Vertical Line =====
        p.setPen(QPen(QColor("#D6A300"), 2))
        p.drawLine(8, 11, 8, 27)

        # ===== Yellow Square =====
        p.setPen(QPen(QColor("#B8860B"), 1))
        p.setBrush(QColor("#F3C316"))
        p.drawRect(3, 27, 10, 10)