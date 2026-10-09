from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
)


class BankFaultCard(QFrame):

    def __init__(
        self,
        bank_number,
        pcs_number,
        initial_temperature=298.15,
        parent=None
    ):
        super().__init__(parent)

        self.bank_number = bank_number
        self.pcs_number = pcs_number
        self.initial_temperature = float(initial_temperature)

        # ==================================================
        # CARD SIZE
        # ==================================================

        self.setFixedSize(250, 220)

        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 8px;
            }

            QLabel#bankTitle {
                color: #172B4D;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#pcsName {
                color: #64748B;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 10px;
            }

            QLabel#valueTitle {
                color: #64748B;
                font-size: 10px;
            }

            QSpinBox {
                background: #FFFFFF;
                color: #172B4D;
                border: 1px solid #D9E2EC;
                border-radius: 5px;
                padding-left: 8px;
                font-size: 14px;
                font-weight: 600;
            }

            QSpinBox:focus {
                border: 1px solid #2563EB;
            }

            QLabel#percent {
                color: #172B4D;
                font-size: 12px;
            }

            QPushButton {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 10px;
                text-align: left;
            }

            QPushButton:hover {
                background: #F8FAFC;
                border: 1px solid #2563EB;
            }

            QPushButton#voltage {
                color: #D97706;
            }

            QPushButton#temperature {
                color: #DC2626;
            }

            QPushButton#frequency {
                color: #7C3AED;
            }
        """)

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        layout.setSpacing(4)

        # ==================================================
        # HEADER
        # ==================================================

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)

        bank_title = QLabel(
            f"BANK-{bank_number}"
        )

        bank_title.setObjectName(
            "bankTitle"
        )

        pcs_name = QLabel(
            f"PCS-{pcs_number}"
        )

        pcs_name.setObjectName(
            "pcsName"
        )

        title_layout.addWidget(
            bank_title
        )

        title_layout.addWidget(
            pcs_name
        )

        header.addLayout(
            title_layout
        )

        header.addStretch()

        # Online status

        status = QLabel(
            "● Online"
        )

        status.setStyleSheet("""
            QLabel {
                color: #16A34A;
                background: #F0FDF4;
                border: 1px solid #D1FAE5;
                border-radius: 4px;
                padding: 5px 7px;
                font-size: 9px;
                font-weight: 600;
            }
        """)

        header.addWidget(
            status
        )

        layout.addLayout(
            header
        )

        # ==================================================
        # SEPARATOR
        # ==================================================

        line = QFrame()

        line.setFixedHeight(1)

        line.setStyleSheet("""
            QFrame {
                background: #E2E8F0;
                border: none;
            }
        """)

        layout.addWidget(
            line
        )

        # ==================================================
        # SOC / SOH
        # ==================================================

        values_layout = QHBoxLayout()

        values_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        values_layout.setSpacing(5)

        # --------------------------------------------------
        # SOC
        # --------------------------------------------------

        soc_layout = QVBoxLayout()

        soc_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        soc_layout.setSpacing(2)

        soc_title = QLabel(
            "SOC"
        )

        soc_title.setObjectName(
            "valueTitle"
        )

        soc_title.setAlignment(
            Qt.AlignCenter
        )

        soc_row = QHBoxLayout()

        soc_row.setSpacing(2)

        self.soc_value = QSpinBox()

        self.soc_value.setRange(
            0,
            100
        )

        self.soc_value.setValue(
            50
        )

        self.soc_value.setFixedHeight(
            30
        )

        self.soc_value.setButtonSymbols(
            QSpinBox.NoButtons
        )

        soc_percent = QLabel(
            "%"
        )

        soc_percent.setObjectName(
            "percent"
        )

        soc_percent.setAlignment(
            Qt.AlignCenter
        )

        soc_row.addWidget(
            self.soc_value
        )

        soc_row.addWidget(
            soc_percent
        )

        soc_layout.addWidget(
            soc_title
        )

        soc_layout.addLayout(
            soc_row
        )

        # --------------------------------------------------
        # SOH
        # --------------------------------------------------

        soh_layout = QVBoxLayout()

        soh_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        soh_layout.setSpacing(2)

        soh_title = QLabel(
            "SOH"
        )

        soh_title.setObjectName(
            "valueTitle"
        )

        soh_title.setAlignment(
            Qt.AlignCenter
        )

        soh_row = QHBoxLayout()

        soh_row.setSpacing(2)

        self.soh_value = QSpinBox()

        self.soh_value.setRange(
            0,
            100
        )

        self.soh_value.setValue(
            95
        )

        self.soh_value.setFixedHeight(
            30
        )

        self.soh_value.setButtonSymbols(
            QSpinBox.NoButtons
        )

        soh_percent = QLabel(
            "%"
        )

        soh_percent.setObjectName(
            "percent"
        )

        soh_percent.setAlignment(
            Qt.AlignCenter
        )

        soh_row.addWidget(
            self.soh_value
        )

        soh_row.addWidget(
            soh_percent
        )

        soh_layout.addWidget(
            soh_title
        )

        soh_layout.addLayout(
            soh_row
        )

        values_layout.addLayout(
            soc_layout
        )

        values_layout.addLayout(
            soh_layout
        )

        layout.addLayout(
            values_layout
        )

        # ==================================================
        # FAULT BUTTONS
        # ==================================================

        voltage_button = QPushButton(
            "⚡  Create Voltage Fault"
        )

        voltage_button.setObjectName(
            "voltage"
        )

        voltage_button.setFixedHeight(
            29
        )

        self.temperature_button = QPushButton()

        self.temperature_button.setObjectName("temperature")

        self.temperature_button.setFixedHeight(29)

        self.update_temperature_button()

        frequency_button = QPushButton(
            "〽  Create Frequency Fault"
        )

        frequency_button.setObjectName(
            "frequency"
        )

        frequency_button.setFixedHeight(
            29
        )

        voltage_button.clicked.connect(
            lambda: self.create_fault(
                "voltage"
            )
        )

        self.temperature_button.clicked.connect(
            self.toggle_temperature_fault
        )

        frequency_button.clicked.connect(
            lambda: self.create_fault(
                "frequency"
            )
        )

        layout.addWidget(
            voltage_button
        )

        layout.addWidget(
            self.temperature_button
        )

        layout.addWidget(
            frequency_button
        )

    def set_soc_soh(self, soc, soh):
        self.soc_value.setValue(int(float(soc)))
        self.soh_value.setValue(int(float(soh)))

    def update_temperature_button(self):
        if abs(self.initial_temperature - 298.15) < 0.01:
            self.temperature_button.setText(
                "🌡  Enable Temp Fault"
            )
        elif abs(self.initial_temperature - 329.15) < 0.01:
            self.temperature_button.setText(
                "🌡  Disable Temp Fault"
            )
        else:
            self.temperature_button.setText(
                "🌡  Enable Temp Fault"
            )

    def toggle_temperature_fault(self):
        if abs(self.initial_temperature - 298.15) < 0.01:
            self.initial_temperature = 329.15
            print(
                f"Temperature Fault ENABLED | "
                f"BANK-{self.bank_number} | "
                f"PCS-{self.pcs_number}"
            )
        else:
            self.initial_temperature = 298.15
            print(
                f"Temperature Fault DISABLED | "
                f"BANK-{self.bank_number} | "
                f"PCS-{self.pcs_number}"
            )

        self.update_temperature_button()

    # ==================================================
    # FAULT
    # ==================================================

    def create_fault(self, fault_type):

        print(
            f"FAULT CREATED | "
            f"BANK-{self.bank_number} | "
            f"{fault_type}"
        )

        print(
            f"SOC: {self.soc_value.value()}%"
        )

        print(
            f"SOH: {self.soh_value.value()}%"
        )


# ======================================================
# BANK CARDS
# ======================================================

class BankFaultCards(QWidget):

    def __init__(self, initial_values=None, parent=None):
        super().__init__(parent)

        self.initial_values = initial_values or {}

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # 4 cards ke beech sirf 8px
        layout.setSpacing(8)

        # ==================================================
        # 4 BANKS
        # ==================================================

        for index in range(4):

            pcs_id = f"PCS{index + 1}"
            values = self.initial_values.get(pcs_id, {})

            card = BankFaultCard(
                bank_number=index + 1,
                pcs_number=index + 1,
                initial_temperature=values.get(
                    "Initial_Temperature_K",
                    298.15
                ),
            )

            card.set_soc_soh(
                values.get("SOC", 50),
                values.get("SOH", 100),
            )

            layout.addWidget(
                card
            )

        # Extra blank space right side
        layout.addStretch()