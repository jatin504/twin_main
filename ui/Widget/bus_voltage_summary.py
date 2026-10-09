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

        self.bus_data = []
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

        self.scrollArea = QScrollArea()

        self.scrollArea.setFixedHeight(120)

        self.scrollArea.setWidgetResizable(False)

        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scrollArea.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scrollArea.setFrameShape(
            QFrame.NoFrame
        )

        self.scrollArea.setStyleSheet("""
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

        table.setFixedHeight(1)

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

        # ==================================================
        # SET TABLE INTO SCROLL
        # ==================================================

        self.scrollArea.setWidget(table)

        main_layout.addWidget(self.scrollArea)

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

        self.total_label = QLabel(
            f"Total Buses: {len(self.bus_data)}"
        )

        self.total_label.setFixedHeight(15)

        self.total_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #374151;
                border: none;
                font-size: 6px;
            }
        """)

        footer_layout.addWidget(
            self.total_label
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
        if not profile:
            return

        self.bus_data = [
            (bus_key, bus_key.replace("_", " "), float(voltage))
            for bus_key, voltage in profile.items()
        ]
        bus_keys = [bus_key for bus_key, _, _ in self.bus_data]
        self.total_label.setText(
            f"Total Buses: {len(self.bus_data)}"
        )

        table = self.scrollArea.widget()
        if table is None:
            return

        table_layout = table.layout()
        if list(self.bus_rows) != bus_keys:
            row_height = 14

            while table_layout.count():
                item = table_layout.takeAt(0)
                row = item.widget()
                if row is not None:
                    row.deleteLater()

            self.bus_rows.clear()

            for bus_number, (bus_key, name, voltage) in enumerate(
                self.bus_data,
                start=1,
            ):
                row = QWidget()
                row.setFixedHeight(row_height)
                row.setStyleSheet("""
                    QWidget {
                        background: #FFFFFF;
                        border: none;
                    }
                """)

                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(8, 0, 0, 0)
                row_layout.setSpacing(0)

                bus = QLabel(str(bus_number))
                bus.setFixedWidth(32)
                self.style_label(bus)
                row_layout.addWidget(bus)

                name_label = QLabel(name)
                name_label.setFixedWidth(145)
                self.style_label(name_label)
                row_layout.addWidget(name_label)

                voltage_label = QLabel(f"{voltage:.3f}")
                voltage_label.setFixedWidth(70)
                self.style_label(voltage_label)
                row_layout.addWidget(voltage_label)

                status = QLabel("●")
                status.setFixedWidth(30)
                row_layout.addWidget(status)
                table_layout.addWidget(row)

                self.bus_rows[bus_key] = {
                    "row": row,
                    "voltage_label": voltage_label,
                    "status": status,
                }

            table.setFixedHeight(
                max(1, len(self.bus_data) * row_height)
            )

        for bus_key, _, voltage in self.bus_data:
            row_data = self.bus_rows[bus_key]
            row_data["voltage_label"].setText(f"{voltage:.3f}")

            color = "#36B24A" if voltage > 0 else "#E53935"
            row_data["status"].setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    background: transparent;
                    border: none;
                    font-size: 7px;
                }}
            """)