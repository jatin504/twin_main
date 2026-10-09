from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
)


class BusVoltageSummaryWidget(QFrame):

    def __init__(self):
        super().__init__()

        # ==================================================
        # SIZE
        # ==================================================

        self.setFixedWidth(330)
        self.setFixedHeight(200)

        # ==================================================
        # DATA
        # ==================================================

        self.bus_data = [
            ("GRID_11KV", "GRID (Slack)", 0.0),
            ("BUS_690_A", "BUS 690 A", 0.0),
            ("PCS_BUS", "PCS BUS", 0.0),
            ("PV_BUS", "SOLAR PLANT", 0.0),
            ("LOAD_BUS", "PLANT LOAD", 0.0),
        ]
        self.bus_rows = {}

        # ==================================================
        # MAIN STYLE
        # ==================================================

        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 3px;
            }
        """)

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            8, 6, 8, 5
        )

        main_layout.setSpacing(0)

        # ==================================================
        # TITLE
        # ==================================================

        title = QLabel(
            "BUS VOLTAGE SUMMARY"
        )

        title.setFixedHeight(20)

        title.setStyleSheet("""
            QLabel {
                background: #F4F6F9;
                color: #111827;
                border: none;
                font-size: 10px;
                font-weight: bold;
                padding-left: 2px;
            }
        """)

        main_layout.addWidget(title)

        # ==================================================
        # FIXED TABLE HEADER
        # ==================================================

        header = QWidget()

        header.setFixedWidth(280)
        header.setFixedHeight(22)

        header.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(
            8, 0, 0, 0
        )

        header_layout.setSpacing(0)

        self.add_header(
            header_layout,
            "Bus",
            32
        )

        self.add_header(
            header_layout,
            "BUS",
            145
        )

        self.add_header(
            header_layout,
            "Voltage (p.u.)",
            70
        )

        self.add_header(
            header_layout,
            "Status",
            30
        )

        main_layout.addWidget(header)

        # ==================================================
        # SCROLL AREA
        # ==================================================

        scroll = QScrollArea()

        scroll.setFixedHeight(144)

        scroll.setWidgetResizable(False)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        scroll.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: none;
            }

            QScrollBar:vertical {
                width: 7px;
                background: #F1F3F5;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #BEC5CC;
                border-radius: 3px;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #F1F3F5;
            }
        """)

        # ==================================================
        # TABLE CONTENT
        # ==================================================

        table = QWidget()

        table.setFixedWidth(280)

        # IMPORTANT:
        # Content height > scroll height
        # so vertical scrollbar appears

        table.setFixedHeight(
            22 + len(self.bus_data) * 12
        )

        table.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border: none;
            }
        """)

        table_layout = QVBoxLayout(table)

        table_layout.setContentsMargins(
            0, 0, 0, 0
        )

        table_layout.setSpacing(0)

        # header moved above scroll area (fixed)

        # ==================================================
        # ROWS
        # ==================================================

        self.bus_rows = {}

        for bus_no, name, voltage in self.bus_data:

            row = QWidget()

            row.setFixedHeight(12)

            row.setStyleSheet("""
                QWidget {
                    background: #FFFFFF;
                    border: none;
                }
            """)

            row_layout = QHBoxLayout(row)

            row_layout.setContentsMargins(8, 0, 0, 0)
            row_layout.setSpacing(0)

            bus = QLabel("-")
            bus.setFixedWidth(32)
            self.style_label(bus)
            row_layout.addWidget(bus)

            name_label = QLabel(name)
            name_label.setFixedWidth(145)
            self.style_label(name_label)
            row_layout.addWidget(name_label)

            voltage_label = QLabel(
                f"{voltage:.3f}"
            )
            voltage_label.setFixedWidth(70)
            self.style_label(voltage_label)
            row_layout.addWidget(voltage_label)

            status = QLabel("●")
            status.setFixedWidth(30)

            if voltage > 0:
                status.setStyleSheet("""
                    QLabel {
                        color: #36B24A;
                        background: transparent;
                        border: none;
                        font-size: 7px;
                    }
                """)
            else:
                status.setStyleSheet("""
                    QLabel {
                        color: #E53935;
                        background: transparent;
                        border: none;
                        font-size: 7px;
                    }
                """)

            row_layout.addWidget(status)

            table_layout.addWidget(row)

            self.bus_rows[bus_no] = (
                voltage_label,
                status,
            )

        # ==================================================
        # SET TABLE INTO SCROLL
        # ==================================================

        scroll.setWidget(table)

        main_layout.addWidget(scroll)

        # ==================================================
        # FOOTER
        # ==================================================

        footer = QWidget()

        footer.setFixedHeight(35)

        footer.setStyleSheet("""
            QWidget {
                background: #FFFFFF;
                border: none;
            }
        """)

        footer_layout = QVBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            0, 0, 0, 0
        )

        footer_layout.setSpacing(0)

        # ----------------------------------------------
        # DIVIDER
        # ----------------------------------------------

        divider = QFrame()

        divider.setFixedHeight(1)

        divider.setStyleSheet("""
            QFrame {
                background: #E5E7EB;
                border: none;
            }
        """)

        footer_layout.addWidget(
            divider
        )

        # ----------------------------------------------
        # TOTAL BUSES
        # ----------------------------------------------

        total = QLabel(
            f"Total Buses: {len(self.bus_data)}"
        )

        total.setFixedHeight(15)

        total.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #374151;
                border: none;
                font-size: 6px;
            }
        """)

        footer_layout.addWidget(
            total
        )

        # ----------------------------------------------
        # LEGEND
        # ----------------------------------------------

        legend = QWidget()

        legend_layout = QHBoxLayout(
            legend
        )

        legend_layout.setContentsMargins(
            0, 0, 0, 0
        )

        legend_layout.setSpacing(4)

        # Green

        green_dot = QLabel("●")

        green_dot.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #36B24A;
                border: none;
                font-size: 7px;
            }
        """)

        green_text = QLabel(
            "> 0.95 p.u."
        )

        green_text.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #4B5563;
                border: none;
                font-size: 6px;
            }
        """)

        legend_layout.addWidget(
            green_dot
        )

        legend_layout.addWidget(
            green_text
        )

        legend_layout.addSpacing(20)

        # Orange

        orange_dot = QLabel("●")

        orange_dot.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #F59E0B;
                border: none;
                font-size: 7px;
            }
        """)

        orange_text = QLabel(
            "≤ 0.95 p.u."
        )

        orange_text.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #4B5563;
                border: none;
                font-size: 6px;
            }
        """)

        legend_layout.addWidget(
            orange_dot
        )

        legend_layout.addWidget(
            orange_text
        )

        legend_layout.addStretch()

        footer_layout.addWidget(
            legend
        )

        main_layout.addWidget(
            footer
        )

    # ==================================================
    # HELPERS
    # ==================================================

    def style_label(self, label):

        label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #374151;
                border: none;
                font-size: 8px;
            }
        """)

    def add_header(
        self,
        layout,
        text,
        width
    ):

        label = QLabel(text)

        label.setFixedWidth(width)

        label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #6B7280;
                border: none;
                font-size: 8px;
                font-weight: bold;
            }
        """)

        layout.addWidget(label)

    def update_voltage_data(self, profile):

        for bus_key, name, voltage in self.bus_data:

            voltage = float(
                profile.get(bus_key, 0.0)
            )

            if bus_key not in self.bus_rows:
                continue

            voltage_label, status = self.bus_rows[bus_key]

            voltage_label.setText(
                f"{voltage:.3f}"
            )

            if voltage > 0:

                status.setStyleSheet("""
                    QLabel {
                        color: #36B24A;
                        background: transparent;
                        border: none;
                        font-size: 7px;
                    }
                """)

            else:

                status.setStyleSheet("""
                    QLabel {
                        color: #E53935;
                        background: transparent;
                        border: none;
                        font-size: 7px;
                    }
                """)