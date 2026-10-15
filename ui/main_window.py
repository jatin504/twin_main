import os
from datetime import datetime, timedelta

import yaml

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QTabWidget,
    QSizePolicy,
    QStackedWidget,
    QGraphicsOpacityEffect,
)

from state.tags import Tags
from ui.Widget.header import HeaderWidget
from ui.Widget.navbar import NavBar
from ui.Widget.ribbon import Ribbon
from ui.Widget.grid_availability_control import GridAvailabilityControl
from ui.Widget.power_flow import PowerFlowWidget
from ui.Widget.voltage_profile_widget import VoltageProfileWidget
from ui.Widget.branch_summary import BranchSummaryWidget
from ui.Widget.bess_summary import BessSummaryWidget
from ui.Widget.bess_dispatch_schedule import BessDispatchScheduleWidget
from ui.Widget.time_series_widget import TimeSeriesWidget
from ui.Widget.bank_fault_cards import (
    BankFaultCards,
    BankFaultCard,
)
from ui.Widget.plant_control_cards import PlantControlCards

from dotenv import load_dotenv

load_dotenv()


class EventToast(QFrame):
    """
    Floating, non-blocking toast notification banner that pops up smoothly
    at the top-right of the dashboard whenever a new BESS dispatch event arrives.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EventToast")
        self.setFixedWidth(420)
        self.setFixedHeight(95)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(1.0)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(350)
        self._fade.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade.finished.connect(self._on_fade_finished)
        self._fading_out = False

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame#EventToast {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:1 #1E293B);
                border: 1px solid #334155;
                border-left: 5px solid #10B981;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(4)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        icon_lbl = QLabel("⚡")
        icon_lbl.setStyleSheet("color: #F59E0B; font-size: 13px; font-weight: bold;")
        header_row.addWidget(icon_lbl)

        title_lbl = QLabel("NEW DISPATCH EVENT DETECTED")
        title_lbl.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        header_row.addWidget(title_lbl)

        header_row.addStretch()

        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet("color: #94A3B8; font-size: 9.5px; font-weight: 600;")
        header_row.addWidget(self.time_lbl)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(16, 16)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self._fade_out)
        header_row.addWidget(close_btn)
        layout.addLayout(header_row)

        # Body Row
        body_row = QHBoxLayout()
        body_row.setSpacing(8)

        self.eid_lbl = QLabel("EVENT")
        self.eid_lbl.setStyleSheet("color: #F8FAFC; font-size: 12px; font-weight: 700; font-family: monospace;")
        body_row.addWidget(self.eid_lbl)

        self.dec_badge = QLabel("ACTIVE")
        body_row.addWidget(self.dec_badge)
        body_row.addStretch()
        layout.addLayout(body_row)

        # Details Row
        self.details_lbl = QLabel()
        self.details_lbl.setStyleSheet("color: #CBD5E1; font-size: 9.5px; font-weight: 500;")
        layout.addWidget(self.details_lbl)

    def show_event(self, payload: dict | None = None, duration_ms: int = 4000):
        """Display toast notification with event details."""
        payload = payload or {}
        event_id = str(payload.get("event_id") or "EVENT")
        decision = str(payload.get("decision") or "ACTIVE").upper()
        load = payload.get("load", 0.0)
        soc = payload.get("soc", 50.0)
        time_stamp = payload.get("time_stamp", "")

        time_part = ""
        if time_stamp:
            try:
                time_part = str(time_stamp).split(" ")[-1][:5]
            except Exception:
                time_part = str(time_stamp)
        self.time_lbl.setText(f"Start: {time_part}" if time_part else "")
        self.eid_lbl.setText(event_id)

        # Decision color theme & accent left border
        if "CHARGE" in decision:
            dec_color = "#10B981"
            dec_bg = "rgba(16, 185, 129, 0.2)"
            border_left = "#10B981"
        elif "DISCHARGE" in decision:
            dec_color = "#F59E0B"
            dec_bg = "rgba(245, 158, 11, 0.2)"
            border_left = "#F59E0B"
        else:
            dec_color = "#94A3B8"
            dec_bg = "rgba(148, 163, 184, 0.2)"
            border_left = "#64748B"

        self.setStyleSheet(f"""
            QFrame#EventToast {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F172A, stop:1 #1E293B);
                border: 1px solid #334155;
                border-left: 5px solid {border_left};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        self.dec_badge.setText(decision)
        self.dec_badge.setStyleSheet(f"""
            QLabel {{
                background: {dec_bg};
                color: {dec_color};
                font-size: 9px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 4px;
                border: 1px solid {dec_color};
            }}
        """)

        try:
            load_num = float(load)
            load_str = f"{load_num:.1f} kW"
        except Exception:
            load_str = f"{load} kW"

        try:
            soc_num = float(soc)
            soc_str = f"{soc_num:.1f}%"
        except Exception:
            soc_str = f"{soc}%"

        self.details_lbl.setText(f"Load Demand: {load_str}  |  Target SOC: {soc_str}  |  Window: 15m")

        self.adjustSize()
        self._place()
        self._fading_out = False
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self.show()
        self.raise_()
        self._hide_timer.start(max(3500, int(duration_ms)))

    def _place(self):
        parent_window = self.window() if self.window() else self.parentWidget()
        if parent_window and parent_window.isVisible():
            margin = 32
            win_width = max(1200, parent_window.width())
            target_x = max(20, win_width - self.width() - margin)
            target_pt = parent_window.mapToGlobal(QPoint(target_x, 75))
            self.move(target_pt)
        else:
            self.move(800, 75)

    def reposition(self):
        if self.isVisible():
            self._place()

    def _fade_out(self):
        if not self.isVisible() or self._fading_out:
            return
        self._fading_out = True
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _on_fade_finished(self):
        if self._fading_out:
            self.hide()
            self._opacity.setOpacity(1.0)
            self._fading_out = False

class MainWindow(QMainWindow):

    def __init__(
        self,
        network_manager=None,
        custom_mode=False,
        backend_factory=None,
    ):
        super().__init__()

        self.network_manager = None
        self.simulator = None
        if isinstance(network_manager, tuple):
            self.network_manager = network_manager[0]
            self.simulator = network_manager[1]
        else:
            self.network_manager = network_manager
        self.custom_mode = custom_mode
        self.backend_factory = backend_factory

        self.setWindowTitle("ETALab Simulation - Project : KB20 US-MICROSOFT NOIDA")
        self.plant_yaml_path = os.getenv("PLANT_TOPOLOGY_PATH")
        self.setWindowTitle("Plant Digital Twin")
        self.plant_yaml_path = "plant/plant.yaml"
        self.load_custom_configuration()
        self.create_configuration_tabs()

    def create_configuration_tabs(self):
        self.setStyleSheet("""
        QMainWindow {
            background: #FFFFFF;
        }
        QTabWidget::pane {
            border: none;
            background: #FFFFFF;
        }
        QTabBar::tab {
            background: #F1F5F9;
            color: #172B4D;
            border: none;
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            background: #FFFFFF;
            color: #2563EB;
            border-bottom: 2px solid #2563EB;
        }
        """)
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.config_tabs = QTabWidget()
        self.config_tabs.setTabPosition(QTabWidget.North)

        self.custom_page = QWidget()
        self.build_custom_page(self.custom_page)

        self.builtin_page = QWidget()
        self.builtin_page.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        if self.network_manager is not None:
            self.build_builtin_page(self.builtin_page)

        self.config_tabs.addTab(
            self.custom_page,
            "Custom Configuration",
        )
        self.config_tabs.addTab(
            self.builtin_page,
            "Built-in Configuration",
        )

        # --------------------------------------------------
        # BUILT-IN SIMULATION CONTROL
        # --------------------------------------------------
        self.simulation_button = QPushButton(
            "▶ Start Simulation",
            self.config_tabs
        )
        self.simulation_button.setFixedSize(
            150,
            32
        )
        self.simulation_button.setStyleSheet("""
            QPushButton {
                background: #16A34A;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: #15803D;
                
            }
        """)
        self.simulation_button.clicked.connect(
            self.toggle_simulation
        )
        # --------------------------------------------------
        # RESTART SIMULATION
        # --------------------------------------------------
        self.restart_button = QPushButton(
            "↻ Restart Simulation",
            self.config_tabs
        )
        self.restart_button.setFixedSize(
            150,
            32
        )
        self.restart_button.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
            right_margin = 5
            }
        """)
        self.restart_button.clicked.connect(
            self.restart_simulation
        )
        self.restart_button.hide()
        # Put button directly on tab bar.
        self.simulation_button.show()
        QTimer.singleShot(
            0,
            self.position_simulation_button
        )

        if self.custom_mode:
            self.config_tabs.setCurrentIndex(0)
        else:
            self.config_tabs.setCurrentIndex(1)

        self.config_tabs.currentChanged.connect(
            self.configuration_tab_changed
        )
        main_layout.addWidget(self.config_tabs)
        self.setCentralWidget(central)

    def build_custom_page(self, page):
        page.setStyleSheet("""
        QWidget {
            background: #FFFFFF;
        }
        """)
        custom_layout = QVBoxLayout(page)
        custom_layout.setContentsMargins(15, 15, 15, 15)
        custom_layout.setSpacing(0)
        custom_layout.setAlignment(Qt.AlignTop)

        # BANK CONTROL
        bank_title = QLabel(
                "Bank Control & Fault Injection"
        )
        bank_title.setStyleSheet("""
                QLabel {
                    color: #172B4D;
                    font-size: 20px;
                    font-weight: 700;
                }
        """)
        custom_layout.addWidget(
                bank_title
        )
        self.bankFaultCards = BankFaultCards(
            initial_values=self.get_yaml_soc_soh()
        )
        custom_layout.addWidget(
            self.bankFaultCards,
            0,
            Qt.AlignTop
        )
        custom_layout.addSpacing(15)
        
        # PLANT CONTROL
        plant_title = QLabel(
                "Plant Control"
        )
        plant_title.setStyleSheet("""
                QLabel {
                    color: #172B4D;
                    font-size: 20px;
                    font-weight: 700;
                }
        """)
        custom_layout.addWidget(plant_title)
        custom_layout.addSpacing(2)
        self.plantControlCards = PlantControlCards(
            transformer_list=self.get_yaml_transformer_impedance()
        )
        custom_layout.addWidget(
            self.plantControlCards,
            0,
            Qt.AlignTop
        )
        self.gridAvailabilityControl = GridAvailabilityControl(self.plant_yaml_path)
        self.gridAvailabilityControl.availability_changed.connect(self._apply_grid_availability)
        custom_layout.addWidget(self.gridAvailabilityControl)
        # SUBMIT BUTTON - CUSTOM ONLY
        submit_layout = QHBoxLayout()
        submit_layout.setContentsMargins(0, 15, 0, 0)
        submit_layout.setSpacing(10)
        self.submit_button = QPushButton(
            "Submit"
        )
        self.submit_button.setFixedSize(
            120,
            38
        )
        self.submit_button.setStyleSheet("""
                QPushButton {
                    background: #2563EB;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: #1D4ED8;
                }
        """)
        self.submit_button.clicked.connect(
            self.submit_configuration
        )
        submit_layout.addWidget(
            self.submit_button
        )
        submit_layout.addStretch()
        custom_layout.addLayout(
            submit_layout
        )
    def _apply_grid_availability(self, available):
        """Apply the persisted utility switch to registered live grid states."""
        simulator = getattr(self, "simulator", None)
        database = getattr(simulator, "plant_database", None)
        if database is None:
            return
        for device_id in database.ids():
            device = database.device(device_id)
            if device.exists(Tags.Grid.AVAILABLE):
                device.set(Tags.Grid.AVAILABLE, available)

    def build_builtin_page(self, page):
        page.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        page.setMinimumSize(0, 0)

        page.setStyleSheet("""
        QMainWindow{
            background:#F5F7FA;
        }

        QWidget{
            background:#F5F7FA;
        }
        """)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = HeaderWidget()
        layout.addWidget(self.header)

        # Navigation
        self.navbar = NavBar()
        layout.addWidget(self.navbar)

        # Ribbon
        self.ribbon = Ribbon()
        self.ribbon.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        layout.addWidget(
            self.ribbon
        )

       
        # SCROLL AREA
             # CENTRAL STACK - SWITCHES BETWEEN ORIGINAL POWER FLOW & FULL-SCREEN TIME SERIES
        self.central_stack = QStackedWidget()
        layout.addWidget(self.central_stack, 1)

        # PAGE 0: ORIGINAL POWER FLOW DASHBOARD
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.verticalScrollBar().setSingleStep(40)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.scrollArea.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.scrollArea.setFrameShape(
            QScrollArea.NoFrame
        )
        self.scrollArea.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.central_stack.addWidget(self.scrollArea)

        # SCROLL CONTENT
        scrollContent = QWidget()
        scrollContent.setMinimumSize(1520, 1060)

        scrollLayout = QVBoxLayout(scrollContent)
        scrollLayout.setContentsMargins(0, 0, 0, 10)
        scrollLayout.setSpacing(10)
        scrollLayout.setAlignment(Qt.AlignTop)

        # ROW 1 - POWER FLOW DIAGRAM & BUS VOLTAGES (MATCHES REFERENCE DESIGN)
        powerFlowRow = QWidget()
        powerFlowRow.setFixedSize(1520, 510)

        self.powerFlow = PowerFlowWidget(
            network_manager=self.simulator
        )

        # POWER FLOW
        self.powerFlow.setParent(powerFlowRow)
        self.powerFlow.move(0, 0)

        # SHOW POWER FLOW
        self.powerFlow.show()

        scrollLayout.addWidget(powerFlowRow)

        # ROW 2 - 2-COLUMN 1-HR TREND & ADJACENT VOLTAGE PROFILE GRAPH
        trendRow = QWidget()
        trendRow.setFixedSize(1520, 270)

        # Left slot: 1-Hour Rolling Trends taking 2 columns of space (width: 1030)
        self.dashboardTimeSeries = TimeSeriesWidget(simulator=self.simulator, dashboard=True)
        self.dashboardTimeSeries.setParent(trendRow)
        self.dashboardTimeSeries.setGeometry(0, 0, 1030, 265)
        self.dashboardTimeSeries.show()

        # Right slot: Adjacent Voltage Profile graph (width: 480)
        self.adjacentVoltageProfile = VoltageProfileWidget(simulator=self.simulator, width=480, height=265)
        self.adjacentVoltageProfile.setParent(trendRow)
        self.adjacentVoltageProfile.setGeometry(1040, 0, 480, 265)
        self.adjacentVoltageProfile.show()

        scrollLayout.addWidget(trendRow)

        # ROW 3 - BRANCH SUMMARY, BESS DISPATCH SCHEDULE (MIDDLE), BESS SUMMARY (RIGHT)
        secondRow = QWidget()
        secondRow.setFixedSize(1520, 255)

        self.branchSummary = BranchSummaryWidget(plant_yaml_path=self.plant_yaml_path)
        self.branchSummary.setParent(secondRow)
        self.branchSummary.setGeometry(0, 0, 390, 250)
        self.branchSummary.show()

        # Middle slot: BESS Dispatch Schedule (expanded width: 630px)
        self.bessDispatchSchedule = BessDispatchScheduleWidget()
        self.bessDispatchSchedule.setParent(secondRow)
        self.bessDispatchSchedule.setGeometry(400, 0, 630, 250)

        # Notification Toast popup for new event triggers
        self.event_toast = EventToast(self)
        self.bessDispatchSchedule.event_started.connect(self.event_toast.show_event)

        result_json = os.getenv("BESS_DISPATCH_RESULT_PATH")
        if not result_json or not os.path.exists(result_json):
            fallback_local = os.path.join(os.path.dirname(__file__), "result.json")
            if os.path.exists(fallback_local):
                result_json = fallback_local
            elif os.path.exists("ui/result.json"):
                result_json = "ui/result.json"

        if result_json and os.path.exists(result_json):
            self.bessDispatchSchedule.load_json(result_json)
        self.bessDispatchSchedule.json_timer.timeout.connect(self._update_header_timing)
        self.bessDispatchSchedule.event_started.connect(lambda _event: self._update_header_timing())
        self._update_header_timing()
        # Keep all dispatch details inside the scrollable dashboard content.
        dispatch_height = max(250, self.bessDispatchSchedule.layout().minimumSize().height())
        self.bessDispatchSchedule.setFixedHeight(dispatch_height)
        secondRow.setFixedHeight(max(255, dispatch_height + 5))
        self.bessDispatchSchedule.show()

        # Right slot: BESS Summary (compact width: 480px)
        self.bessSummary = BessSummaryWidget()
        self.bessSummary.setParent(secondRow)
        self.bessSummary.setGeometry(1040, 0, 480, 250)
        self.bessSummary.show()

        scrollLayout.addWidget(secondRow)
        self.scrollArea.setWidget(scrollContent)

        # PAGE 1: DEDICATED 1-HOUR TIME SERIES CHART (FULL SCREEN VIEW)
        self.timeSeriesContainer = QWidget()
        ts_layout = QVBoxLayout(self.timeSeriesContainer)
        ts_layout.setContentsMargins(10, 8, 10, 8)
        ts_layout.setSpacing(0)

        self.timeSeriesWidget = TimeSeriesWidget(simulator=self.simulator)
        self.timeSeriesWidget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        ts_layout.addWidget(self.timeSeriesWidget)
        self.central_stack.addWidget(self.timeSeriesContainer)

        # TAB
        self.navbar.tabChanged.connect(
            self.changeTab
        )

        
        # RIBBON LIVE DATA TIMER
        self.ribbon_timer = QTimer(self)

        self.ribbon_timer.timeout.connect(
            self.update_ribbon
        )

        self.ribbon_timer.start(1000)

        # VOLTAGE PROFILE TIMER
        self.voltage_timer = QTimer(self)

        self.voltage_timer.timeout.connect(
            self.update_voltage_profile
        )

        self.voltage_timer.start(1000)

    def configuration_tab_changed(self, index):
        if index == 0:
            self.simulation_button.hide()
            self.restart_button.hide()
            return

        if index == 1:
            if self.network_manager is None:
                if self.backend_factory is not None:
                    print(
                        "Starting built-in backend..."
                    )
                    backend = self.backend_factory()
                    self.network_manager = backend[0]
                    self.simulator = backend[1]
                    self.build_builtin_page(
                        self.builtin_page
                    )
            QTimer.singleShot(
                0,
                self.position_simulation_button
            )

    def position_simulation_button(self):
        if not hasattr(self, "simulation_button"):
            return

        container = self.config_tabs
        tab_bar = self.config_tabs.tabBar()
        button_width = self.simulation_button.width()
        button_height = self.simulation_button.height()
        spacing = 8
        right_margin = 8
        restart_x = (
            container.width()
            - self.restart_button.width()
            - right_margin
        )
        simulation_x = (
            restart_x
            - spacing
            - button_width
        )
        y = max(
            0,
            (tab_bar.height() - button_height) // 2
        )
        self.simulation_button.setGeometry(
            simulation_x,
            y,
            button_width,
            button_height
        )
        self.restart_button.setGeometry(
            restart_x,
            y,
            self.restart_button.width(),
            self.restart_button.height()
        )
        if self.config_tabs.currentIndex() == 1:
            self.simulation_button.show()
            self.restart_button.show()
            self.simulation_button.raise_()
            self.restart_button.raise_()
        else:
            self.simulation_button.hide()
            self.restart_button.hide()

    def sync_custom_page_width(self):
        # Do not set a fixed width on custom_page.
        # QTabWidget should manage the page width automatically.
        return

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "simulation_button"):
            QTimer.singleShot(
                0,
                self.position_simulation_button
            )
        if hasattr(self, "event_toast"):
            self.event_toast.reposition()

    def load_custom_configuration(self):
        try:
            with open(
                self.plant_yaml_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = yaml.safe_load(file) or {}

            pcs_list = data.get("pcs", [])
            for pcs in pcs_list:
                pcs_id = pcs.get("id", "")
                initial = pcs.get(
                    "initial_condition",
                    {}
                )
                soc = initial.get("SOC", 50)
                soh = initial.get("SOH", 100)
                print(
                    f"{pcs_id}: "
                    f"SOC={soc}, SOH={soh}"
                )
        except Exception as e:
            print(
                "YAML LOAD ERROR:",
                e
            )

    def toggle_simulation(self):
        if self.simulator is None:
            print("ERROR: Simulator is not available")
            return

        # =============================================
        # START SIMULATION
        # =============================================
        if not self.simulator.is_running:
            try:
                self.simulator.start(
                    self.simulator,
                    self.network_manager
                )
                self.simulation_button.setText(
                    "■ Stop Simulation"
                )
                self.simulation_button.setStyleSheet("""
                    QPushButton {
                        background: #DC2626;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 700;
                        padding: 0 12px;
                    }
                    QPushButton:hover {
                        background: #B91C1C;
                    }
                """)
                print("Simulation Started")
            except Exception as e:
                print(
                    "START SIMULATION ERROR:",
                    e
                )
        # =============================================
        # STOP SIMULATION
        # =============================================
        else:
            try:
                self.simulator.stop()
                self.simulation_button.setText(
                    "▶ Start Simulation"
                )
                self.simulation_button.setStyleSheet("""
                    QPushButton {
                        background: #16A34A;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 700;
                        padding: 0 12px;
                    }
                    QPushButton:hover {
                        background: #15803D;
                    }
                """)
                print("Simulation Stopped")
            except Exception as e:
                print(
                    "STOP SIMULATION ERROR:",
                    e
                )

    def restart_simulation(self):
        if self.simulator is None:
            print("ERROR: Simulator is not available")
            return

        try:
            new_net = self.simulator.reset(
                restart=True
            )
            if new_net is not None:
                self.network_manager = new_net
            elif hasattr(self.simulator, "_network") and self.simulator._network is not None:
                self.network_manager = self.simulator._network

            if hasattr(self, "adjacentVoltageProfile") and hasattr(self.adjacentVoltageProfile, "set_simulator"):
                self.adjacentVoltageProfile.set_simulator(self.simulator)
            if hasattr(self, "dashboardTimeSeries"):
                self.dashboardTimeSeries.simulator = self.simulator
                self.dashboardTimeSeries.update_from_simulator(self.simulator)
            if hasattr(self, "loadDistribution"):
                self.loadDistribution.simulator = self.simulator
                self.loadDistribution.update_from_simulator(self.simulator)

            if hasattr(self, "bessDispatchSchedule") and self.bessDispatchSchedule is not None:
                if getattr(self.bessDispatchSchedule, "running_event_id", None) is None:
                    self.bessDispatchSchedule.elapsed_seconds = 0
                    if hasattr(self.bessDispatchSchedule, "schedule") and self.bessDispatchSchedule.schedule:
                        self.bessDispatchSchedule.set_running_event(self.bessDispatchSchedule.schedule[0].get("event_id"))

            if hasattr(self, "gridAvailabilityControl"):
                self.gridAvailabilityControl.reload()
                if self.gridAvailabilityControl.button.isEnabled():
                    self._apply_grid_availability(self.gridAvailabilityControl.available)

            self.simulation_button.setText(
                "■ Stop Simulation"
            )
            self.simulation_button.setStyleSheet("""
                QPushButton {
                    background: #DC2626;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 700;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background: #B91C1C;
                }
            """)
            print("Simulation Restarted")

            self.update_voltage_profile()
        except Exception as e:
            print(
                "RESTART SIMULATION ERROR:",
                e
            )

    def submit_configuration(self):
        try:
            with open(
                self.plant_yaml_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = yaml.safe_load(file) or {}

            # ==================================================
            # PCS SOC / SOH
            # ==================================================
            cards = self.bankFaultCards.findChildren(
                BankFaultCard
            )
            pcs_list = data.get("pcs", [])

            for index, card in enumerate(
                cards,
                start=1
            ):
                soc = card.soc_value.value()
                soh = card.soh_value.value()
                temperature = card.initial_temperature
                pcs_id = f"PCS{index}"

                for pcs in pcs_list:
                    if pcs.get("id") == pcs_id:
                        if "initial_condition" not in pcs:
                            pcs["initial_condition"] = {}
                        pcs["initial_condition"]["SOC"] = float(soc)
                        pcs["initial_condition"]["SOH"] = float(soh)
                        pcs["initial_condition"]["Initial_Temperature_K"] = float(temperature)
                        break

            # ==================================================
            # TRANSFORMER R / X  (ALL TRANSFORMERS)
            # ==================================================
            all_impedances = self.plantControlCards.get_all_impedances()
            for transformer in data.get(
                "transformers",
                []
            ):
                tx_id = transformer.get("id")
                if tx_id in all_impedances:
                    impedance = all_impedances[tx_id]
                    if "impedance" not in transformer:
                        transformer["impedance"] = {}
                    transformer["impedance"]["r_pu"] = float(
                        impedance["r_pu"]
                    )
                    transformer["impedance"]["x_pu"] = float(
                        impedance["x_pu"]
                    )
                    print(
                        f"{tx_id} | "
                        f"R={impedance['r_pu']} pu | "
                        f"X={impedance['x_pu']} pu"
                    )

            # ==================================================
            # SAVE YAML
            # ==================================================
            with open(
                self.plant_yaml_path,
                "w",
                encoding="utf-8"
            ) as file:
                yaml.safe_dump(
                    data,
                    file,
                    sort_keys=False,
                    default_flow_style=False
                )

            print(
                "Configuration saved to plant/plant.yaml"
            )
        except Exception as e:
            print(
                "YAML SAVE ERROR:",
                e
            )

    def get_yaml_transformer_impedance(self):
        """
        Returns a list of all transformers with their
        IDs and impedance values from the YAML file.
        [
            {"id": "T1", "r_pu": 0.01, "x_pu": 0.04},
            {"id": "T2", "r_pu": 0.01, "x_pu": 0.04},
            ...
        ]
        """
        result = []
        try:
            with open(
                self.plant_yaml_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = yaml.safe_load(file) or {}

            transformers = data.get("transformers", [])
            for transformer in transformers:
                tx_id = transformer.get("id", "T?")
                impedance = transformer.get(
                    "impedance",
                    {}
                )
                result.append({
                    "id": tx_id,
                    "r_pu": impedance.get("r_pu", 0.01),
                    "x_pu": impedance.get("x_pu", 0.04),
                })
        except Exception as e:
            print(
                "TRANSFORMER YAML LOAD ERROR:",
                e
            )

        return result

    def get_yaml_soc_soh(self):
        result = {}
        try:
            with open(
                self.plant_yaml_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = yaml.safe_load(file) or {}

            for pcs in data.get("pcs", []):
                pcs_id = pcs.get("id")
                initial = pcs.get(
                    "initial_condition",
                    {}
                )
                result[pcs_id] = {
                    "SOC": initial.get("SOC", 50),
                    "SOH": initial.get("SOH", 100),
                    "Initial_Temperature_K": initial.get(
                        "Initial_Temperature_K",
                        298.15
                    ),
                }
        except Exception as e:
            print(
                "YAML LOAD ERROR:",
                e
            )

        return result

    def changeTab(self, index):
        print("Selected Tab :", index)
        # 0: OVERVIEW, 1: POWER FLOW, 2: VOLTAGE PROFILE, 3: TIME SERIES, 4: EVENTS, 5: REPORTS
        if index == 3:
            # TIME SERIES TAB: Dedicated Full Screen 1-Hour Time Series View!
            if hasattr(self, "central_stack") and hasattr(self, "timeSeriesContainer"):
                self.central_stack.setCurrentWidget(self.timeSeriesContainer)
            if hasattr(self, "timeSeriesWidget"):
                self.timeSeriesWidget.update_from_simulator(self.simulator)
        elif index == 2:
            # VOLTAGE PROFILE TAB: Focus on original layout Bus Voltages
            if hasattr(self, "central_stack") and hasattr(self, "scrollArea"):
                self.central_stack.setCurrentWidget(self.scrollArea)
            if hasattr(self, "scrollArea") and self.scrollArea:
                self.scrollArea.verticalScrollBar().setValue(0)
                self.scrollArea.horizontalScrollBar().setValue(self.scrollArea.horizontalScrollBar().maximum())
        else:
            # POWER FLOW / OVERVIEW: Original layout with Bus Voltages 100% visible
            if hasattr(self, "central_stack") and hasattr(self, "scrollArea"):
                self.central_stack.setCurrentWidget(self.scrollArea)
    
    def _update_header_timing(self):
        """Read the dispatch clock independently of plant telemetry updates."""
        schedule = getattr(self, "bessDispatchSchedule", None)
        if schedule is None or not hasattr(self, "header"):
            return
        elapsed = max(0, int(schedule.elapsed_seconds))
        self.header.update_elapsed_time(f"{elapsed // 60:02d}:{elapsed % 60:02d} / 15m")
        sim_dt = schedule.get_current_sim_datetime()
        self.header.update_simulation_time(
            sim_dt.strftime("%d-%b-%Y   %H:%M:%S") if sim_dt else "—")

    def update_ribbon(self):

        try:
            plant_db = self.simulator.plant_database
            pcs_ids = sorted(
                device_id
                for device_id in plant_db.ids()
                if device_id.startswith("PCS")
            )
            pcs_data = []

            for pcs_id in pcs_ids:
                db = plant_db.device(pcs_id)
                pcs_data.append({
                    "soc": db.value(Tags.Battery.SOC),
                    "soh": db.value(Tags.Battery.SOH),
                    "stored_energy": db.value(
                        Tags.Battery.STORED_ENERGY
                    ),
                    "active_power": db.value(
                        Tags.PCS.ACTIVE_POWER
                    ),
                    "battery_power": db.value(
                        Tags.Battery.POWER
                    ),
                    "battery_voltage": db.value(
                        Tags.Battery.VOLTAGE
                    ),
                    "battery_current": db.value(
                        Tags.Battery.CURRENT
                    ),
                    "grid_voltage": db.value(
                        Tags.PCS.AC_VOLTAGE
                    ),
                    "temperature": db.value(
                        Tags.Battery.TEMPERATURE
                    ),
                })

            # UPDATE BESS SUMMARY
            bess_rows = []

            for index, pcs in enumerate(pcs_data, start=1):
                active_power = pcs.get("active_power", 0) or 0
                soc = pcs.get("soc", 0) or 0
                stored_energy = pcs.get("stored_energy", 0) or 0

                if active_power < 0:
                    status = "Charging"
                elif active_power > 0:
                    status = "Discharging"
                else:
                    status = "Standby"

                bess_rows.append([
                    f"BESS BANK-{index}",
                    f"PCS-{index}",
                    f"{active_power / 1000:.2f}",
                    "0.00",
                    f"{soc:.0f}",
                    f"{stored_energy / 1000:.2f} / 2.00",
                    status,
                ])

            self.bessSummary.update_bess_data(
                bess_rows
            )

            grid_db = plant_db.device("PPC")
            grid_data = {
                "frequency": grid_db.value(
                    Tags.Grid.FREQUENCY
                ),
                "ac_voltage": grid_db.value(
                    Tags.PCS.AC_VOLTAGE
                ),
                "current": grid_db.value(
                    Tags.Grid.CURRENT
                ),
                "import_power": grid_db.value(
                    Tags.Grid.IMPORT_POWER
                ),
                "export_power": grid_db.value(
                    Tags.Grid.EXPORT_POWER
                ),
                "load_power": grid_db.value(
                    Tags.Network.LOAD_POWER
                ),
                "network_losses": grid_db.value(
                    Tags.Network.NETWORK_LOSSES
                ),
                "bess_power": grid_db.value(Tags.Battery.POWER),
                "bess_soc": grid_db.value(Tags.Battery.SOC),
                "bess_stored_energy": grid_db.value(Tags.Battery.STORED_ENERGY),
            }

            # Get active running event from dispatch schedule
            active_ev = None
            if hasattr(self, "bessDispatchSchedule") and hasattr(self.bessDispatchSchedule, "running_row_index"):
                idx = self.bessDispatchSchedule.running_row_index
                if idx is not None and hasattr(self.bessDispatchSchedule,
                                "schedule_data") and self.bessDispatchSchedule.schedule_data:
                    if 0 <= idx < len(self.bessDispatchSchedule.schedule_data):
                        active_ev = self.bessDispatchSchedule.schedule_data[idx]

            # UPDATE RIBBON
            self.ribbon.update_data(
                grid_data,
                pcs_data,
                solar_data={"active_power": (grid_db.value(Tags.SOLAR.PV_POWER)
                                              if grid_db.exists(Tags.SOLAR.PV_POWER) else 0.0)},
                schedule_data=self.bessDispatchSchedule.result_data,
                active_event=active_ev  or {},
            )

            latest_load = grid_data.get("load_power", 0) or 0
            self.bessDispatchSchedule.update_twin_load(
                latest_load
            )

            self._update_header_timing()
            

        except Exception as e:

            print(
                "RIBBON ERROR:",
                e
            )

    def update_voltage_profile(self):
        if self.simulator and getattr(self.simulator, "_network", None) is not None:
            self.network_manager = self.simulator._network

        if not self.network_manager:
            print("ERROR: NetworkManager is None")
            return

        profile = self.network_manager.voltage_profile

        if not profile:
            print("Voltage profile is empty")
            return

        # VOLTAGE PROFILE CHARTS
        if hasattr(self, "adjacentVoltageProfile"):
            self.adjacentVoltageProfile.update_voltage_data(
                profile
            )

        # The bus table has its own data input, separate from the chart.
        if hasattr(self, "bessSummary"):
            self.bessSummary.update_voltage_data(profile)

        # BRANCH SUMMARY (DYNAMIC FROM TOPOLOGY & NETWORK)
        if hasattr(self, "branchSummary"):
            self.branchSummary.update_from_network(
                self.network_manager
            )

        # 1-HOUR TIME SERIES CHARTS
        if hasattr(self, "timeSeriesWidget"):
            self.timeSeriesWidget.update_from_simulator(
                self.simulator
            )
        if hasattr(self, "dashboardTimeSeries"):
            self.dashboardTimeSeries.update_from_simulator(
                self.simulator
            )

        # LOAD DISTRIBUTION
        if hasattr(self, "loadDistribution"):
            self.loadDistribution.update_from_simulator(
                self.simulator
            )
