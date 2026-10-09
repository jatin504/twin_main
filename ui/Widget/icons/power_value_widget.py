from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class PowerValueWidget(QWidget):

    def __init__(self, mw, mvar):
        super().__init__()

        self.setFixedSize(78, 40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 1, 0, 0)
        layout.setSpacing(0)

        mwLbl = QLabel(mw)
        mwLbl.setStyleSheet("""
        QLabel{
            color:#27B63A;
            font-size:9px;
            font-weight:600;
        }
        """)

        mvarLbl = QLabel(mvar)
        mvarLbl.setStyleSheet("""
        QLabel{
            color:#27B63A;
            font-size:9px;
            font-weight:600;
        }
        """)

        layout.addWidget(mwLbl)
        layout.addWidget(mvarLbl)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Green line
        p.setPen(QPen(QColor("#27B63A"), 2))

        # 20px vertical line
        p.drawLine(8, 28, 8, 8)

        # Up arrow
        arrow = QPolygon([
            QPoint(8, 4),
            QPoint(4, 10),
            QPoint(12, 10),
        ])

        p.setBrush(QColor("#27B63A"))
        p.setPen(Qt.NoPen)
        p.drawPolygon(arrow)