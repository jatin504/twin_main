from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QFrame,
)


class ConfigurationDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.configuration = "builtin"

        # ==================================================
        # FULLSCREEN WHITE WINDOW
        # ==================================================

        self.setWindowTitle("Plant Configuration")
        self.showFullScreen()

        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
            }

            QFrame#card {
                background: #F5F7FA;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }

            QLabel#title {
                color: #111827;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #6B7280;
                font-size: 12px;
            }

            QPushButton#configButton {
                background: #FFFFFF;
                color: #1F2937;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 12px;
                text-align: left;
            }

            QPushButton#configButton:hover {
                background: #F8FAFC;
                border: 1px solid #2563EB;
            }

            QPushButton#continue {
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                font-size: 12px;
                font-weight: 700;
                padding: 10px 28px;
            }

            QPushButton#continue:hover {
                background: #1D4ED8;
            }
        """)

        # ==================================================
        # CENTER CARD
        # ==================================================

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        outer_layout.addStretch()

        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        center_layout.addStretch()

        # Popup/Card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(520)
        card.setMinimumHeight(350)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            32,
            28,
            32,
            28
        )
        card_layout.setSpacing(10)

        # ==================================================
        # TITLE
        # ==================================================

        title = QLabel("Plant Configuration")
        title.setObjectName("title")

        subtitle = QLabel(
            "Select the configuration to use before "
            "starting the Digital Twin."
        )
        subtitle.setObjectName("subtitle")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(12)

        # ==================================================
        # BUILT-IN CONFIGURATION
        # ==================================================

        self.builtin_button = QPushButton()

        self.builtin_button.setObjectName("configButton")
        self.builtin_button.setFixedHeight(72)

        self.builtin_button.setText(
            "Built-in Configuration\n"
            "Use the existing plant configuration"
        )

        self.builtin_button.clicked.connect(
            self.select_builtin
        )

        card_layout.addWidget(
            self.builtin_button
        )

        # ==================================================
        # CUSTOM CONFIGURATION
        # ==================================================

        self.custom_button = QPushButton()

        self.custom_button.setObjectName("configButton")
        self.custom_button.setFixedHeight(72)

        self.custom_button.setText(
            "Custom Configuration\n"
            "Start with a blank dashboard"
        )

        self.custom_button.clicked.connect(
            self.select_custom
        )

        card_layout.addWidget(
            self.custom_button
        )

        card_layout.addSpacing(10)

        # ==================================================
        # CONTINUE BUTTON
        # ==================================================

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)

        buttons.addStretch()

        continue_button = QPushButton(
            "Continue"
        )

        continue_button.setObjectName(
            "continue"
        )

        continue_button.setFixedHeight(42)

        continue_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(
            continue_button
        )

        card_layout.addLayout(buttons)

        center_layout.addWidget(card)

        center_layout.addStretch()

        outer_layout.addLayout(
            center_layout
        )

        outer_layout.addStretch()

        # Default selection
        self.select_builtin()

    # ==================================================
    # BUILT-IN SELECT
    # ==================================================

    def select_builtin(self):

        self.configuration = "builtin"

        self.builtin_button.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #1D4ED8;
                border: 2px solid #2563EB;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 12px;
                text-align: left;
                font-weight: 700;
            }
        """)

        self.custom_button.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #1F2937;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 12px;
                text-align: left;
                font-weight: 400;
            }

            QPushButton:hover {
                background: #F8FAFC;
                border: 1px solid #2563EB;
            }
        """)

    # ==================================================
    # CUSTOM SELECT
    # ==================================================

    def select_custom(self):

        self.configuration = "custom"

        self.custom_button.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #1D4ED8;
                border: 2px solid #2563EB;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 12px;
                text-align: left;
                font-weight: 700;
            }
        """)

        self.builtin_button.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #1F2937;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 12px;
                text-align: left;
                font-weight: 400;
            }

            QPushButton:hover {
                background: #F8FAFC;
                border: 1px solid #2563EB;
            }
        """)

    # ==================================================
    # GET CONFIGURATION
    # ==================================================

    def get_configuration(self):

        return self.configuration