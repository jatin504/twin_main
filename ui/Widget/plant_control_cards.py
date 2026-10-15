from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt


class PlantControlCard(QFrame):

    def __init__(
        self,
        transformer_id="T1",
        initial_values=None,
        parent=None,
    ):
        super().__init__(parent)

        self.transformer_id = transformer_id

        initial_values = initial_values or {}
        r_pu = float(initial_values.get("r_pu", 0.01))
        x_pu = float(initial_values.get("x_pu", 0.04))

        self.setFixedSize(270, 210)

        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 8px;
            }

            QLabel#transformerTitle {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 700;
                background: #2563EB;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
            }

            QLabel#fieldLabel {
                color: #64748B;
                font-size: 10px;
            }

            QDoubleSpinBox {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 7px;
                padding: 4px;
                color: #172B4D;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 7px;
                color: #172B4D;
                font-size: 11px;
                text-align: left;
                padding-left: 12px;
            }

            QPushButton:hover {
                background: #F8FAFC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # ==================================================
        # TRANSFORMER ID TITLE
        # ==================================================

        title_label = QLabel(
            f"🔌  {self.transformer_id}"
        )
        title_label.setObjectName("transformerTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(28)

        layout.addWidget(title_label)

        # ==================================================
        # R / X LABELS
        # ==================================================

        impedance_labels = QHBoxLayout()
        impedance_labels.setSpacing(6)

        r_label = QLabel("R")
        r_label.setObjectName("fieldLabel")
        r_label.setAlignment(Qt.AlignCenter)

        x_label = QLabel("X")
        x_label.setObjectName("fieldLabel")
        x_label.setAlignment(Qt.AlignCenter)

        impedance_labels.addWidget(r_label)
        impedance_labels.addWidget(x_label)

        layout.addLayout(impedance_labels)

        # ==================================================
        # R / X VALUES
        # ==================================================

        self.r_input = QDoubleSpinBox()
        self.r_input.setRange(0.0, 10.0)
        self.r_input.setDecimals(4)
        self.r_input.setSingleStep(0.01)
        self.r_input.setValue(r_pu)
        self.r_input.setButtonSymbols(
            QDoubleSpinBox.NoButtons
        )

        self.x_input = QDoubleSpinBox()
        self.x_input.setRange(0.0, 10.0)
        self.x_input.setDecimals(4)
        self.x_input.setSingleStep(0.01)
        self.x_input.setValue(x_pu)
        self.x_input.setButtonSymbols(
            QDoubleSpinBox.NoButtons
        )

        # Unit boxes
        r_unit = QLabel("pu")
        r_unit.setAlignment(Qt.AlignCenter)
        r_unit.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 7px;
                color: #64748B;
                font-size: 10px;
            }
        """)

        x_unit = QLabel("pu")
        x_unit.setAlignment(Qt.AlignCenter)
        x_unit.setStyleSheet("""
            QLabel {
                background: #FFFFFF;
                border: 1px solid #DDE5EE;
                border-radius: 7px;
                color: #64748B;
                font-size: 10px;
            }
        """)

        # Put value + unit together
        r_box = QHBoxLayout()
        r_box.setSpacing(4)
        r_box.addWidget(self.r_input)
        r_box.addWidget(r_unit)

        x_box = QHBoxLayout()
        x_box.setSpacing(4)
        x_box.addWidget(self.x_input)
        x_box.addWidget(x_unit)

        impedance_values = QHBoxLayout()
        impedance_values.setSpacing(6)

        impedance_values.addLayout(r_box)
        impedance_values.addLayout(x_box)

        layout.addLayout(impedance_values)

        # ==================================================
        # GRID VOLTAGE BUTTON
        # ==================================================

        self.grid_voltage_button = QPushButton(
            "⚡  Grid Voltage"
        )
        self.grid_voltage_button.setFixedHeight(32)
        self.grid_voltage_button.setFocusPolicy(
            Qt.NoFocus
        )

        # ==================================================
        # GRID FREQUENCY BUTTON
        # ==================================================

        self.grid_frequency_button = QPushButton(
            "〽  Grid Frequency"
        )
        self.grid_frequency_button.setFixedHeight(32)
        self.grid_frequency_button.setFocusPolicy(
            Qt.NoFocus
        )

        # ==================================================
        # GRID AVAILABILITY BUTTON
        # ==================================================

        self.grid_availability_button = QPushButton(
            "◉  Grid Availability"
        )
        self.grid_availability_button.setFixedHeight(32)
        self.grid_availability_button.setFocusPolicy(
            Qt.NoFocus
        )

        layout.addWidget(
            self.grid_voltage_button
        )

        layout.addWidget(
            self.grid_frequency_button
        )

        layout.addWidget(
            self.grid_availability_button
        )

        layout.addStretch()

    # ======================================================
    # IMPEDANCE
    # ======================================================

    def get_impedance(self):

        return {
            "r_pu": self.r_input.value(),
            "x_pu": self.x_input.value(),
        }

    def get_transformer_id(self):
        return self.transformer_id


class PlantControlCards(QWidget):
    """
    Dynamically creates one PlantControlCard per transformer
    found in the YAML data.
    """

    def __init__(
        self,
        transformer_list=None,
        parent=None,
    ):
        super().__init__(parent)

        # transformer_list is a list of dicts:
        # [
        #   {"id": "T1", "r_pu": 0.01, "x_pu": 0.04},
        #   {"id": "T2", "r_pu": 0.01, "x_pu": 0.04},
        #   ...
        # ]
        transformer_list = transformer_list or []

        self.setFixedHeight(220)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(8)

        # ==================================================
        # DYNAMIC TRANSFORMER CARDS
        # ==================================================

        self.cards = {}

        for tx in transformer_list:
            tx_id = tx.get("id", "T?")

            card = PlantControlCard(
                transformer_id=tx_id,
                initial_values={
                    "r_pu": tx.get("r_pu", 0.01),
                    "x_pu": tx.get("x_pu", 0.04),
                },
            )

            self.cards[tx_id] = card

            layout.addWidget(card)

        layout.addStretch()

    def get_all_impedances(self):
        """
        Returns a dict keyed by transformer ID:
        {
            "T1": {"r_pu": 0.01, "x_pu": 0.04},
            "T2": {"r_pu": 0.01, "x_pu": 0.04},
            ...
        }
        """
        result = {}
        for tx_id, card in self.cards.items():
            result[tx_id] = card.get_impedance()
        return result

    def get_impedance(self):
        """
        Backward-compatible: returns first card's impedance.
        Prefer get_all_impedances() for multi-transformer use.
        """
        if self.cards:
            first_card = next(iter(self.cards.values()))
            return first_card.get_impedance()
        return {"r_pu": 0.01, "x_pu": 0.04}