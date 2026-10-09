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


class BranchSummaryWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("BranchSummaryWidget")
        self.setFixedSize(400, 250)

        self.setStyleSheet("""
            QFrame#BranchSummaryWidget {
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
                font-size: 9px;
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
                padding: 2px 2px;
                font-family: Arial;
                font-size: 8px;
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

        title = QLabel("BRANCH SUMMARY")
        title.setObjectName("title")
        title.setFixedHeight(25)

        layout.addWidget(title)

        # ==================================================
        # TABLE
        # ==================================================

        self.table = QTableWidget()

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels([
            "From",
            "To",
            "P (MW)",
            "Q (MVar)",
            "Loading (%)",
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
        # COLUMN WIDTH - 400px WIDGET
        # ==================================================

        header = self.table.horizontalHeader()

        for column in range(6):
            header.setSectionResizeMode(
                column,
                QHeaderView.Fixed
            )

        self.table.setColumnWidth(0, 70)   # From
        self.table.setColumnWidth(1, 80)   # To
        self.table.setColumnWidth(2, 55)   # P
        self.table.setColumnWidth(3, 55)   # Q
        self.table.setColumnWidth(4, 70)   # Loading
        self.table.setColumnWidth(5, 50)   # Status

        layout.addWidget(self.table)

        self.create_table()

    # ==================================================
    # CREATE TABLE
    # ==================================================

    def create_table(self):

        data = [
            ["GRID",     "PCC",       "1.75", "0.32", "40", "Closed"],
            ["PCC",      "MAIN BUS",  "1.75", "0.32", "41", "Closed"],
            ["MAIN BUS", "SOLAR BUS", "2.15", "0.05", "35", "Closed"],
            ["MAIN BUS", "PCS-1 BUS", "0.55", "0.00", "42", "Closed"],
            ["MAIN BUS", "PCS-2 BUS", "0.20", "0.00", "38", "Closed"],
            ["MAIN BUS", "PCS-3 BUS", "0.10", "0.00", "36", "Closed"],
            ["MAIN BUS", "PCS-4 BUS", "0.00", "0.00", "0",  "Open"],
            ["MAIN BUS", "LOAD BUS",  "4.25", "0.68", "45", "Closed"],
            ["MAIN BUS", "(Losses)",  "0.05", "0.01", "—",  "—"],
        ]

        self.set_data(data)

    # ==================================================
    # SET DATA
    # ==================================================

    def set_data(self, data):

        self.table.setRowCount(len(data))

        for row, row_data in enumerate(data):

            self.table.setRowHeight(row, 15)

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
            # STATUS COLOR
            # ==================================================

            status_item = self.table.item(row, 5)

            if status_item:

                status = status_item.text().lower()

                if status == "closed":
                    status_item.setForeground(
                        QColor("#25A244")
                    )

                elif status == "open":
                    status_item.setForeground(
                        QColor("#E53935")
                    )

                status_item.setFont(
                    QFont(
                        "Arial",
                        8,
                        QFont.Bold
                    )
                )

            # ==================================================
            # LOADING COLOR
            # ==================================================

            loading_item = self.table.item(row, 4)

            if loading_item:

                try:

                    loading = float(
                        loading_item.text()
                    )

                    if loading >= 80:

                        loading_item.setForeground(
                            QColor("#E53935")
                        )

                    elif loading >= 50:

                        loading_item.setForeground(
                            QColor("#F39C12")
                        )

                    else:

                        loading_item.setForeground(
                            QColor("#25A244")
                        )

                except ValueError:
                    pass

    # ==================================================
    # UPDATE
    # ==================================================

    def update_branch_data(self, branches):

        if not branches:
            return

        rows = []

        for branch in branches:

            rows.append([
                branch.get("from", ""),
                branch.get("to", ""),
                f'{branch.get("p", 0):.2f}',
                f'{branch.get("q", 0):.2f}',
                str(branch.get("loading", 0)),
                branch.get("status", "Closed"),
            ])

        self.set_data(rows)