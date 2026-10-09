import os
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QWidget,
)


class _ClickableScheduleRow(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class BessDispatchScheduleWidget(QFrame):
    """
    BESS Dispatch Schedule widget.

    Designed as a separate widget so it can be added to MainWindow
    without changing the existing BESS / Branch / Bus widgets.

    Data can be supplied through update_schedule() or load_json().
    Expected schedule item format:

    {
        "time": "15:45 - 16:00",
        "load": 2200,
        "decision": "DISCHARGE",
        "dispatch": 2200
    }

    Optional current interval details:

    {
        "load": 2200,
        "pv": 0,
        "grid_import_limit": 4000,
        "decision": "DISCHARGE",
        "charge": 0,
        "grid_charge": 0,
        "discharge": 2200,
        "soc": 47.88,
        "available_energy": 12.45
    }
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("BessDispatchScheduleWidget")
        self.setFixedSize(630, 250)

        self.schedule_data = []
        self.result_data = {}
        self.current_details = {}
        self.json_file_path = None
        self.json_last_modified = 0
        self.current_twin_load = None
        self.manual_active_index = None
        self.active_row_index = None
        self.running_event_id = None
        self.manual_running_event_id = None
        self.manual_running_timestamp = None
        self.elapsed_seconds = 0
        self.current_window_load = []
        self.schedule_rows = []
        self.schedule_row_labels = []
        self.fullscreen_dialog = None
        self._fullscreen_parent = None
        self._fullscreen_geometry = None

        self.setStyleSheet("""
            QFrame#BessDispatchScheduleWidget {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 4px;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: #F1F3F5;
                width: 6px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #B9C1C8;
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

        root = QVBoxLayout(self)
        root.setContentsMargins(5, 3, 5, 3)
        root.setSpacing(1)

        # =========================================================
        # HEADER
        # =========================================================

        header = QHBoxLayout()
        header.setContentsMargins(3, 0, 3, 0)
        header.setSpacing(4)
        header_widget = QWidget()
        header_widget.setFixedHeight(40)
        header_widget.setLayout(header)

        calendar = QLabel("▣")
        calendar.setFixedWidth(20)
        calendar.setStyleSheet("""
            QLabel {
                color: #173A63;
                font-size: 17px;
                font-weight: bold;
            }
        """)
        header.addWidget(calendar)

        title = QLabel("BESS DISPATCH SCHEDULE")
        title.setStyleSheet("""
            QLabel {
                color: #17324D;
                font-size: 10px;
                font-weight: 800;
            }
        """)
        header.addWidget(title)
        header.addStretch(1)

        time_box = QVBoxLayout()
        time_box.setContentsMargins(0, 0, 0, 0)
        time_box.setSpacing(0)

        self.time_label = QLabel("15:52")
        self.time_label.setAlignment(Qt.AlignRight)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #1671D9;
                font-size: 13px;
                font-weight: 800;
            }
        """)

        self.elapsed_time_top = QLabel("Elapsed: 00:00 / 15m")
        self.elapsed_time_top.setAlignment(Qt.AlignRight)
        self.elapsed_time_top.setStyleSheet("""
            QLabel {
                color: #D97706;
                font-size: 7px;
                font-weight: 700;
            }
        """)

        self.date_label = QLabel("29 Sep 2025")
        self.date_label.setAlignment(Qt.AlignRight)
        self.date_label.setStyleSheet("""
            QLabel {
                color: #526170;
                font-size: 7px;
                font-weight: 600;
            }
        """)

        time_box.addWidget(self.time_label)
        time_box.addWidget(self.elapsed_time_top)
        time_box.addWidget(self.date_label)

        header.addLayout(time_box)
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("⛶")
        self.fullscreen_button.setFixedSize(22, 22)
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.setToolTip("Fullscreen")
        self.fullscreen_button.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #526170;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }
            QToolButton:hover {
                color: #1671D9;
                background: #F1F5F9;
                border-radius: 4px;
            }
        """)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        header.addWidget(self.fullscreen_button)
        root.addWidget(header_widget)

        # DEDICATED ACTIVE EVENT BANNER (Prominent & Never overlaps)
        self.running_event_badge = QFrame()
        self.running_event_badge.setObjectName("RunningEventBadge")
        self.running_event_badge.setFixedHeight(20)
        badge_layout = QHBoxLayout(self.running_event_badge)
        badge_layout.setContentsMargins(6, 1, 6, 1)
        badge_layout.setSpacing(4)

        self.running_dot = QLabel("●")
        self.running_dot.setStyleSheet("color: #94A3B8; font-size: 8px;")

        self.running_event_label = QLabel("RUNNING EVENT ID: NONE")
        self.running_event_label.setStyleSheet("color: #64748B; font-size: 8px; font-weight: 700;")

        self.running_elapsed_badge = QLabel("ELAPSED: 00:00 / 15:00 (Min 1/15)")
        self.running_elapsed_badge.setStyleSheet("color: #B45309; font-size: 7.5px; font-weight: 700;")

        self.running_status_hint = QLabel("STANDBY")
        self.running_status_hint.setStyleSheet("color: #64748B; font-size: 7.5px; font-weight: 700;")

        badge_layout.addWidget(self.running_dot)
        badge_layout.addWidget(self.running_event_label)
        badge_layout.addStretch(1)
        badge_layout.addWidget(self.running_elapsed_badge)
        badge_layout.addWidget(self.running_status_hint)

        self.running_event_badge.setStyleSheet("""
            QFrame#RunningEventBadge {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
            }
        """)
        root.addWidget(self.running_event_badge)

        # =========================================================
        # TOP KPI CARDS
        # =========================================================

        kpi_container = QWidget()
        kpi_container.setFixedHeight(34)
        kpi_row = QHBoxLayout(kpi_container)
        kpi_row.setContentsMargins(0, 0, 0, 0)
        kpi_row.setSpacing(5)

        self.current_load_value = self._create_kpi(
            kpi_row, "Event Load", "2200 kW"
        )
        self.decision_value = self._create_kpi(
            kpi_row, "Decision", "DISCHARGE", decision=True
        )
        self.dispatch_value = self._create_kpi(
            kpi_row, "Energy Dispatch", "550 kWh"
        )
        self.soc_value = self._create_kpi(
            kpi_row, "Target SoC", "47.88 %"
        )

        root.addWidget(kpi_container)

        # =========================================================
        # SCHEDULE HEADER
        # =========================================================

        schedule_frame = QFrame()
        schedule_frame.setStyleSheet("""
            QFrame {
                background: #F8FAFC;
                border: 1px solid #DCE3EC;
                border-radius: 3px;
            }
        """)

        schedule_header = QHBoxLayout(schedule_frame)
        schedule_header.setContentsMargins(4, 0, 4, 0)
        schedule_header.setSpacing(0)
        schedule_frame.setFixedHeight(18)

        self._add_header_cell(schedule_header, "Event ID", 95)
        self._add_header_cell(schedule_header, "Time", 38)
        self._add_header_cell(schedule_header, "Load (kW)", 46)
        self._add_header_cell(schedule_header, "Tariff", 40)
        self._add_header_cell(schedule_header, "Decision", 58)
        self._add_header_cell(schedule_header, "Dispatch", 48)
        self._add_header_cell(schedule_header, "Exp / Act (MWh)", 78)
        self._add_header_cell(schedule_header, "Cycles", 42)
        self._add_header_cell(schedule_header, "Target SoC", 48)
        self._add_header_cell(schedule_header, "Status", 54)

        root.addWidget(schedule_frame)

        # =========================================================
        # SCHEDULE TABLE
        # =========================================================

        self.schedule_scroll = QScrollArea()
        self.schedule_scroll.setWidgetResizable(True)
        self.schedule_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.schedule_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.schedule_scroll.setFrameShape(QFrame.NoFrame)

        self.schedule_scroll.setStyleSheet("""
            QScrollArea {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-top: none;
            }
        """)
        self.schedule_scroll.setFixedHeight(78)

        self.schedule_content = QWidget()
        self.schedule_layout = QVBoxLayout(self.schedule_content)
        self.schedule_layout.setContentsMargins(0, 0, 0, 0)
        self.schedule_layout.setSpacing(0)

        self.schedule_scroll.setWidget(self.schedule_content)
        root.addWidget(self.schedule_scroll)

        # =========================================================
        # CURRENT INTERVAL DETAILS
        # =========================================================

        self.details_frame = QFrame()
        self.details_frame.setStyleSheet("""
            QFrame {
                background: #F8FAFC;
                border: 1px solid #DCE3EC;
                border-radius: 3px;
            }
        """)
        self.details_frame.setFixedHeight(82)

        details_layout = QVBoxLayout(self.details_frame)
        details_layout.setContentsMargins(5, 2, 5, 2)
        details_layout.setSpacing(0)

        self.interval_title = QLabel(
            "Current Interval Details (15:45 - 16:00)"
        )
        self.interval_title.setStyleSheet("""
            QLabel {
                color: #243B53;
                font-size: 7px;
                font-weight: 800;
            }
        """)
        self.detail_labels = {}
        self.detail_name_labels = []

        details_header = QHBoxLayout()
        details_header.setContentsMargins(0, 0, 0, 0)
        details_header.setSpacing(4)
        details_header.addWidget(self.interval_title, 1)

        for key, label, value in (
            ("is_pass", "Pass", "—"),
            ("fault", "Fault", "None"),
        ):
            name = QLabel(label)
            name.setStyleSheet("color: #667788; font-size: 6px;")
            self.detail_name_labels.append(name)
            value_label = QLabel(value)
            value_label.setStyleSheet(
                "color: #263746; font-size: 6px; font-weight: 700;"
            )
            details_header.addWidget(name)
            details_header.addWidget(value_label)
            self.detail_labels[key] = value_label

        details_layout.addLayout(details_header)

        details_grid = QGridLayout()
        details_grid.setContentsMargins(0, 0, 0, 0)
        details_grid.setHorizontalSpacing(6)
        details_grid.setVerticalSpacing(1)

        fields = [
            ("load", "Load", "2200.0 kW"),
            ("decision", "Decision", "DISCHARGE"),
            ("discharge", "Discharge", "2200.0 kW"),
            ("tariff_per_kw", "Tariff", "2.00 /kW"),
            ("pv", "PV", "0.0 kW"),
            ("charge", "Charge", "0.0 kW"),
            ("soc", "SOC", "47.88 %"),
            ("grid_import_limit", "Grid Import Limit", "4000.0 kW"),
            ("grid_charge", "Grid Charge", "0.0 kW"),
            ("available_energy", "Available Energy", "12.45 MWh"),
        ]

        for index, (key, label, value) in enumerate(fields):
            row = index % 3
            col = (index // 3) * 2
            font_size = "8px" if key in (
                "load",
                "decision",
                "discharge",
                "tariff_per_kw",
            ) else "6.5px"

            name = QLabel(label)
            self.detail_name_labels.append(name)
            name.setStyleSheet(f"""
                QLabel {{
                    color: #667788;
                    font-size: {font_size};
                }}
            """)

            value_label = QLabel(value)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setStyleSheet(f"""
                QLabel {{
                    color: #263746;
                    font-size: {font_size};
                    font-weight: 700;
                }}
            """)

            details_grid.addWidget(name, row, col)
            details_grid.addWidget(value_label, row, col + 1)

            self.detail_labels[key] = value_label

        details_layout.addLayout(details_grid)

        self.description_title = QLabel("Description")
        self.description_title.setStyleSheet(
            "color: #667788; font-size: 6px;"
        )
        details_layout.addWidget(self.description_title)

        description_value = QLabel(
            "BESS event executed successfully."
        )
        description_value.setWordWrap(True)
        description_value.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        description_value.setStyleSheet(
            "color: #263746; font-size: 6px; font-weight: 700;"
        )
        details_layout.addWidget(description_value, 1)
        self.detail_labels["description"] = description_value

        self.event_id_value = QLabel("Event ID: —")
        self.event_id_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.event_id_value.setContentsMargins(4, 0, 0, 0)
        self.event_id_value.setStyleSheet(
            "color: #263746; font-size: 6px; font-weight: 700;"
        )
        details_layout.addWidget(self.event_id_value)

        root.addWidget(self.details_frame)
        root.addStretch(1)

        # Initial display
        self.update_schedule([
            {
                "time": "15:45 - 16:00",
                "load": 2200,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 2200,
            },
            {
                "time": "16:00 - 16:15",
                "load": 1800,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 1800,
            },
            {
                "time": "16:15 - 16:30",
                "load": 1500,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 1500,
            },
            {
                "time": "16:30 - 16:45",
                "load": 1200,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 1200,
            },
            {
                "time": "16:45 - 17:00",
                "load": 800,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 800,
            },
            {
                "time": "17:00 - 17:15",
                "load": 400,
                "tariff_per_kw": 2.0,
                "decision": "DISCHARGE",
                "dispatch": 400,
            },
        ])

        self.json_timer = QTimer(self)
        self.json_timer.timeout.connect(self._on_timer_tick)
        self.json_timer.start(1000)

    def _on_timer_tick(self):
        self.check_json_update()
        if self.running_event_id:
            self.elapsed_seconds += 1
            # An event interval runs and ends in 15 minutes (or len(window_load) elements)
            total_elements = len(self.current_window_load) if self.current_window_load else 15
            total_window_seconds = total_elements * 60

            cur_sec = self.elapsed_seconds % max(1, total_window_seconds)
            current_step = min(total_elements, (cur_sec // 60) + 1)
            remaining_mins = max(0, total_elements - current_step)
            el_m = cur_sec // 60
            el_s = cur_sec % 60
            tot_m = total_elements

            elapsed_str = f"{el_m:02d}:{el_s:02d}"
            tot_str = f"{tot_m:02d}:00"

            if hasattr(self, "running_elapsed_badge"):
                self.running_elapsed_badge.setText(
                    f"ELAPSED: {elapsed_str} / {tot_str}  |  REMAINING: {remaining_mins}m (Step {current_step}/{tot_m})"
                )
                self.running_elapsed_badge.show()
            if hasattr(self, "elapsed_time_top"):
                self.elapsed_time_top.setText(f"Elapsed: {elapsed_str} / {tot_m}m")
                self.elapsed_time_top.show()

            if self.current_window_load and (current_step - 1) < len(self.current_window_load):
                val = self.current_window_load[current_step - 1]
                if hasattr(self, "current_load_value"):
                    self.current_load_value.setText(f"{float(val):.0f} kW")
        else:
            if hasattr(self, "running_elapsed_badge"):
                self.running_elapsed_badge.hide()
            if hasattr(self, "elapsed_time_top"):
                self.elapsed_time_top.hide()

    # =============================================================
    # KPI CARD
    # =============================================================

    def _set_fullscreen_fonts(self, fullscreen):
        if fullscreen:
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #1671D9;
                    font-size: 24px;
                    font-weight: 800;
                }
            """)
            self.date_label.setStyleSheet("""
                QLabel {
                    color: #526170;
                    font-size: 11px;
                    font-weight: 600;
                }
            """)
            if hasattr(self, "elapsed_time_top"):
                self.elapsed_time_top.setStyleSheet("color: #D97706; font-size: 12px; font-weight: 700;")
            if hasattr(self, "running_elapsed_badge"):
                self.running_elapsed_badge.setStyleSheet("color: #B45309; font-size: 11px; font-weight: 800; border: none;")
            self.current_load_value.setStyleSheet("""
                QLabel {
                    color: #263746;
                    font-size: 18px;
                    font-weight: 800;
                }
            """)
            self.dispatch_value.setStyleSheet("""
                QLabel {
                    color: #263746;
                    font-size: 18px;
                    font-weight: 800;
                }
            """)
            self.details_frame.setFixedHeight(150)
            self.interval_title.setStyleSheet("""
                QLabel {
                    color: #243B53;
                    font-size: 14px;
                    font-weight: 800;
                }
            """)
            self.description_title.setStyleSheet(
                "color: #667788; font-size: 11px;"
            )
            self.detail_labels["description"].setStyleSheet(
                "color: #263746; font-size: 11px; font-weight: 700;"
            )
            self.event_id_value.setStyleSheet(
                "color: #263746; font-size: 10px; font-weight: 700;"
            )
            for label in self.detail_name_labels:
                label.setStyleSheet(
                    "color: #667788; font-size: 10px;"
                )
            for key, label in self.detail_labels.items():
                if key != "description":
                    label.setStyleSheet(
                        "color: #263746; font-size: 10px; "
                        "font-weight: 700;"
                    )
            self._update_running_event_badge()
            return

        self.time_label.setStyleSheet("""
            QLabel {
                color: #1671D9;
                font-size: 14px;
                font-weight: 800;
            }
        """)
        self.date_label.setStyleSheet("""
            QLabel {
                color: #526170;
                font-size: 6px;
                font-weight: 600;
            }
        """)
        self.current_load_value.setStyleSheet("""
            QLabel {
                color: #263746;
                font-size: 10px;
                font-weight: 800;
            }
        """)
        self.dispatch_value.setStyleSheet("""
            QLabel {
                color: #263746;
                font-size: 10px;
                font-weight: 800;
            }
        """)
        self.details_frame.setFixedHeight(82)
        self.interval_title.setStyleSheet("""
            QLabel {
                color: #243B53;
                font-size: 7px;
                font-weight: 800;
            }
        """)
        self.description_title.setStyleSheet(
            "color: #667788; font-size: 6px;"
        )
        self.detail_labels["description"].setStyleSheet(
            "color: #263746; font-size: 6px; font-weight: 700;"
        )
        self.event_id_value.setStyleSheet(
            "color: #263746; font-size: 6px; font-weight: 700;"
        )
        for label in self.detail_name_labels:
            label.setStyleSheet("color: #667788; font-size: 6px;")
        for key, label in self.detail_labels.items():
            if key in ("description", "is_pass", "fault"):
                continue
            font_size = "8px" if key in (
                "load",
                "decision",
                "discharge",
                "tariff_per_kw",
            ) else "6px"
            label.setStyleSheet(
                "color: #263746; "
                f"font-size: {font_size}; font-weight: 700;"
            )
        self._update_running_event_badge()

    def _toggle_fullscreen(self):
        if self.fullscreen_dialog is not None:
            self.fullscreen_dialog.close()
            return

        parent = self.parentWidget()
        if parent is None:
            return

        self._fullscreen_parent = parent
        self._fullscreen_geometry = self.geometry()

        dialog = QDialog(parent.window())
        dialog.setWindowTitle("BESS Dispatch Schedule")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self)
        dialog.finished.connect(
            lambda _result, active_dialog=dialog:
                self._restore_from_fullscreen(active_dialog)
        )

        self.fullscreen_dialog = dialog
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.schedule_scroll.setFixedHeight(250)
        self._set_fullscreen_fonts(True)
        self.fullscreen_button.setText("✕")
        self.fullscreen_button.setToolTip("Exit fullscreen")
        dialog.showFullScreen()

    def _restore_from_fullscreen(self, dialog):
        if dialog is not self.fullscreen_dialog:
            return

        parent = self._fullscreen_parent
        geometry = self._fullscreen_geometry
        self.fullscreen_dialog = None
        self._fullscreen_parent = None
        self._fullscreen_geometry = None

        if parent is not None and geometry is not None:
            self.setParent(parent)
            self.setFixedSize(geometry.size())
            self.setGeometry(geometry)
            self.schedule_scroll.setFixedHeight(78)
            self._set_fullscreen_fonts(False)
            self.fullscreen_button.setText("⛶")
            self.fullscreen_button.setToolTip("Fullscreen")
            self.show()

        dialog.deleteLater()

    def _create_kpi(self, parent_layout, title, value, decision=False):
        frame = QFrame()
        frame.setFixedHeight(34)

        frame.setStyleSheet("""
            QFrame {
                background: #FBFCFD;
                border: 1px solid #DCE3EC;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #667788;
                font-size: 6px;
            }
        """)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)

        if decision:
            value_label.setStyleSheet("""
                QLabel {
                    background: #BFF0C7;
                    color: #25863B;
                    border-radius: 3px;
                    font-size: 8px;
                    font-weight: 800;
                    padding: 1px 3px;
                }
            """)
        else:
            value_label.setStyleSheet("""
                QLabel {
                    color: #263746;
                    font-size: 10px;
                    font-weight: 800;
                }
            """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        parent_layout.addWidget(frame, 1)
        return value_label

    # =============================================================
    # TABLE HEADER
    # =============================================================

    def _add_header_cell(self, layout, text, width):
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #667788;
                font-size: 6px;
                font-weight: 700;
                border: none;
            }
        """)
        layout.addWidget(label)

    # =============================================================
    # UPDATE SCHEDULE
    # =============================================================

    def update_schedule(
        self,
        schedule_data,
        current_details=None,
        current_time=None,
        current_date=None,
    ):
        if schedule_data is None:
            schedule_data = []

        self.schedule_data = schedule_data

        if current_time is not None:
            self.time_label.setText(str(current_time))

        if current_date is not None:
            self.date_label.setText(str(current_date))

        # Check for running event in schedule_data
        running_idx = None
        for i, item in enumerate(schedule_data):
            if str(item.get("status", "")).upper() == "RUNNING":
                running_idx = i
                if not self.running_event_id:
                    self.running_event_id = item.get("event_id")
                break

        self.running_row_index = running_idx
        self._update_running_event_badge()

        if len(self.schedule_rows) != len(schedule_data):
            while self.schedule_layout.count():
                item = self.schedule_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            self.schedule_rows = []
            self.schedule_row_labels = []
            self.active_row_index = None
            for index, item in enumerate(schedule_data):
                is_active = (index == running_idx) if running_idx is not None else (index == 0)
                row = self._create_schedule_row(item, is_active, index)
                self.schedule_rows.append(row)
                self.schedule_layout.addWidget(row)

            self.schedule_layout.addStretch()
        else:
            for index, item in enumerate(schedule_data):
                self._update_schedule_row(index, item)

        # Update KPI from running row (or first row)
        active_target_item = None
        if running_idx is not None and running_idx < len(schedule_data):
            active_target_item = schedule_data[running_idx]
            self.active_row_index = running_idx
        elif schedule_data:
            active_target_item = schedule_data[0]
            self.active_row_index = 0

        if active_target_item:
            self.current_window_load = active_target_item.get("window_load", [])
            load = self._number(active_target_item.get("load", 0))
            dispatch = self._number(active_target_item.get("dispatch", 0))
            decision = str(active_target_item.get("decision", "STANDBY")).upper()

            self.current_load_value.setText(f"{load:.0f} kW")
            self.dispatch_value.setText(f"{dispatch * 0.25:.0f} kWh")
            self.soc_value.setText(f"{self._number(active_target_item.get('soc', 0)):.2f} %")
            self.decision_value.setText(decision)

            self.interval_title.setText(
                f"Current Interval Details ({active_target_item.get('time', '')})"
            )
            self._update_header_timestamp(active_target_item)

        if current_details is not None:
            self.update_details(current_details)
        elif active_target_item is not None:
            self.update_details(active_target_item)

        if running_idx is not None and self.manual_active_index is None:
            QTimer.singleShot(100, lambda idx=running_idx: self._scroll_to_row(idx))
        elif (
            self.current_twin_load is not None
            or self.manual_active_index is not None
        ):
            self._update_active_row(force=True)

    def update_twin_load(self, load_kw):
        self.current_twin_load = float(load_kw)

        # Sync step and remaining minutes if twin load matches window_load elements
        if self.current_window_load:
            best_step_idx = None
            min_step_diff = float("inf")
            for idx, w_val in enumerate(self.current_window_load):
                diff = abs(float(w_val) - self.current_twin_load)
                if diff < min_step_diff:
                    min_step_diff = diff
                    best_step_idx = idx

            # If closely matching current window_load elements (within 35 kW)
            if best_step_idx is not None and min_step_diff <= 35.0:
                tot_elem = len(self.current_window_load)
                current_step = best_step_idx + 1
                remaining_mins = max(0, tot_elem - current_step)
                sec_in_min = self.elapsed_seconds % 60
                self.elapsed_seconds = best_step_idx * 60 + sec_in_min
                el_m = self.elapsed_seconds // 60
                el_s = self.elapsed_seconds % 60
                elapsed_str = f"{el_m:02d}:{el_s:02d}"
                tot_str = f"{tot_elem:02d}:00"
                if hasattr(self, "running_elapsed_badge"):
                    self.running_elapsed_badge.setText(
                        f"ELAPSED: {elapsed_str} / {tot_str}  |  REMAINING: {remaining_mins}m (Step {current_step}/{tot_elem})"
                    )
                if hasattr(self, "elapsed_time_top"):
                    self.elapsed_time_top.setText(f"Elapsed: {elapsed_str} / {tot_elem}m")

        self._update_active_row()

    def _update_active_row(self, force=False):
        if not self.schedule_data:
            return

        if self.manual_active_index is not None:
            if self.manual_active_index < len(self.schedule_data):
                self._refresh_schedule_active_row(
                    self.manual_active_index,
                    force=force,
                )
                return
            self.manual_active_index = None

        if self.current_twin_load is None:
            return

        best_index = None
        best_difference = float("inf")

        for index, item in enumerate(self.schedule_data):
            schedule_load = self._number(item.get("load", 0))
            difference = abs(schedule_load - self.current_twin_load)

            if difference < best_difference:
                best_difference = difference
                best_index = index

        if best_index is not None:
            self._refresh_schedule_active_row(best_index, force=force)

    def _select_schedule_row(self, index):
        if not 0 <= index < len(self.schedule_data):
            return

        self.manual_active_index = index
        self._refresh_schedule_active_row(index, force=True)

    def _update_header_timestamp(self, item):
        timestamp = item.get("time_stamp")
        if not timestamp:
            return

        try:
            interval_start = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            return

        self.time_label.setText(interval_start.strftime("%H:%M"))
        self.date_label.setText(interval_start.strftime("%d %b %Y"))

    def _refresh_schedule_active_row(self, active_index, force=False):
        if not 0 <= active_index < len(self.schedule_rows):
            return

        if self.active_row_index != active_index:
            if self.active_row_index is not None:
                self._set_schedule_row_active(
                    self.active_row_index,
                    False,
                )
            self.active_row_index = active_index
            self._set_schedule_row_active(active_index, True)

        if 0 <= active_index < len(self.schedule_data):
            active_item = self.schedule_data[active_index]
            load = self._number(active_item.get("load", 0))
            dispatch = self._number(active_item.get("dispatch", 0))
            decision = str(
                active_item.get("decision", "STANDBY")
            ).upper()

            self.current_load_value.setText(f"{load:.0f} kW")
            self.dispatch_value.setText(f"{dispatch * 0.25:.0f} kWh")
            self.soc_value.setText(
                f"{self._number(active_item.get('soc', 0)):.2f} %"
            )
            self.decision_value.setText(decision)
            self.interval_title.setText(
                f"Current Interval Details "
                f"({active_item.get('time', '')})"
            )
            self._update_header_timestamp(active_item)
            self.update_details(active_item)

    def _get_row_style(self, item, active=False):
        status = str(item.get("status", "UPCOMING")).upper()
        if status == "RUNNING":
            bg = "#FEF08A" if active else "#FEF9C3"
            return f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid #F59E0B;
                    border-left: 4px solid #D97706;
                    {"border: 1.5px solid #2563EB; border-left: 4px solid #D97706;" if active else ""}
                }}
            """
        elif status == "PASS":
            bg = "#D1FAE5" if active else "#ECFDF5"
            return f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid #A7F3D0;
                    border-left: 4px solid #16A34A;
                    {"border: 1.5px solid #2563EB; border-left: 4px solid #16A34A;" if active else ""}
                }}
            """
        elif status == "FAIL":
            bg = "#FEE2E2" if active else "#FEF2F2"
            return f"""
                QFrame {{
                    background: {bg};
                    border: 1px solid #FECACA;
                    border-left: 4px solid #DC2626;
                    {"border: 1.5px solid #2563EB; border-left: 4px solid #DC2626;" if active else ""}
                }}
            """
        else:
            bg = "#F1F5F9" if active else "#FFFFFF"
            return f"""
                QFrame {{
                    background: {bg};
                    border: none;
                    border-bottom: 1px solid #E2E8F0;
                    border-left: 4px solid transparent;
                    {"border: 1.5px solid #2563EB; border-left: 4px solid #2563EB;" if active else ""}
                }}
            """

    @staticmethod
    def _get_status_badge_style(status):
        status = str(status).upper()
        if status == "RUNNING":
            return """
                background: #F59E0B;
                color: #FFFFFF;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 800;
                padding: 1px 2px;
            """
        elif status == "PASS":
            return """
                background: #16A34A;
                color: #FFFFFF;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 800;
                padding: 1px 2px;
            """
        elif status == "FAIL":
            return """
                background: #DC2626;
                color: #FFFFFF;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 800;
                padding: 1px 2px;
            """
        else:
            return """
                background: #F1F5F9;
                color: #64748B;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 600;
                padding: 1px 2px;
            """

    def _update_running_event_badge(self):
        if hasattr(self, "running_event_label") and hasattr(self, "running_dot"):
            is_fs = (self.fullscreen_dialog is not None)
            font_size = "11px" if is_fs else "8px"
            dot_size = "11px" if is_fs else "8px"
            radius = "6px" if is_fs else "4px"

            if self.running_event_id:
                self.running_event_label.setText(f"RUNNING EVENT ID: {self.running_event_id}")
                if hasattr(self, "running_status_hint"):
                    self.running_status_hint.setText("ACTIVE DISPATCH")
                    self.running_status_hint.setStyleSheet(f"color: #B45309; font-size: {font_size}; font-weight: 800; border: none;")
                self.running_event_badge.setStyleSheet(f"""
                    QFrame#RunningEventBadge {{
                        background: #FEF3C7;
                        border: 1.5px solid #F59E0B;
                        border-radius: {radius};
                    }}
                """)
                self.running_dot.setStyleSheet(f"color: #D97706; font-size: {dot_size};")
                self.running_event_label.setStyleSheet(f"color: #92400E; font-size: {font_size}; font-weight: 800; border: none;")
            else:
                self.running_event_label.setText("NO ACTIVE EVENT RUNNING")
                if hasattr(self, "running_status_hint"):
                    self.running_status_hint.setText("STANDBY")
                    self.running_status_hint.setStyleSheet(f"color: #64748B; font-size: {font_size}; font-weight: 700; border: none;")
                self.running_event_badge.setStyleSheet(f"""
                    QFrame#RunningEventBadge {{
                        background: #F8FAFC;
                        border: 1px solid #E2E8F0;
                        border-radius: {radius};
                    }}
                """)
                self.running_dot.setStyleSheet(f"color: #94A3B8; font-size: {dot_size};")
                self.running_event_label.setStyleSheet(f"color: #64748B; font-size: {font_size}; font-weight: 700; border: none;")

    def _scroll_to_row(self, index):
        if 0 <= index < len(self.schedule_rows):
            row_widget = self.schedule_rows[index]
            self.schedule_scroll.ensureWidgetVisible(row_widget, 0, 10)

    def _set_schedule_row_active(self, index, active):
        if not 0 <= index < len(self.schedule_rows):
            return
        item = self.schedule_data[index] if index < len(self.schedule_data) else {}
        self.schedule_rows[index].setStyleSheet(self._get_row_style(item, active=active))

    def _update_schedule_row(self, index, item):
        labels = self.schedule_row_labels[index]
        actual_energy = item.get("actual_energy")
        actual_energy_text = (
            f"{self._number(actual_energy):.2f}"
            if actual_energy is not None
            else "—"
        )
        decision_text = str(
            item.get("decision", "STANDBY")
        ).upper()
        status_text = str(item.get("status", "SCHEDULED")).upper()

        labels["event_id"].setText(str(item.get("event_id", "—")))
        if status_text == "RUNNING":
            labels["event_id"].setStyleSheet("color: #92400E; font-size: 8px; font-weight: 800; border: none;")
        elif status_text == "PASS":
            labels["event_id"].setStyleSheet("color: #15803D; font-size: 8px; font-weight: 700; border: none;")
        elif status_text == "FAIL":
            labels["event_id"].setStyleSheet("color: #B91C1C; font-size: 8px; font-weight: 700; border: none;")
        else:
            labels["event_id"].setStyleSheet("color: #35485A; font-size: 8px; border: none;")

        labels["time"].setText(str(item.get("time", "")))
        labels["load"].setText(f"{self._number(item.get('load', 0)):.0f}")
        if "tariff" in labels:
            t_val = item.get("tariff_per_kw", item.get("tariff", 0.0))
            labels["tariff"].setText(f"{self._number(t_val):.1f}")
        labels["decision"].setText(decision_text)
        labels["decision"].setStyleSheet(f"""
            QLabel {{
                background: {self._decision_color(decision_text)};
                color: #23823B;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 800;
                padding: 1px 2px;
            }}
        """)
        labels["dispatch"].setText(
            f"{self._number(item.get('dispatch', 0)) * 0.25:.0f}"
        )
        expected_energy = item.get("expected_energy", item.get("battery_energy_mwh", 0))
        exp_act_display = f"{self._number(expected_energy):.2f} / {actual_energy_text}"
        labels["available_energy"].setText(exp_act_display)
        labels["cycle_count"].setText(
            f"{self._number(item.get('cycle_count', 0)):.3f}"
        )
        labels["target_soc"].setText(
            f"{self._number(item.get('soc', 0)):.1f}%"
        )
        if "status" in labels:
            labels["status"].setText(status_text)
            labels["status"].setStyleSheet(f"QLabel {{ {self._get_status_badge_style(status_text)} }}")

        is_active = (index == self.active_row_index)
        self.schedule_rows[index].setStyleSheet(self._get_row_style(item, active=is_active))

    # =============================================================
    # CREATE SCHEDULE ROW
    # =============================================================

    def _create_schedule_row(self, item, active=False, index=0):
        row = _ClickableScheduleRow()
        row.setFixedHeight(17)
        row.setCursor(Qt.PointingHandCursor)
        row.clicked.connect(
            lambda row_index=index: self._select_schedule_row(row_index)
        )

        row.setStyleSheet(self._get_row_style(item, active=active))

        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 0, 2, 0)
        layout.setSpacing(0)

        status_text = str(item.get("status", "SCHEDULED")).upper()

        event_id = QLabel(str(item.get("event_id", "—")))
        event_id.setFixedWidth(95)
        event_id.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        event_id.setContentsMargins(2, 0, 0, 0)

        time = QLabel(str(item.get("time", "")))
        time.setFixedWidth(38)
        time.setAlignment(Qt.AlignCenter)

        load = QLabel(
            f"{self._number(item.get('load', 0)):.0f}"
        )
        load.setFixedWidth(46)
        load.setAlignment(Qt.AlignCenter)

        tariff_val = item.get("tariff_per_kw", item.get("tariff", 0.0))
        tariff = QLabel(f"{self._number(tariff_val):.1f}")
        tariff.setFixedWidth(40)
        tariff.setAlignment(Qt.AlignCenter)

        decision_text = str(
            item.get("decision", "STANDBY")
        ).upper()

        decision = QLabel(decision_text)
        decision.setFixedWidth(58)
        decision.setAlignment(Qt.AlignCenter)

        dispatch = QLabel(
            f"{self._number(item.get('dispatch', 0)) * 0.25:.0f}"
        )
        dispatch.setFixedWidth(48)
        dispatch.setAlignment(Qt.AlignCenter)

        actual_energy = item.get("actual_energy")
        actual_energy_text = (
            f"{self._number(actual_energy):.2f}"
            if actual_energy is not None
            else "—"
        )
        expected_energy = item.get("expected_energy", item.get("battery_energy_mwh", 0))
        exp_act_display = f"{self._number(expected_energy):.2f} / {actual_energy_text}"
        available_energy = QLabel(exp_act_display)
        available_energy.setFixedWidth(78)
        available_energy.setAlignment(Qt.AlignCenter)

        cycle_count = QLabel(
            f"{self._number(item.get('cycle_count', 0)):.3f}"
        )
        cycle_count.setFixedWidth(42)
        cycle_count.setAlignment(Qt.AlignCenter)

        target_soc = QLabel(
            f"{self._number(item.get('soc', 0)):.1f}%"
        )
        target_soc.setFixedWidth(48)
        target_soc.setAlignment(Qt.AlignCenter)

        status_label = QLabel(status_text)
        status_label.setFixedWidth(54)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet(f"QLabel {{ {self._get_status_badge_style(status_text)} }}")
        status_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        for label in (
            time,
            load,
            tariff,
            dispatch,
            available_energy,
            cycle_count,
            target_soc,
        ):
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
            label.setStyleSheet("""
                QLabel {
                    color: #35485A;
                    font-size: 7.5px;
                    border: none;
                }
            """)

        event_id.setAttribute(Qt.WA_TransparentForMouseEvents)
        if status_text == "RUNNING":
            event_id.setStyleSheet("color: #92400E; font-size: 8px; font-weight: 800; border: none;")
        elif status_text == "PASS":
            event_id.setStyleSheet("color: #15803D; font-size: 8px; font-weight: 700; border: none;")
        elif status_text == "FAIL":
            event_id.setStyleSheet("color: #B91C1C; font-size: 8px; font-weight: 700; border: none;")
        else:
            event_id.setStyleSheet("color: #35485A; font-size: 8px; border: none;")

        decision_color = self._decision_color(decision_text)
        decision.setStyleSheet(f"""
            QLabel {{
                background: {decision_color};
                color: #23823B;
                border-radius: 3px;
                font-size: 6px;
                font-weight: 800;
                padding: 1px 2px;
            }}
        """)
        decision.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout.addWidget(event_id)
        layout.addWidget(time)
        layout.addWidget(load)
        layout.addWidget(tariff)
        layout.addWidget(decision)
        layout.addWidget(dispatch)
        layout.addWidget(available_energy)
        layout.addWidget(cycle_count)
        layout.addWidget(target_soc)
        layout.addWidget(status_label)

        self.schedule_row_labels.append({
            "event_id": event_id,
            "time": time,
            "load": load,
            "tariff": tariff,
            "decision": decision,
            "dispatch": dispatch,
            "available_energy": available_energy,
            "cycle_count": cycle_count,
            "target_soc": target_soc,
            "status": status_label,
        })

        return row

    # =============================================================
    # DETAILS
    # =============================================================

    def update_details(self, details):
        self.current_details = details or {}

        mapping = {
            "is_pass": lambda v: (
                "TRUE" if v is True else "FALSE" if v is False else "—"
            ),
            "fault": lambda v: "None" if v is None else str(v),
            "description": lambda v: str(v or "—"),
            "load": lambda v: f"{self._number(v):.1f} kW",
            "pv": lambda v: f"{self._number(v):.1f} kW",
            "grid_import_limit": lambda v: f"{self._number(v):.1f} kW",
            "decision": lambda v: str(v).upper(),
            "charge": lambda v: f"{self._number(v):.1f} kW",
            "grid_charge": lambda v: f"{self._number(v):.1f} kW",
            "discharge": lambda v: f"{self._number(v):.1f} kW",
            "soc": lambda v: f"{self._number(v):.2f} %",
            "available_energy": lambda v: f"{self._number(v):.2f} MWh",
            "tariff_per_kw": lambda v: f"{self._number(v):.2f} /kW",
            "tariff": lambda v: f"{self._number(v):.2f} /kW",
        }

        for key, formatter in mapping.items():
            if key in details and key in self.detail_labels:
                self.detail_labels[key].setText(
                    formatter(details[key])
                )

        if "tariff_per_kw" in self.detail_labels and "tariff_per_kw" not in details and "tariff" in details:
            self.detail_labels["tariff_per_kw"].setText(f"{self._number(details['tariff']):.2f} /kW")

        description = str(details.get("description") or "—")
        event_id = str(details.get("event_id") or "—")
        self.detail_labels["description"].setText(description)
        self.event_id_value.setText(f"Event ID: {event_id}")

    # =============================================================
    # JSON LOADER
    # =============================================================

    def set_running_event(self, event_id, time_stamp=None):
        """Programmatically set or override the running event."""
        self.manual_running_event_id = event_id
        self.manual_running_timestamp = time_stamp
        self.running_event_id = event_id
        self._update_running_event_badge()
        if self.schedule_data:
            running_idx = None
            for idx, item in enumerate(self.schedule_data):
                cur_eid = item.get("event_id")
                cur_ts = item.get("time_stamp")
                if (event_id and cur_eid == event_id) or (time_stamp and cur_ts == time_stamp):
                    item["status"] = "RUNNING"
                    if running_idx is None:
                        running_idx = idx
                elif item.get("status") == "RUNNING":
                    item["status"] = "UPCOMING"
                self._update_schedule_row(idx, item)
            self._update_running_event_badge()
            if running_idx is not None:
                self.running_row_index = running_idx
                self._refresh_schedule_active_row(running_idx, force=True)
                QTimer.singleShot(100, lambda i=running_idx: self._scroll_to_row(i))

    def load_json(self, file_path):
        import json

        if not file_path or not os.path.exists(file_path):
            print(f"BessDispatchSchedule: file not found: {file_path}")
            return

        self.json_file_path = os.fspath(file_path)
        try:
            with open(
                self.json_file_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except Exception as e:
            print(f"Error loading dispatch schedule JSON: {e}")
            return

        self.result_data = data if isinstance(data, dict) else {}
        records = data.get("schedule", []) if isinstance(data, dict) else []
        if not isinstance(records, list):
            records = []

        outcomes_by_timestamp = {}
        outcomes_by_event_id = {}
        results = data.get("results", []) if isinstance(data, dict) else []
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                event = result.get("bess_event_decision", {})
                if isinstance(event, dict):
                    ts = event.get("time_stamp")
                    if ts:
                        outcomes_by_timestamp[ts] = result
                    eid = event.get("event_id")
                    if eid:
                        outcomes_by_event_id[eid] = result

        # Check explicit top-level running configuration in json
        explicit_running_id = data.get("running_event_id") or data.get("active_event_id")
        explicit_running_ts = data.get("running_timestamp") or data.get("running_time_stamp")

        detected_running_id = explicit_running_id or self.manual_running_event_id
        detected_running_ts = explicit_running_ts or self.manual_running_timestamp

        # Detect if any result in results array is currently running (in-progress)
        if not detected_running_id and not detected_running_ts:
            for result in results:
                if not isinstance(result, dict):
                    continue
                st = str(result.get("status", "")).lower()
                is_running_flag = result.get("is_running")
                sr = result.get("strategy_result", [])
                is_completed = False
                if isinstance(sr, list) and sr:
                    if sr[-1].get("status") == "completed":
                        is_completed = True

                if (st in ("running", "in_progress")) or (is_running_flag is True) or (not is_completed and result.get("is_pass") is None and len(sr) > 0):
                    ev_dec = result.get("bess_event_decision", {})
                    detected_running_id = ev_dec.get("event_id")
                    detected_running_ts = ev_dec.get("time_stamp")
        # Fallback if no explicit running event key exists in JSON:
        if not detected_running_id and not detected_running_ts:
            if results and len(results) < len(records):
                next_item = records[len(results)]
                detected_running_id = next_item.get("event_id")
                detected_running_ts = next_item.get("time_stamp")
            elif records:
                detected_running_id = records[0].get("event_id")
                detected_running_ts = records[0].get("time_stamp")

        self.running_event_id = detected_running_id
        running_row_index = None

        schedule = []
        for idx, item in enumerate(records):
            timestamp = item.get("time_stamp") or ""
            outcome = outcomes_by_timestamp.get(timestamp, {})
            try:
                start_dt = datetime.fromisoformat(timestamp)
                time_text = start_dt.strftime("%H:%M")
            except (TypeError, ValueError):
                time_text = timestamp.split(" ")[-1][:5] if timestamp else ""

            decision = str(item.get("decision", "STANDBY"))
            charge = self._number(item.get("charge_kw", 0))
            grid_charge = self._number(item.get("grid_charge_kw", 0))
            discharge = self._number(item.get("discharge_kw", 0))
            dispatch = max(charge, grid_charge) if decision.lower() in ("grid_charge", "pv_charge") else discharge
            event_decision = outcome.get("bess_event_decision", {})
            if not isinstance(event_decision, dict):
                event_decision = {}

            strategy_result = outcome.get("strategy_result", [])
            actual_energy = None
            if isinstance(strategy_result, list):
                for strategy_step in reversed(strategy_result):
                    if (
                        isinstance(strategy_step, dict)
                        and "battery_energy_mwh" in strategy_step
                    ):
                        actual_energy = strategy_step["battery_energy_mwh"]
                        break

            event_id = item.get(
                "event_id",
                event_decision.get(
                    "event_id",
                    outcome.get("event_id", outcome.get("event_number", "—")),
                ),
            )

            # Determine row status: RUNNING, PASS, FAIL, UPCOMING
            is_running = False
            if detected_running_ts and timestamp == detected_running_ts:
                is_running = True
            elif outcome and (str(outcome.get("status", "")).lower() in ("running", "in_progress") or outcome.get("is_running") is True):
                is_running = True
            elif outcome and outcome.get("is_pass") is None and outcome.get("strategy_result"):
                sr_list = outcome.get("strategy_result", [])
                if sr_list and isinstance(sr_list, list) and sr_list[-1].get("status") != "completed":
                    is_running = True
            elif detected_running_id and event_id == detected_running_id and running_row_index is None and (not outcome or outcome.get("is_pass") is None):
                is_running = True

            if is_running:
                status = "RUNNING"
                if running_row_index is None:
                    running_row_index = idx
                if not self.running_event_id:
                    self.running_event_id = event_id
            elif outcome:
                # Finished event
                if outcome.get("is_pass") is True:
                    status = "PASS"
                elif outcome.get("is_pass") is False:
                    status = "FAIL"
                elif str(outcome.get("status", "")).lower() == "completed":
                    status = "PASS" if not outcome.get("fault") else "FAIL"
                else:
                    status = "UPCOMING"
            else:
                status = "UPCOMING"

            schedule.append({
                "event_id": event_id,
                "time": time_text,
                "time_stamp": timestamp,
                "load": item.get("load_kw", 0),
                "tariff_per_kw": self._number(item.get("tariff_per_kw", 0.0)),
                "pv": item.get("pv_kw", 0),
                "grid_import_limit": item.get("grid_import_limit_kw", 0),
                "decision": decision,
                "charge": charge,
                "grid_charge": item.get("grid_charge_kw", 0),
                "discharge": discharge,
                "dispatch": dispatch,
                "soc": item.get(
                    "soc_percent",
                    event_decision.get("soc_percent", 0),
                ),
                "available_energy": item.get("battery_energy_mwh", 0),
                "expected_energy": event_decision.get(
                    "battery_energy_mwh",
                    item.get("battery_energy_mwh", 0),
                ),
                "actual_energy": (
                    actual_energy
                    if actual_energy is not None
                    else None
                ),
                "window_load": item.get("window_load", []),
                "cycle_count": item.get(
                    "throughput_cycles",
                    event_decision.get("throughput_cycles", 0),
                ),
                "is_pass": outcome.get("is_pass"),
                "fault": outcome.get("fault"),
                "status": status,
                "description": item.get("description")
                or outcome.get("description")
                or "BESS event executed successfully.",
            })

        self.running_row_index = running_row_index
        self._update_running_event_badge()

        initial_detail = schedule[running_row_index] if (running_row_index is not None and running_row_index < len(schedule)) else (schedule[0] if schedule else None)
        self.update_schedule(schedule, initial_detail)
        self.json_last_modified = os.path.getmtime(self.json_file_path)

    def check_json_update(self):
        if not self.json_file_path:
            return

        try:
            modified = os.path.getmtime(self.json_file_path)
            if modified != self.json_last_modified:
                self.load_json(self.json_file_path)
        except Exception as error:
            print("DISPATCH JSON UPDATE ERROR:", error)

    # =============================================================
    # HELPERS
    # =============================================================

    @staticmethod
    def _number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _decision_color(decision):
        decision = decision.upper()

        if decision == "DISCHARGE":
            return "#BFF0C7"

        if decision == "CHARGE":
            return "#BFE3FF"

        if decision in ("IDLE", "STANDBY"):
            return "#E8EDF2"

        return "#DFF0FF"
