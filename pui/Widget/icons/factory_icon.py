from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QColor, QPainter, QPolygon, QFont
from PySide6.QtWidgets import QWidget


class FactoryIcon(QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(150, 90)
        self.dragging = False
        self.offset = None
        self.load_power = 0.0

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True
        )

    def update_data(self, load_power=0.0):
        self.load_power = float(load_power or 0.0)
        
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.dragging:
            p = self.mapToParent(e.position().toPoint() - self.offset)
            self.move(p)

            print(
                f"Factory : x={self.x()} y={self.y()}"
            )

    def mouseReleaseEvent(self, e):
        self.dragging = False

        print(
            f"\nFINAL FACTORY POSITION : "
            f"x={self.x()} y={self.y()}"
        )

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#AEB4BC"))   # grey

        # ================= Base =================
        p.drawRect(15, 58, 42, 20)

        # ================= Roof =================
        roof = QPolygon([
            QPoint(15, 58),

            QPoint(22, 58),
            QPoint(22, 46),

            QPoint(31, 58),
            QPoint(31, 46),

            QPoint(40, 58),
            QPoint(40, 46),

            QPoint(49, 58),
            QPoint(49, 46),

            QPoint(57, 58),
            QPoint(57, 78),

            QPoint(15, 78),
        ])

        p.drawPolygon(roof)

        # ================= Chimney =================
        chimney = QPolygon([
            QPoint(18,18),
            QPoint(26,18),
            QPoint(29,58),
            QPoint(15,58),
        ])

        p.drawPolygon(chimney)

        # Chimney Cap
        p.drawRect(17,10,10,7)

        # ================= Windows =================
        p.setBrush(QColor("#FFFFFF"))

        p.drawRect(20,63,6,8)
        p.drawRect(30,63,6,8)
        p.drawRect(40,63,6,8)
        p.drawRect(50,63,4,8)

        # ================= Bottom Line =================
        p.setBrush(QColor("#AEB4BC"))
        p.drawRect(12,79,48,3)

        # ================= LOAD TEXT - RIGHT SIDE =================

        # LOAD
        p.setPen(QColor("#333333"))

        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        p.setFont(font)

        p.drawText(
            QRect(70, 25, 75, 20),
            Qt.AlignLeft | Qt.AlignVCenter,
            "LOAD"
        )

        # VALUE
        font = QFont()
        font.setPointSize(7)
        font.setBold(False)
        p.setFont(font)

        p.drawText(
            QRect(70, 43, 75, 20),
            Qt.AlignLeft | Qt.AlignVCenter,
            f"{self.load_power / 1000:.2f} MW"
        )