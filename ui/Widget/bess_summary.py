from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class BessSummaryWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("BessSummaryWidget")
        self.setFixedSize(480, 250)

        self.setStyleSheet("""
            QFrame#BessSummaryWidget {
                background: #FFFFFF;
                border: 1px solid #D9E0E6;
                border-radius: 4px;
            }

            QLabel#title {
                background: #F4F6F8;
                color: #17212B;
                border: none;
                padding: 4px 8px;
                font-family: Arial;
                font-size: 12px;
                font-weight: bold;
            }

            QTableWidget {
                background: #FFFFFF;
                color: #263238;
                border: none;
                gridline-color: #DDE3E8;
                font-family: Arial;
                font-size: 10px;
                selection-background-color: #EAF2F8;
                selection-color: #263238;
            }

            QTableWidget::item {
                padding: 0px 3px;
                border-bottom: 1px solid #E5E9ED;
            }

            QHeaderView::section {
                background: #F8F9FA;
                color: #4D5B66;
                border: none;
                border-right: 1px solid #DDE3E8;
                border-bottom: 1px solid #DDE3E8;
                padding: 3px 3px;
                font-family: Arial;
                font-size: 9px;
                font-weight: bold;
            }

            QTableCornerButton::section {
                background: #F8F9FA;
                border: none;
            }

            QScrollBar:vertical {
                background: #F5F6F7;
                width: 6px;
            }

            QScrollBar::handle:vertical {
                background: #B8C1C8;
                border-radius: 3px;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        # ==================================================
        # TITLE
        # ==================================================

        self.bank_count = 0
        self.title = QLabel("BESS SUMMARY    |    Total Banks: 0")
        self.title.setObjectName("title")
        self.title.setFixedHeight(25)

        layout.addWidget(self.title)

        # ==================================================
        # TABLE
        # ==================================================

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "Bank",
            "PCS",
            "P (MW)",
            "Q (MVAr)",
            "SOC (%)",
            "Energy (MWh)",
            "Status",
        ])

        self.table.verticalHeader().setVisible(False)

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.table.horizontalHeader().setSectionsMovable(False)

        self.total_table = QTableWidget()
        self.total_table.setColumnCount(7)
        self.total_table.horizontalHeader().setVisible(False)
        self.total_table.verticalHeader().setVisible(False)
        self.total_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.total_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.total_table.setFrameShape(QFrame.NoFrame)
        self.total_table.setFixedHeight(25)

        # ==================================================
        # COLUMN WIDTH
        # ==================================================

        header = self.table.horizontalHeader()
        total_header = self.total_table.horizontalHeader()

        for column in range(7):
            header.setSectionResizeMode(
                column,
                QHeaderView.Fixed
            )
            total_header.setSectionResizeMode(
                column,
                QHeaderView.Fixed
            )

        column_widths = [72, 48, 58, 60, 58, 86, 84]
        for column, width in enumerate(column_widths):
            self.table.setColumnWidth(column, width)
            self.total_table.setColumnWidth(column, width)

        layout.addWidget(self.table)
        layout.addWidget(self.total_table)

        self.create_table()

    # ==================================================
    # CREATE TABLE
    # ==================================================

    def create_table(self):
        self.set_data([
            [
                "TOTAL",
                "",
                "0.00",
                "0.00",
                "0 (Avg.)",
                "0.00 / 0.00",
                "",
            ],
        ])

    # ==================================================
    # SET DATA
    # ==================================================

    def set_data(self, data):
        bank_rows = data[:-1]
        total_row = data[-1]

        self.table.setRowCount(len(bank_rows))
        for row, row_data in enumerate(bank_rows):
            self._set_table_row(self.table, row, row_data)

        self.total_table.setRowCount(1)
        self._set_table_row(self.total_table, 0, total_row, is_total=True)

    def _set_table_row(self, table, row_index, row_data, is_total=False):
        table.setRowHeight(row_index, 24)

        for column, value in enumerate(row_data):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor("#263238"))
            table.setItem(row_index, column, item)

        soc_item = table.item(row_index, 4)
        if soc_item and not is_total:
            soc_item.setForeground(QColor("#25A244"))

        status_item = table.item(row_index, 6)
        if status_item:
            status = status_item.text().lower()
            if status == "discharging":
                status_item.setForeground(QColor("#25A244"))
            elif status == "standby":
                status_item.setForeground(QColor("#263238"))

            status_item.setFont(QFont("Arial", 9, QFont.Bold))

        if is_total:
            for column in range(7):
                item = table.item(row_index, column)
                if item:
                    item.setFont(QFont("Arial", 9, QFont.Bold))

    # ==================================================
    # UPDATE
    # ==================================================

    def update_bess_data(self, data):

        if not data:
            return

        bank_count = len(data)
        self.bank_count = bank_count
        self.title.setText(
            f"BESS SUMMARY    |    Total Banks: {bank_count}"
        )

        total_power = 0.0
        total_q = 0.0
        total_soc = 0.0
        total_energy = 0.0

        for row in data:
            total_power += float(row[2])
            total_q += float(row[3])
            total_soc += float(row[4])

            energy = row[5].split("/")[0].strip()
            total_energy += float(energy)

        avg_soc = total_soc / bank_count
        total_capacity = bank_count * 2.00

        table_data = list(data)
        table_data.append([
            "TOTAL",
            "",
            f"{total_power:.2f}",
            f"{total_q:.2f}",
            f"{avg_soc:.0f} (Avg.)",
            f"{total_energy:.2f} / {total_capacity:.2f}",
            "",
        ])

        self.set_data(table_data)