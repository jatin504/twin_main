from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class LTPanelBox(QWidget):
    """Single LT panel / space provision box."""

    def __init__(self, title, rating="", connection="", parent=None):
        super().__init__(parent)

        self.title = title
        self.rating = rating
        self.connection = connection

        # Reference-image size
        self.setFixedSize(140, 18)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        green = QColor("#24D94F")
        blue = QColor("#0639D8")
        magenta = QColor("#D51BFF")

        # Main green rectangle
        p.setPen(QPen(green, 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(3, 3, self.width() - 7, self.height() - 7)

        center_x = self.width() // 2

        # Bottom magenta connection point
        p.setBrush(magenta)
        p.drawEllipse(center_x - 2, self.height() - 5, 4, 4)

        p.setPen(blue)

        title_font = QFont("Arial", 7)
        p.setFont(title_font)

        p.drawText(
            QRect(8, 2, self.width() - 16, 12),
            Qt.AlignCenter,
            self.title,
        )


class MainLTPanel1(LTPanelBox):
    def __init__(self, parent=None):
        super().__init__(
            "MAIN_LT_PANEL1",
            parent=parent,
        )


class MainLTPanel2(LTPanelBox):
    def __init__(self, parent=None):
        super().__init__(
            "MAIN_LT_PANEL2",
            parent=parent,
        )


class SpaceProvision(LTPanelBox):
    def __init__(self, parent=None):
        super().__init__(
            "SPACE_PROVISION",
            parent=parent,
        )


class LTPanelGroup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 76)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.move(800, 83)

        self.mainLTPanel1 = MainLTPanel1(self)
        self.mainLTPanel1.setObjectName("MAIN_LT_PANEL1")
        self.mainLTPanel1.move(8, 12)

        self.mainLTPanel2 = MainLTPanel2(self)
        self.mainLTPanel2.setObjectName("MAIN_LT_PANEL2")
        self.mainLTPanel2.move(8, 32)

        self.spaceProvision = SpaceProvision(self)
        self.spaceProvision.setObjectName("SPACE_PROVISION")
        self.spaceProvision.move(8, 52)

        for panel in (
            self.mainLTPanel1,
            self.mainLTPanel2,
            self.spaceProvision,
        ):
            panel.show()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#24D94F"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(1, 1, self.width() - 3, self.height() - 3)

        header_rect = QRect(5, 1, 78, 11)
        p.fillRect(header_rect, QColor("#FFFFFF"))
        p.setPen(QColor("#E23C3C"))
        header_font = QFont("Arial", 6)
        header_font.setBold(True)
        p.setFont(header_font)
        p.drawText(header_rect.adjusted(2, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, "SERVICE BLOCK")
