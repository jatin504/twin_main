from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CBSolarIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(26, 26)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # vertical line
        p.setPen(QPen(QColor("#9AA0A6"), 2))
        p.drawLine(13, 0, 13, 26)

        # horizontal line
        p.drawLine(0, 13, 26, 13)

        # green square
        p.setPen(QPen(QColor("#63C132"), 2))
        p.drawRect(4, 4, 18, 18)

        # switch blade
        p.drawLine(9, 16, 16, 9)

        # contact
        p.setPen(QPen(QColor("#C7B28A"), 2))
        p.drawPoint(17, 8)