from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

class GreenHorizontalLine(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(32,6)

    def paintEvent(self,e):

        p=QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QPen(QColor("#39C84A"),2))
        p.drawLine(0,3,30,3)