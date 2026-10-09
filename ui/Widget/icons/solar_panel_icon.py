from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget


class SolarPanelIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(34, 52)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ================= SUN =================

        cx = 17
        cy = 9

        p.setPen(QPen(QColor("#E8A300"), 2))

        p.drawEllipse(cx - 4, cy - 4, 8, 8)

        p.drawLine(cx, 0, cx, 3)
        p.drawLine(cx, 15, cx, 18)

        p.drawLine(8, 9, 11, 9)
        p.drawLine(23, 9, 26, 9)

        p.drawLine(11, 3, 13, 5)
        p.drawLine(21, 13, 23, 15)

        p.drawLine(23, 3, 21, 5)
        p.drawLine(13, 13, 11, 15)

        # ================= PANEL =================

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3D7CC4"))

        y = 22

        # row 1
        p.drawPolygon(QPolygon([
            QPoint(7, y),
            QPoint(16, y),
            QPoint(15, y + 8),
            QPoint(5, y + 8),
        ]))

        p.drawPolygon(QPolygon([
            QPoint(18, y),
            QPoint(27, y),
            QPoint(29, y + 8),
            QPoint(19, y + 8),
        ]))

        # row 2
        y += 10

        p.drawPolygon(QPolygon([
            QPoint(5, y),
            QPoint(15, y),
            QPoint(14, y + 8),
            QPoint(3, y + 8),
        ]))

        p.drawPolygon(QPolygon([
            QPoint(17, y),
            QPoint(28, y),
            QPoint(30, y + 8),
            QPoint(18, y + 8),
        ]))

        # stand
        p.setPen(QPen(QColor("#4B5563"), 2))
        p.drawLine(17, 40, 17, 48)
        p.drawLine(12, 48, 22, 48)
