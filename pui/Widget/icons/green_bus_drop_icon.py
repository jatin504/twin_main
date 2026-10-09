from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class GreenBusDropIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 32)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== Green Vertical Line =====
        p.setPen(QPen(QColor("#2ECC40"), 2))
        p.drawLine(8, 2, 8, 22)

        # ===== Grey Arrow (Down) =====
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6F737A"))

        arrow = QPolygon([
            QPoint(3, 22),
            QPoint(13, 22),
            QPoint(8, 30),
        ])

        p.drawPolygon(arrow)