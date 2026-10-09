from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class BreakerIcon(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(30, 30)

        self.dragging = False
        self.offset = None

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Yellow line
        pen = QPen(QColor("#D3A000"), 2)
        p.setPen(pen)
        p.drawLine(0, 15, 8, 15)

        # Green box
        pen = QPen(QColor("#4CAF50"), 2)
        p.setPen(pen)
        p.drawRect(8, 6, 14, 14)

        # Black circle
        p.setBrush(QColor("#111111"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(12, 10, 6, 6)

        # White Arrow
        pen = QPen(QColor("#F5F5F5"), 2)
        p.setPen(pen)

        p.drawLine(22, 15, 28, 15)
        p.drawLine(24, 12, 22, 15)
        p.drawLine(24, 18, 22, 15)

    # ---------- Drag ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.dragging:
            pos = self.mapToParent(e.position().toPoint() - self.offset)
            self.move(pos)
            print(f"Breaker x={self.x()} y={self.y()}")

    def mouseReleaseEvent(self, e):
        self.dragging = False
        print(f"FINAL Breaker ({self.x()}, {self.y()})")