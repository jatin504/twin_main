import yaml

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QTabWidget,
    QSizePolicy,
)

from state.tags import Tags
from pui.Widget.header import HeaderWidget
from pui.Widget.navbar import NavBar
from pui.Widget.ribbon import Ribbon
from pui.Widget.power_flow import PowerFlowWidget
from pui.Widget.voltage_profile_widget import VoltageProfileWidget
from pui.Widget.bus_voltage_summary import BusVoltageSummaryWidget
from pui.Widget.branch_summary import BranchSummaryWidget
from pui.Widget.bess_summary import BessSummaryWidget
from pui.Widget.bank_fault_cards import (
    BankFaultCards,
    BankFaultCard,
)
from pui.Widget.plant_control_cards import PlantControlCards


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
        custom_layout.addWidget(
                plant_title
        )
        custom_layout.addSpacing(2)
        self.plantControlCards = PlantControlCards(
            initial_values=self.get_yaml_transformer_impedance()
        )
        custom_layout.addWidget(
            self.plantControlCards,
            0,
            Qt.AlignTop
        )
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
       

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.scrollArea.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.scrollArea.setFrameShape(
            QScrollArea.NoFrame
        )

        self.scrollArea.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout.addWidget(
            self.scrollArea,
            1
        )

       
        # SCROLL CONTENT
       

        scrollContent = QWidget()

        scrollLayout = QVBoxLayout(scrollContent)
        scrollLayout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        scrollLayout.setSpacing(0)

        scrollLayout.setAlignment(Qt.AlignTop)

       
        # FIRST ROW
        powerFlowRow = QWidget()
        powerFlowRow.setFixedHeight(570)

        self.powerFlow = PowerFlowWidget(
            network_manager=self.simulator
        )
        self.voltageProfile = VoltageProfileWidget()
        self.busVoltageSummary = BusVoltageSummaryWidget()

        # POWER FLOW
        self.powerFlow.setParent(powerFlowRow)
        self.powerFlow.move(0, 0)

       
        # VOLTAGE PROFILE
        self.voltageProfile.setParent(powerFlowRow)
        self.voltageProfile.move(1190, 0)

        # BUS VOLTAGE SUMMARY
        self.busVoltageSummary.setParent(powerFlowRow)
        self.busVoltageSummary.move(1190, 310)
        
        # SHOW
        self.powerFlow.show()
        self.voltageProfile.show()
        self.busVoltageSummary.show()

        # ADD FIRST ROW
        scrollLayout.addWidget(
            powerFlowRow
        )

        # SECOND ROW - BRANCH SUMMARY
        self.branchSummary = BranchSummaryWidget()
        self.branchSummary.setParent(scrollContent)
        self.branchSummary.setGeometry(
            0,
            510,
            400,
            190
        )
        self.branchSummary.show()
        
        self.bessSummary = BessSummaryWidget()
        self.bessSummary.setParent(scrollContent)

        self.bessSummary.setGeometry(
            410,
            510,
            600,
            190
        )

        self.bessSummary.show()

        scrollContent.setMinimumHeight(760)

        # SET SCROLL CONTENT
        self.scrollArea.setWidget(
            scrollContent
        )

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
            self.simulator.reset(
                restart=True
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
            print("Simulation Restarted")
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
            # TRANSFORMER R / X
            # ==================================================
            impedance = self.plantControlCards.get_impedance()
            for transformer in data.get(
                "transformers",
                []
            ):
                if transformer.get("id") == "T1":
                    if "impedance" not in transformer:
                        transformer["impedance"] = {}
                    transformer["impedance"]["r_pu"] = float(
                        impedance["r_pu"]
                    )
                    transformer["impedance"]["x_pu"] = float(
                        impedance["x_pu"]
                    )
                    print(
                        f"T1 | "
                        f"R={impedance['r_pu']} pu | "
                        f"X={impedance['x_pu']} pu"
                    )
                    break

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
        try:
            with open(
                self.plant_yaml_path,
                "r",
                encoding="utf-8"
            ) as file:
                data = yaml.safe_load(file) or {}

            transformers = data.get("transformers", [])
            for transformer in transformers:
                if transformer.get("id") == "T1":
                    impedance = transformer.get(
                        "impedance",
                        {}
                    )
                    return {
                        "r_pu": impedance.get("r_pu", 0.01),
                        "x_pu": impedance.get("x_pu", 0.04),
                    }
        except Exception as e:
            print(
                "TRANSFORMER YAML LOAD ERROR:",
                e
            )

        return {
            "r_pu": 0.01,
            "x_pu": 0.04,
        }

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

    def update_ribbon(self):

        try:
            plant_db = self.simulator.plant_database
            pcs_ids = sorted(
                device_id
                for device_id in plant_db.ids()
                if device_id.startswith("PCS")
            )[:4]
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
            }

            
            # UPDATE RIBBON
            self.ribbon.update_data(
                grid_data,
                pcs_data,
            )

            
            # UPDATE BESS SUMMARY
            bess_rows = []

            for index, pcs in enumerate(pcs_data, start=1):
                active_power = pcs.get("active_power", 0)
                soc = pcs.get("soc", 0)
                stored_energy = pcs.get("stored_energy", 0)

                if active_power < 0:
                    status = "Discharging"
                elif active_power > 0:
                    status = "Charging"
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

        except Exception as e:

            print(
                "RIBBON ERROR:",
                e
            )

    def update_voltage_profile(self):

        if not self.network_manager:
            print("ERROR: NetworkManager is None")
            return

        profile = self.network_manager.voltage_profile

        print("UI PROFILE:", profile)

        if not profile:
            print("Voltage profile is empty")
            return

        # VOLTAGE PROFILE CHART
        self.voltageProfile.update_voltage_data(
            profile
        )

        # BUS VOLTAGE SUMMARY
        self.busVoltageSummary.update_voltage_data(
            profile
        )