from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)

# INVERTER DRAWING


class InverterDrawing(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(42, 42)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ===== Top Connector =====

        p.setPen(QPen(QColor("#86A86B"), 2.4))
        p.drawLine(21, 0, 21, 7)

        path = QPainterPath()

        path.moveTo(16, 0)
        path.lineTo(26, 0)
        path.lineTo(23, 7)
        path.lineTo(19, 7)
        path.closeSubpath()

        p.setPen(QPen(QColor("#6E8D59"), 1))
        p.setBrush(QColor("#9CBC79"))

        p.drawPath(path)

        # =================================================
        # OUTER BOX
        # =================================================

        p.setPen(QPen(QColor("#9CA3AF"), 2.8))
        p.setBrush(Qt.NoBrush)

        p.drawRoundedRect(
            3,
            8,
            36,
            31,
            4,
            4
        )

        # =================================================
        # INNER BOX
        # =================================================

        p.setPen(QPen(QColor("#D1D5DB"), 1.5))

        p.drawRoundedRect(
            4,
            9,
            34,
            29,
            4,
            4
        )

        # =================================================
        # DIAGONAL
        # =================================================

        p.setPen(QPen(QColor("#9CA3AF"), 2.2))

        p.drawLine(
            8,
            39,
            34,
            13
        )

        # =================================================
        # TOP WAVE
        # =================================================

        path = QPainterPath()

        path.moveTo(10, 22)

        path.cubicTo(
            11.5, 18,
            14, 18,
            15.5, 22
        )

        path.cubicTo(
            17, 26,
            19.5, 26,
            21, 22
        )

        p.drawPath(path)

        # =================================================
        # BOTTOM WAVE
        # =================================================

        path = QPainterPath()

        path.moveTo(20, 32)

        path.cubicTo(
            21.5, 28,
            24, 28,
            25.5, 32
        )

        path.cubicTo(
            27, 36,
            29.5, 36,
            31, 32
        )

        p.drawPath(path)

        p.end()



# COMPLETE SOLAR INVERTER WIDGET

class InverterIcon5(QWidget):

    def __init__(
        self,
        title="SOLAR INVERTER-1",
        mw="2.15 MW",
        mvar="0.05 MVAr",
        pf="PF 0.99 Lag",
        loading=35,
    ):
        super().__init__()

        # Overall widget
        self.setFixedSize(145, 80)

        # Transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

        # =================================================
        # MAIN HORIZONTAL LAYOUT
        # =================================================

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # LEFT TEXT

        textLayout = QVBoxLayout()

        textLayout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        textLayout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        textLayout.setSpacing(2)

        # ----- Title -----

        titleLabel = QLabel(title)

        titleLabel.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #30343B;
                font-size: 9px;
                font-weight: 700;
            }
        """)

        # ----- MW -----

        mwLabel = QLabel(mw)

        mwLabel.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #404040;
                font-size: 8px;
            }
        """)

        # ----- MVAr -----

        mvarLabel = QLabel(mvar)

        mvarLabel.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #404040;
                font-size: 8px;
            }
        """)

        # ----- PF -----

        pfLabel = QLabel(pf)

        pfLabel.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #404040;
                font-size: 8px;
            }
        """)

        # ----- Loading -----

        loadingLabel = QLabel(
            f"Loading:  {loading} %"
        )

        loadingLabel.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #58B52A;
                font-size: 9px;
                font-weight: 700;
            }
        """)

        # Add text

        textLayout.addWidget(titleLabel)
        textLayout.addWidget(mwLabel)
        textLayout.addWidget(mvarLabel)
        textLayout.addWidget(pfLabel)

        textLayout.addSpacing(5)

        textLayout.addWidget(loadingLabel)

        layout.addLayout(textLayout, 0)

        # =================================================
        # RIGHT INVERTER BOX
        # =================================================

        inverter = InverterDrawing()

        layout.addWidget(
            inverter,
            0,
            Qt.AlignLeft | Qt.AlignTop
        )

        # =================================================
        # NO WHITE BACKGROUND
        # =================================================

        self.setStyleSheet("""
            InverterIcon5 {
                background: transparent;
            }

            QLabel {
                background: transparent;
            }
        """)