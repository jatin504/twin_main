from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class YellowSquareIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(14, 14)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Border
        p.setPen(QPen(QColor("#C08A00"), 1))

        # Fill
        p.setBrush(QColor("#F3C316"))

        # Square
        p.drawRect(2, 2, 10, 10)