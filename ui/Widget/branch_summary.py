import os
import yaml
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

    def __init__(self, parent=None, plant_yaml_path="plant/plant.yaml"):
        super().__init__(parent)

        self.setObjectName("BranchSummaryWidget")
        self.setFixedSize(400, 250)
        self.plant_yaml_path = plant_yaml_path
        self.branch_definitions = []

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
                font-size: 11px;
                font-weight: bold;
            }

            QTableWidget {
                background: #FFFFFF;
                color: #263238;
                border: none;
                gridline-color: #DDE3E8;
                font-family: Arial;
                font-size: 8.5px;
                selection-background-color: #EAF2F8;
                selection-color: #263238;
            }

            QTableWidget::item {
                padding: 0px 2px;
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
                font-size: 7.5px;
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
        title = QLabel("BRANCH SUMMARY (PLANT TOPOLOGY)")
        title.setObjectName("title")
        title.setFixedHeight(24)
        layout.addWidget(title)

        # ==================================================
        # TABLE (DYNAMIC FROM plant.yaml)
        # ==================================================
        self.table = QTableWidget()
        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "Branch",
            "From",
            "To",
            "P (MW)",
            "Q (MVar)",
            "Load (%)",
            "Status",
        ])

        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.horizontalHeader().setSectionsMovable(False)

        header = self.table.horizontalHeader()
        for column in range(7):
            header.setSectionResizeMode(column, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 48)   # Branch / Feeder
        self.table.setColumnWidth(1, 62)   # From
        self.table.setColumnWidth(2, 62)   # To
        self.table.setColumnWidth(3, 44)   # P
        self.table.setColumnWidth(4, 44)   # Q
        self.table.setColumnWidth(5, 48)   # Load%
        self.table.setColumnWidth(6, 56)   # Status

        layout.addWidget(self.table)

        # Initial dynamic build from plant.yaml
        self.reload_from_topology(self.plant_yaml_path)

    # ==================================================
    # TOPOLOGY LOADER
    # ==================================================
    def load_topology(self, yaml_path=None):
        path = yaml_path or self.plant_yaml_path or "plant/plant.yaml"
        if not os.path.exists(path):
            alt_path = os.path.join(os.path.dirname(__file__), "..", "..", "plant", "plant.yaml")
            if os.path.exists(alt_path):
                path = alt_path

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading plant.yaml in BranchSummary: {e}")
        return {}

    def reload_from_topology(self, yaml_path=None):
        topology = self.load_topology(yaml_path)
        self.branch_definitions = self.build_branches_from_topology(topology)
        self.populate_initial_table()

    def build_branches_from_topology(self, topology):
        """
        Dynamically extract branches from plant.yaml:
        - Transformers (T1, T2, T3, etc.)
        - Feeders mapped to devices (PCS1..5, PV1, LOAD)
        """
        branches = []
        if not topology:
            # Fallback baseline if topology file is missing
            return [
                {"id": "T1", "type": "transformer", "index": 0, "branch": "T1", "from": "GRID_33KV", "to": "BUS_433_A", "p": 0.0, "q": 0.0, "loading": 0.0, "status": "Closed"},
                {"id": "T2", "type": "transformer", "index": 1, "branch": "T2", "from": "GRID_33KV", "to": "BUS_433_B", "p": 0.0, "q": 0.0, "loading": 0.0, "status": "Closed"},
                {"id": "T3", "type": "transformer", "index": 2, "branch": "T3", "from": "GRID_33KV", "to": "BUS_433_C", "p": 0.0, "q": 0.0, "loading": 0.0, "status": "Closed"},
            ]

        # 1. Map feeders to devices (PCS, PV)
        feeder_device_map = {}
        for pcs in topology.get("pcs", []):
            f_id = pcs.get("feeder")
            if f_id:
                feeder_device_map[f_id] = pcs.get("id", "PCS")

        for pv in topology.get("pv", []):
            f_id = pv.get("feeder")
            if f_id:
                feeder_device_map[f_id] = pv.get("id", "PV")

        # 2. Transformers
        for index, tx in enumerate(topology.get("transformers", [])):
            tx_id = tx.get("id", f"T{index+1}")
            hv = tx.get("hv_bus", "GRID_33KV")
            lv = tx.get("lv_bus", "BUS_433")
            rating = float(tx.get("rating_kva", 2500))
            branches.append({
                "id": tx_id,
                "type": "transformer",
                "index": index,
                "branch": tx_id,
                "from": hv,
                "to": lv,
                "rating_kva": rating,
                "p": 0.0,
                "q": 0.0,
                "loading": 0.0,
                "status": "Closed",
            })

        # 3. Feeders
        for index, f in enumerate(topology.get("feeders", [])):
            f_id = f.get("id", f"FDR_{index+1}")
            dev_name = feeder_device_map.get(f_id)
            if dev_name:
                label = dev_name
            elif "LOAD" in f_id.upper():
                label = "LOAD"
            elif "PV" in f_id.upper():
                label = "PV1"
            else:
                label = f_id.replace("_FEEDER", "")

            from_bus = f.get("from", "")
            to_bus = f.get("to", "")
            branches.append({
                "id": f_id,
                "type": "feeder",
                "index": index,
                "branch": label,
                "from": from_bus,
                "to": to_bus,
                "device": dev_name,
                "p": 0.0,
                "q": 0.0,
                "loading": 0.0,
                "status": "Closed",
            })

        return branches

    # ==================================================
    # TABLE POPULATION
    # ==================================================
    def populate_initial_table(self):
        self.table.setRowCount(len(self.branch_definitions))

        for row, b in enumerate(self.branch_definitions):
            self.table.setRowHeight(row, 16)

            # Values
            row_data = [
                b.get("branch", ""),
                b.get("from", ""),
                b.get("to", ""),
                f"{b.get('p', 0.0):.2f}",
                f"{b.get('q', 0.0):.2f}",
                f"{b.get('loading', 0.0):.1f}",
                b.get("status", "Closed"),
            ]

            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#263238"))
                self.table.setItem(row, col, item)

            self._style_row(row, b.get("loading", 0.0), b.get("status", "Closed"))

    def _style_row(self, row, loading_val, status_str):
        # Status Color
        status_item = self.table.item(row, 6)
        if status_item:
            s_low = str(status_str).lower()
            if s_low == "closed":
                status_item.setForeground(QColor("#25A244"))
            elif s_low == "open":
                status_item.setForeground(QColor("#E53935"))
            status_item.setFont(QFont("Arial", 8, QFont.Bold))

        # Loading Color
        load_item = self.table.item(row, 5)
        if load_item:
            try:
                l_num = float(loading_val)
                if l_num >= 80:
                    load_item.setForeground(QColor("#E53935"))
                elif l_num >= 50:
                    load_item.setForeground(QColor("#F39C12"))
                else:
                    load_item.setForeground(QColor("#25A244"))
            except (ValueError, TypeError):
                pass

    def update_row_values(self, row, p, q, loading, status="Closed"):
        if 0 <= row < self.table.rowCount():
            item_p = self.table.item(row, 3)
            if item_p:
                item_p.setText(f"{float(p):.2f}")

            item_q = self.table.item(row, 4)
            if item_q:
                item_q.setText(f"{float(q):.2f}")

            item_load = self.table.item(row, 5)
            if item_load:
                item_load.setText(f"{float(loading):.1f}")

            item_stat = self.table.item(row, 6)
            if item_stat:
                item_stat.setText(str(status))

            self._style_row(row, loading, status)

    # ==================================================
    # LIVE UPDATE FROM NETWORK MANAGER
    # ==================================================
    def update_from_network(self, network_manager):
        if not network_manager:
            return
        backend = getattr(network_manager, "backend", None)
        if not backend or not hasattr(backend, "grid") or backend.grid is None:
            return

        for row, b in enumerate(self.branch_definitions):
            b_type = b.get("type")
            idx = b.get("index", 0)

            if b_type == "transformer":
                try:
                    loading = float(backend.transformer_loading(idx))
                    trafo = backend.grid.transformers[idx]
                    s_rated_mva = float(trafo['S_n_kVA']) / 1000.0
                    s_actual_mva = s_rated_mva * (loading / 100.0)
                    p_mw = s_actual_mva * 0.95
                    q_mvar = s_actual_mva * 0.31
                    status = "Closed"
                    self.update_row_values(row, p_mw, q_mvar, loading, status)
                except Exception:
                    pass

            elif b_type == "feeder":
                try:
                    dev_id = b.get("device")
                    p_mw = 0.0
                    q_mvar = 0.0
                    loading = 0.0
                    status = "Closed"

                    feeders_data = backend.data.get("grid_feeders", []) if hasattr(backend, "data") and backend.data else []
                    matched_f = None
                    if dev_id:
                        for gf in feeders_data:
                            if gf.get("code") == dev_id or gf.get("code", "").startswith(dev_id):
                                matched_f = gf
                                break

                    if matched_f:
                        p_kw = sum(matched_f.get("kW", [0.0]))
                        q_kvar = sum(matched_f.get("kvar", [0.0]))
                        p_mw = abs(p_kw) / 1000.0
                        q_mvar = abs(q_kvar) / 1000.0
                        loading = min(100.0, (abs(p_kw) / 1100.0) * 100.0)
                    elif "LOAD" in b.get("id", "").upper():
                        loads_data = backend.data.get("loads", []) if hasattr(backend, "data") and backend.data else []
                        tot_load_kva = sum(l.get("kVA", 0.0) for l in loads_data)
                        p_mw = (tot_load_kva * 0.95) / 1000.0
                        q_mvar = (tot_load_kva * 0.31) / 1000.0
                        loading = min(100.0, (tot_load_kva / 2500.0) * 100.0)

                    self.update_row_values(row, p_mw, q_mvar, loading, status)
                except Exception:
                    pass

    # ==================================================
    # LEGACY / CUSTOM UPDATE SUPPORT
    # ==================================================
    def update_branch_data(self, branches):
        if not branches:
            return

        rows = []
        for branch in branches:
            rows.append([
                branch.get("branch", branch.get("id", "")),
                branch.get("from", ""),
                branch.get("to", ""),
                f"{branch.get('p', 0):.2f}",
                f"{branch.get('q', 0):.2f}",
                str(branch.get("loading", 0)),
                branch.get("status", "Closed"),
            ])

        self.table.setRowCount(len(rows))
        for row, row_data in enumerate(rows):
            self.table.setRowHeight(row, 16)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#263238"))
                self.table.setItem(row, col, item)
            self._style_row(row, row_data[5], row_data[6])