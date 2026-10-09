from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class GreenHorizontalLine(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(67, 6)

    def line_end_x(self):
        return max(0, self.width() - 1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QPen(QColor("#39C84A"), 2))
        p.drawLine(0, 3, self.line_end_x(), 3)
