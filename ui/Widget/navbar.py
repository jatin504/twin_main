from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QButtonGroup


class NavBar(QWidget):

    tabChanged = Signal(int)

    def __init__(self):
        super().__init__()

        self.setFixedHeight(34)

        self.setStyleSheet("""
        QWidget{
            background:#F7F9FC;
            border-top:1px solid #D8DEE8;
            border-bottom:1px solid #D8DEE8;
        }

        QPushButton{
            background:transparent;
            border:none;
            color:#6B7280;
            font-size:11px;
            font-weight:600;
            padding:6px 2px;
        }

        QPushButton:hover{
            color:#111827;
        }

        QPushButton:checked{
            color:#111827;
            border-bottom:2px solid #2196F3;
            font-weight:700;
        }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 0, 0)
        layout.setSpacing(28)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        tabs = [
            "OVERVIEW",
            "POWER FLOW",
            "VOLTAGE PROFILE",
            "TIME SERIES",
            "EVENTS",
            "REPORTS",
        ]

        for i, text in enumerate(tabs):
            btn = QPushButton(text)
            btn.setCheckable(True)

            if i == 1:
                btn.setChecked(True)

            self.group.addButton(btn, i)
            layout.addWidget(btn)

        layout.addStretch()

        self.group.idClicked.connect(self.tabChanged.emit)