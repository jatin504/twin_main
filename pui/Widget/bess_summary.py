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
        self.setFixedSize(600, 190)

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

        title = QLabel("BESS SUMMARY")
        title.setObjectName("title")
        title.setFixedHeight(25)

        layout.addWidget(title)

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

        # ==================================================
        # COLUMN WIDTH
        # ==================================================

        header = self.table.horizontalHeader()

        for column in range(7):
            header.setSectionResizeMode(
                column,
                QHeaderView.Fixed
            )

        self.table.setColumnWidth(0, 105)
        self.table.setColumnWidth(1, 55)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(4, 65)
        self.table.setColumnWidth(5, 105)
        self.table.setColumnWidth(6, 100)

        layout.addWidget(self.table)

        self.create_table()

    # ==================================================
    # CREATE TABLE
    # ==================================================

    def create_table(self):
        self.set_data([
            [
                "BESS BANK-1",
                "PCS-1",
                "0.00",
                "0.00",
                "0",
                "0.00 / 2.00",
                "Standby",
            ],
            [
                "BESS BANK-2",
                "PCS-2",
                "0.00",
                "0.00",
                "0",
                "0.00 / 2.00",
                "Standby",
            ],
            [
                "BESS BANK-3",
                "PCS-3",
                "0.00",
                "0.00",
                "0",
                "0.00 / 2.00",
                "Standby",
            ],
            [
                "BESS BANK-4",
                "PCS-4",
                "0.00",
                "0.00",
                "0",
                "0.00 / 2.00",
                "Standby",
            ],
            [
                "TOTAL",
                "",
                "0.00",
                "0.00",
                "0 (Avg.)",
                "0.00 / 8.00",
                "",
            ],
        ])

    # ==================================================
    # SET DATA
    # ==================================================

    def set_data(self, data):

        self.table.setRowCount(len(data))

        for row, row_data in enumerate(data):

            self.table.setRowHeight(row, 24)

            for column, value in enumerate(row_data):

                item = QTableWidgetItem(str(value))

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                item.setForeground(
                    QColor("#263238")
                )

                self.table.setItem(
                    row,
                    column,
                    item
                )

            # ==================================================
            # SOC COLOR
            # ==================================================

            soc_item = self.table.item(row, 4)

            if soc_item and row < 4:

                soc_item.setForeground(
                    QColor("#25A244")
                )

            # ==================================================
            # STATUS COLOR
            # ==================================================

            status_item = self.table.item(row, 6)

            if status_item:

                status = status_item.text().lower()

                if status == "discharging":

                    status_item.setForeground(
                        QColor("#25A244")
                    )

                elif status == "standby":

                    status_item.setForeground(
                        QColor("#263238")
                    )

                status_item.setFont(
                    QFont(
                        "Arial",
                        9,
                        QFont.Bold
                    )
                )

            # ==================================================
            # TOTAL ROW
            # ==================================================

            if row == len(data) - 1:

                for column in range(7):

                    item = self.table.item(
                        row,
                        column
                    )

                    if item:

                        item.setFont(
                            QFont(
                                "Arial",
                                9,
                                QFont.Bold
                            )
                        )

    # ==================================================
    # UPDATE
    # ==================================================

    def update_bess_data(self, data):

        if not data:
            return

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

        avg_soc = total_soc / len(data)

        data.append([
            "TOTAL",
            "",
            f"{total_power:.2f}",
            f"{total_q:.2f}",
            f"{avg_soc:.0f} (Avg.)",
            f"{total_energy:.2f} / 8.00",
            "",
        ])

        self.set_data(data)