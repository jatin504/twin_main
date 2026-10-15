from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QWidget,
)


class BessSummaryWidget(QFrame):
    """
    Combined BESS Summary & Bus Voltage Summary widget with integrated modern tab buttons.
    Allows switching between BESS Bank telemetry and Bus Voltage Status in a compact 480x250 card.
    """

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

            QTableWidget {
                background: #FFFFFF;
                color: #263238;
                border: 1px solid #E5E9ED;
                border-bottom: none;
                gridline-color: #DDE3E8;
                font-family: Arial, sans-serif;
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
                font-family: Arial, sans-serif;
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

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # Self-reference for backward compatibility with existing callers
        self.bus_voltage_widget = self

        # State tracking
        self.bank_count = 0
        self.bus_data = {}
        self.bus_rows = {}

        # ==================================================
        # 1. TAB BAR (Segmented Control Header)
        # ==================================================
        tab_bar = QWidget()
        tab_bar.setFixedHeight(28)
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(2, 0, 2, 0)
        tab_layout.setSpacing(6)

        self.tab_bess_btn = QPushButton("⚡ BESS SUMMARY")
        self.tab_bess_btn.setCheckable(True)
        self.tab_bess_btn.setChecked(True)
        self.tab_bess_btn.setCursor(Qt.PointingHandCursor)

        self.tab_bus_btn = QPushButton("📊 BUS VOLTAGES")
        self.tab_bus_btn.setCheckable(True)
        self.tab_bus_btn.setChecked(False)
        self.tab_bus_btn.setCursor(Qt.PointingHandCursor)

        tab_style = """
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-family: Arial, sans-serif;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background: #E2E8F0;
                color: #0F172A;
            }
            QPushButton:checked {
                background: #2563EB;
                color: #FFFFFF;
                border: 1px solid #2563EB;
            }
        """
        self.tab_bess_btn.setStyleSheet(tab_style)
        self.tab_bus_btn.setStyleSheet(tab_style)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)
        self.tab_group.addButton(self.tab_bess_btn, 0)
        self.tab_group.addButton(self.tab_bus_btn, 1)

        tab_layout.addWidget(self.tab_bess_btn)
        tab_layout.addWidget(self.tab_bus_btn)
        tab_layout.addStretch()

        self.tab_info_badge = QLabel("Total Banks: 0")
        self.tab_info_badge.setStyleSheet(
            "color: #475569; font-size: 9.5px; font-weight: 600; border: none; padding-right: 2px;"
        )
        tab_layout.addWidget(self.tab_info_badge)
        root.addWidget(tab_bar)

        # ==================================================
        # 2. STACKED PAGES
        # ==================================================
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # --------------------------------------------------
        # PAGE 0: BESS SUMMARY TABLE
        # --------------------------------------------------
        self.bess_page = QWidget()
        bess_layout = QVBoxLayout(self.bess_page)
        bess_layout.setContentsMargins(0, 0, 0, 0)
        bess_layout.setSpacing(0)

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
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.horizontalHeader().setSectionsMovable(False)

        self.total_table = QTableWidget()
        self.total_table.setColumnCount(7)
        self.total_table.horizontalHeader().setVisible(False)
        self.total_table.verticalHeader().setVisible(False)
        self.total_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.total_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.total_table.setFrameShape(QFrame.NoFrame)
        self.total_table.setFixedHeight(25)
        self.total_table.setStyleSheet("""
            QTableWidget {
                background: #F8FAFC;
                color: #1E293B;
                border: 1px solid #E5E9ED;
                gridline-color: #DDE3E8;
                font-family: Arial, sans-serif;
                font-size: 10px;
                font-weight: bold;
            }
        """)

        header = self.table.horizontalHeader()
        total_header = self.total_table.horizontalHeader()

        for column in range(7):
            header.setSectionResizeMode(column, QHeaderView.Fixed)
            total_header.setSectionResizeMode(column, QHeaderView.Fixed)

        column_widths = [72, 48, 58, 60, 58, 86, 84]
        for column, width in enumerate(column_widths):
            self.table.setColumnWidth(column, width)
            self.total_table.setColumnWidth(column, width)

        bess_layout.addWidget(self.table, 1)
        bess_layout.addWidget(self.total_table)
        self.stack.addWidget(self.bess_page)

        # --------------------------------------------------
        # PAGE 1: BUS VOLTAGE SUMMARY
        # --------------------------------------------------
        self.bus_page = QWidget()
        bus_layout = QVBoxLayout(self.bus_page)
        bus_layout.setContentsMargins(0, 0, 0, 0)
        bus_layout.setSpacing(0)

        # Fixed Header for Bus Voltage
        bus_header = QWidget()
        bus_header.setFixedHeight(24)
        bus_header.setStyleSheet("background: #F8FAFC; border: 1px solid #DCE3EC; border-bottom: none;")
        bus_header_layout = QHBoxLayout(bus_header)
        bus_header_layout.setContentsMargins(8, 0, 8, 0)
        bus_header_layout.setSpacing(0)

        lbl_b = QLabel("Bus")
        lbl_b.setFixedWidth(40)
        lbl_b.setStyleSheet("color: #64748B; font-size: 8.5px; font-weight: bold; border: none;")
        bus_header_layout.addWidget(lbl_b)

        lbl_n = QLabel("BUS NAME")
        lbl_n.setFixedWidth(190)
        lbl_n.setStyleSheet("color: #64748B; font-size: 8.5px; font-weight: bold; border: none;")
        bus_header_layout.addWidget(lbl_n)

        lbl_v = QLabel("Voltage (p.u.)")
        lbl_v.setFixedWidth(120)
        lbl_v.setAlignment(Qt.AlignCenter)
        lbl_v.setStyleSheet("color: #64748B; font-size: 8.5px; font-weight: bold; border: none;")
        bus_header_layout.addWidget(lbl_v)

        lbl_s = QLabel("Status")
        lbl_s.setFixedWidth(80)
        lbl_s.setAlignment(Qt.AlignCenter)
        lbl_s.setStyleSheet("color: #64748B; font-size: 8.5px; font-weight: bold; border: none;")
        bus_header_layout.addWidget(lbl_s)

        bus_layout.addWidget(bus_header)

        # Scrollable Rows Area
        self.bus_scroll = QScrollArea()
        self.bus_scroll.setWidgetResizable(True)
        self.bus_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.bus_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.bus_scroll.setFrameShape(QFrame.NoFrame)
        self.bus_scroll.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-top: none;
                border-bottom: none;
            }
            QScrollBar:vertical {
                width: 6px;
                background: #F1F3F5;
            }
            QScrollBar::handle:vertical {
                background: #BEC5CC;
                border-radius: 3px;
                min-height: 20px;
            }
        """)

        self.bus_container = QWidget()
        self.bus_container.setStyleSheet("background: #FFFFFF;")
        self.bus_rows_layout = QVBoxLayout(self.bus_container)
        self.bus_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.bus_rows_layout.setSpacing(0)
        self.bus_scroll.setWidget(self.bus_container)
        bus_layout.addWidget(self.bus_scroll, 1)

        # Smooth mouse wheel scrolling handler
        def _bus_wheel(event):
            delta = event.angleDelta().y()
            sb = self.bus_scroll.verticalScrollBar()
            sb.setValue(sb.value() - int(delta / 4))
            event.accept()
        self.bus_scroll.wheelEvent = _bus_wheel

        # Footer for Bus Voltage
        bus_footer = QWidget()
        bus_footer.setFixedHeight(24)
        bus_footer.setStyleSheet("background: #F8FAFC; border: 1px solid #DCE3EC; border-top: 1px solid #E5E7EB;")
        bus_footer_layout = QHBoxLayout(bus_footer)
        bus_footer_layout.setContentsMargins(8, 0, 8, 0)
        bus_footer_layout.setSpacing(8)

        self.bus_total_lbl = QLabel("Total Buses: 0")
        self.bus_total_lbl.setStyleSheet("color: #475569; font-size: 8.5px; font-weight: 600; border: none;")
        bus_footer_layout.addWidget(self.bus_total_lbl)
        bus_footer_layout.addStretch()

        g_dot = QLabel("● > 0.95 p.u.")
        g_dot.setStyleSheet("color: #16A34A; font-size: 8px; font-weight: 700; border: none;")
        bus_footer_layout.addWidget(g_dot)

        o_dot = QLabel("● ≤ 0.95 p.u.")
        o_dot.setStyleSheet("color: #D97706; font-size: 8px; font-weight: 700; border: none;")
        bus_footer_layout.addWidget(o_dot)

        bus_layout.addWidget(bus_footer)
        self.stack.addWidget(self.bus_page)

        # Tab Switching Connectors
        self.tab_bess_btn.clicked.connect(lambda: self._switch_tab(0))
        self.tab_bus_btn.clicked.connect(lambda: self._switch_tab(1))

        self.create_table()

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.tab_bess_btn.setChecked(True)
            self.tab_bus_btn.setChecked(False)
            self.tab_info_badge.setText(f"Total Banks: {self.bank_count}")
        else:
            self.tab_bess_btn.setChecked(False)
            self.tab_bus_btn.setChecked(True)
            self.tab_info_badge.setText(f"Total Buses: {len(self.bus_data)}")

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
            elif status == "charging":
                status_item.setForeground(QColor("#0284C7"))
            elif status == "standby":
                status_item.setForeground(QColor("#263238"))

            status_item.setFont(QFont("Arial", 9, QFont.Bold))

        if is_total:
            for column in range(7):
                item = table.item(row_index, column)
                if item:
                    item.setFont(QFont("Arial", 9, QFont.Bold))

    # ==================================================
    # UPDATE BESS TELEMETRY
    # ==================================================
    def update_bess_data(self, data):
        if not data:
            return

        bank_count = len(data)
        self.bank_count = bank_count
        if self.stack.currentIndex() == 0:
            self.tab_info_badge.setText(f"Total Banks: {bank_count}")

        total_power = 0.0
        total_q = 0.0
        total_soc = 0.0
        total_energy = 0.0

        for row in data:
            try:
                total_power += float(row[2])
                total_q += float(row[3])
                total_soc += float(row[4])
                energy = str(row[5]).split("/")[0].strip()
                total_energy += float(energy)
            except (ValueError, IndexError):
                pass

        avg_soc = (total_soc / bank_count) if bank_count > 0 else 0.0
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

    # ==================================================
    # UPDATE BUS VOLTAGE TELEMETRY
    # ==================================================
    def update_voltage_data(self, profile):
        if not profile:
            return

        self.bus_data = profile
        bus_count = len(profile)
        self.bus_total_lbl.setText(f"Total Buses: {bus_count}")
        if self.stack.currentIndex() == 1:
            self.tab_info_badge.setText(f"Total Buses: {bus_count}")

        bus_keys = list(profile.keys())

        # If structure changed, rebuild row widgets
        if list(self.bus_rows.keys()) != bus_keys:
            while self.bus_rows_layout.count():
                item = self.bus_rows_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

            self.bus_rows.clear()

            for idx, (bus_key, val) in enumerate(profile.items(), 1):
                row = QWidget()
                row.setFixedHeight(22)
                bg = "#FFFFFF" if idx % 2 == 1 else "#F8FAFC"
                row.setStyleSheet(f"background: {bg}; border: none;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(8, 0, 8, 0)
                rl.setSpacing(0)

                b_num = QLabel(str(idx))
                b_num.setFixedWidth(40)
                b_num.setStyleSheet("color: #64748B; font-size: 8.5px; border: none;")
                rl.addWidget(b_num)

                b_name = QLabel(bus_key.replace("_", " "))
                b_name.setFixedWidth(190)
                b_name.setStyleSheet("color: #1E293B; font-size: 8.5px; font-weight: 600; border: none;")
                rl.addWidget(b_name)

                v_val = float(val) if val is not None else 1.0
                v_lbl = QLabel(f"{v_val:.3f}")
                v_lbl.setFixedWidth(120)
                v_lbl.setAlignment(Qt.AlignCenter)
                v_lbl.setStyleSheet("color: #1E293B; font-size: 8.5px; font-weight: bold; border: none;")
                rl.addWidget(v_lbl)

                col = "#16A34A" if v_val > 0.95 else "#D97706"
                stat_lbl = QLabel("● Normal" if v_val > 0.95 else "● Warning")
                stat_lbl.setFixedWidth(80)
                stat_lbl.setAlignment(Qt.AlignCenter)
                stat_lbl.setStyleSheet(f"color: {col}; font-size: 8px; font-weight: 700; border: none;")
                rl.addWidget(stat_lbl)

                self.bus_rows_layout.addWidget(row)
                self.bus_rows[bus_key] = {
                    "v_lbl": v_lbl,
                    "stat_lbl": stat_lbl,
                }

            self.bus_rows_layout.addStretch()

        # Update values smoothly without rebuilding DOM
        for bus_key, val in profile.items():
            if bus_key in self.bus_rows:
                try:
                    v_val = float(val)
                except (ValueError, TypeError):
                    v_val = 1.0
                self.bus_rows[bus_key]["v_lbl"].setText(f"{v_val:.3f}")
                col = "#16A34A" if v_val > 0.95 else "#D97706"
                self.bus_rows[bus_key]["stat_lbl"].setText("● Normal" if v_val > 0.95 else "● Warning")
                self.bus_rows[bus_key]["stat_lbl"].setStyleSheet(
                    f"color: {col}; font-size: 8px; font-weight: 700; border: none;"
                )