from __future__ import annotations

import math
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QBrush,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QScrollArea,
)


class VoltageProfileCanvas(QWidget):
    """
    QPainter-based spatial per-unit voltage profile chart across all network buses.
    Supports both compact embed view and high-definition fullscreen display.
    """

    BUS_BASE_KV = {
        "GRID_33KV": 33.0,
        "GRID_33kV": 33.0,
        "BUS_433_A": 0.433,
        "BUS_433_B": 0.433,
        "BUS_433_C": 0.433,
        "PCS_BUS": 0.433,
        "PV_BUS": 0.433,
        "LOAD_BUS": 0.433,
    }

    def __init__(self, parent=None, fullscreen: bool = False):
        super().__init__(parent)
        self.fullscreen = fullscreen
        self.bus_names: list[str] = []
        self.voltage_data: list[float] = []
        self.voltage_dict: dict[str, float] = {}

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(False)
        self.hover_pos: QPoint | None = None
        self.hover_active: bool = False

    def update_voltage_data(self, bus_voltages: dict):
        if not isinstance(bus_voltages, dict):
            return
        self.voltage_dict = dict(bus_voltages)
        self.bus_names = []
        self.voltage_data = []

        for bus_name, voltage in bus_voltages.items():
            self.bus_names.append(str(bus_name))
            try:
                self.voltage_data.append(float(voltage))
            except (ValueError, TypeError):
                self.voltage_data.append(1.0)

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas Bounds
        if self.fullscreen:
            left = 58
            top = 26
            right = w - 24
            bottom = h - 65
        else:
            left = 44
            top = 14
            right = w - 16
            bottom = h - 50

        chart_width = max(10, right - left)
        chart_height = max(10, bottom - top)

        # Background
        p.fillRect(self.rect(), QColor("#FFFFFF"))

        # No Data Fallback
        if not self.voltage_data:
            p.setPen(QColor("#64748B"))
            p.setFont(QFont("Segoe UI", 9 if not self.fullscreen else 11))
            p.drawText(self.rect(), Qt.AlignCenter, "Waiting for spatial bus voltage profile...")
            return

        # Dynamic Y-Axis Scaling
        data_min = min(self.voltage_data)
        data_max = max(self.voltage_data)

        if data_min == data_max:
            padding = max(abs(data_min) * 0.05, 0.02)
        else:
            padding = max((data_max - data_min) * 0.25, 0.02)

        min_voltage = min(data_min - padding, 0.90)
        max_voltage = max(data_max + padding, 1.10)

        # Fix to 5-6 clean steps
        tick_count = 6 if self.fullscreen else 5
        step = (max_voltage - min_voltage) / (tick_count - 1)
        y_axis_values = [min_voltage + (step * i) for i in range(tick_count)]

        # -----------------------------------------------------------------
        # NORMAL OPERATING ZONE SHADING (0.95 to 1.05 p.u.)
        # -----------------------------------------------------------------
        y_norm_high = bottom - ((min(max_voltage, max(min_voltage, 1.05)) - min_voltage) / (max_voltage - min_voltage)) * chart_height
        y_norm_low = bottom - ((min(max_voltage, max(min_voltage, 0.95)) - min_voltage) / (max_voltage - min_voltage)) * chart_height
        norm_band_h = max(0, int(y_norm_low - y_norm_high))
        if norm_band_h > 0:
            p.fillRect(left, int(y_norm_high), chart_width, norm_band_h, QColor(240, 253, 244, 100))

        # -----------------------------------------------------------------
        # HORIZONTAL GRID & Y-AXIS LABELS (ALL ON LEFT SIDE)
        # -----------------------------------------------------------------
        grid_pen = QPen(QColor("#F1F5F9"), 1, Qt.SolidLine)
        axis_font = QFont("Segoe UI", 7 if not self.fullscreen else 8)
        p.setFont(axis_font)

        for val in y_axis_values:
            y = bottom - ((val - min_voltage) / (max_voltage - min_voltage)) * chart_height
            p.setPen(grid_pen)
            p.drawLine(left, int(y), right, int(y))

            # Y-Axis label on the LEFT side, cleanly right-aligned to axis line
            p.setPen(QColor("#475569"))
            p.drawText(QRect(2, int(y - 8), left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, f"{val:.3f}")

        # Nominal 1.000 p.u. Center Line
        if min_voltage <= 1.00 <= max_voltage:
            y_100 = bottom - ((1.00 - min_voltage) / (max_voltage - min_voltage)) * chart_height
            p.setPen(QPen(QColor("#94A3B8"), 1, Qt.DashLine))
            p.drawLine(left, int(y_100), right, int(y_100))

        # Voltage Limit Threshold Lines
        limits = [
            (1.10, "#E53935", "1.10 High Trip"),     # Red - High limit
            (1.05, "#D97706", "1.05 High Warn"),    # Amber - High warning
            (0.95, "#D97706", "0.95 Low Warn"),     # Amber - Low warning
            (0.90, "#E53935", "0.90 Low Trip"),     # Red - Low limit
        ]

        p.setFont(QFont("Segoe UI", 6.5 if not self.fullscreen else 7.5))
        for limit_val, color, lbl_text in limits:
            if min_voltage <= limit_val <= max_voltage:
                y = bottom - ((limit_val - min_voltage) / (max_voltage - min_voltage)) * chart_height
                p.setPen(QPen(QColor(color), 1, Qt.DashLine))
                p.drawLine(left, int(y), right, int(y))

                # Limit label badge at the right edge
                if self.fullscreen or chart_width > 280:
                    p.setPen(QColor(color))
                    p.drawText(right - (68 if not self.fullscreen else 82), int(y - 2), lbl_text)

        # -----------------------------------------------------------------
        # VERTICAL GRID & BUS POSITIONS
        # -----------------------------------------------------------------
        num_buses = len(self.voltage_data)
        bus_x_coords = []
        for i in range(num_buses):
            if num_buses == 1:
                x = left + chart_width / 2
            else:
                x = left + (i / (num_buses - 1)) * chart_width
            bus_x_coords.append(int(x))

            # Light vertical grid line
            p.setPen(QPen(QColor("#F1F5F9"), 1))
            p.drawLine(int(x), top, int(x), bottom)

            # Axis tick mark extending downwards
            p.setPen(QPen(QColor("#CBD5E1"), 1.2))
            p.drawLine(int(x), bottom, int(x), bottom + 4)

        # Baseline axis borders
        p.setPen(QPen(QColor("#CBD5E1"), 1.2))
        p.drawLine(left, bottom, right, bottom)
        p.drawLine(left, top, left, bottom)
        p.setPen(QPen(QColor("#E2E8F0"), 1.0))
        p.drawLine(right, top, right, bottom)

        # -----------------------------------------------------------------
        # VOLTAGE CONNECTING LINE
        # -----------------------------------------------------------------
        points = []
        for i, value in enumerate(self.voltage_data):
            x = bus_x_coords[i]
            y = bottom - ((value - min_voltage) / (max_voltage - min_voltage)) * chart_height
            points.append(QPoint(int(x), int(y)))

        if len(points) >= 2:
            p.setPen(QPen(QColor("#3B82F6"), 2.2 if not self.fullscreen else 2.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPolyline(points)

        # -----------------------------------------------------------------
        # BUS POINTS AND VALUES (STAGGERED TO NEVER OVERLAP)
        # -----------------------------------------------------------------
        val_font = QFont("Segoe UI", 6.5 if not self.fullscreen else 8, QFont.Bold)
        p.setFont(val_font)

        # Stagger offsets if buses are close horizontally (< 50px apart)
        spacing = chart_width / max(1, num_buses - 1)
        stagger = (spacing < 50)

        for i, point in enumerate(points):
            value = self.voltage_data[i]
            if value > 1.10 or value < 0.90:
                point_color = QColor("#E53935")
            elif value > 1.05 or value < 0.95:
                point_color = QColor("#D97706")
            else:
                point_color = QColor("#2563EB")

            # Point dot
            pt_radius = 4 if not self.fullscreen else 5
            p.setPen(QPen(QColor("#FFFFFF"), 1.5))
            p.setBrush(QBrush(point_color))
            p.drawEllipse(point, pt_radius, pt_radius)

            # Numerical value above point
            p.setPen(point_color)
            val_str = f"{value:.3f}"
            str_w = p.fontMetrics().horizontalAdvance(val_str)
            y_off = (-7 if (i % 2 == 0 or not stagger) else -18) if not self.fullscreen else -9
            p.drawText(point.x() - str_w // 2, point.y() + y_off, val_str)

        # -----------------------------------------------------------------
        # ANGLED BUS LABELS (CLEAN ROTATION - ZERO COLLISION)
        # -----------------------------------------------------------------
        label_font = QFont("Segoe UI", 6.5 if not self.fullscreen else 7.5, QFont.DemiBold)
        p.setFont(label_font)
        p.setPen(QColor("#334155"))

        for i, bus_name in enumerate(self.bus_names):
            x = bus_x_coords[i]
            label = bus_name.replace("_", " ")
            label_w = p.fontMetrics().horizontalAdvance(label)

            p.save()
            # Translate directly below tick, rotate -45, draw text extending down-left
            p.translate(int(x), bottom + 8)
            p.rotate(-45)
            p.drawText(-label_w - 2, 4, label)
            p.restore()



class VoltageProfileFullscreenDialog(QDialog):
    """
    Dedicated Full-Screen Dialog for Spatial Bus Voltage Profile.
    - Zero black screen flash, crisp white industrial SCADA background.
    - Full-sized expanded VoltageProfileCanvas with generous margin and clear bus labels.
    - Tooltip-free bus voltage display.
    - Bottom SCADA summary table showing all buses with Base kV, p.u. voltage, actual voltage, and status.
    - Esc or ✕ button exits cleanly and instantly.
    """

    def __init__(self, simulator=None, voltage_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.simulator = simulator
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Spatial Bus Voltage Profile (Fullscreen)")
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_lbl = QLabel("⚡ SPATIAL BUS VOLTAGE PROFILE (p.u.)")
        title_lbl.setStyleSheet("""
            QLabel {
                color: #0F172A;
                font-size: 13px;
                font-weight: 800;
                font-family: 'Segoe UI', sans-serif;
                border: none;
            }
        """)
        subtitle_lbl = QLabel("High-resolution per-unit spatial voltage distribution across plant buses and transformers")
        subtitle_lbl.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 500; border: none;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Status Chips
        live_chip = QLabel("● LIVE MONITORING")
        live_chip.setStyleSheet("""
            QLabel {
                background: #ECFDF5;
                color: #059669;
                border: 1px solid #A7F3D0;
                border-radius: 12px;
                font-size: 9.5px;
                font-weight: 700;
                padding: 4px 10px;
            }
        """)
        header_row.addWidget(live_chip)

        norm_chip = QLabel("Normal Band: 0.95 - 1.05 p.u.")
        norm_chip.setStyleSheet("""
            QLabel {
                background: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                font-size: 9.5px;
                font-weight: 600;
                padding: 4px 10px;
            }
        """)
        header_row.addWidget(norm_chip)

        limit_chip = QLabel("Limits: 0.90 / 1.10 p.u.")
        limit_chip.setStyleSheet("""
            QLabel {
                background: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 12px;
                font-size: 9.5px;
                font-weight: 600;
                padding: 4px 10px;
            }
        """)
        header_row.addWidget(limit_chip)

        # Close Button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(28, 28)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setToolTip("Exit Fullscreen (Esc)")
        self.close_button.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #EF4444;
                color: #FFFFFF;
                border: 1px solid #EF4444;
            }
        """)
        self.close_button.clicked.connect(self.close)
        header_row.addWidget(self.close_button)

        main_layout.addLayout(header_row)

        # Full-Screen Chart Canvas
        self.canvas = VoltageProfileCanvas(self, fullscreen=True)
        main_layout.addWidget(self.canvas, 1)

        # Bottom SCADA Bus Summary Cards Area
        self.bottom_panel = QFrame()
        self.bottom_panel.setFixedHeight(120)
        self.bottom_panel.setStyleSheet("""
            QFrame {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        bottom_layout = QVBoxLayout(self.bottom_panel)
        bottom_layout.setContentsMargins(10, 6, 10, 6)
        bottom_layout.setSpacing(4)

        summary_header = QHBoxLayout()
        summary_title = QLabel("BUS VOLTAGE STATUS OVERVIEW")
        summary_title.setStyleSheet("color: #0F172A; font-size: 10px; font-weight: 800; border: none;")
        summary_header.addWidget(summary_title)
        summary_header.addStretch()

        self.summary_stats = QLabel("Buses Monitored: 0 | All Nominal")
        self.summary_stats.setStyleSheet("color: #059669; font-size: 9.5px; font-weight: 600; border: none;")
        summary_header.addWidget(self.summary_stats)
        bottom_layout.addLayout(summary_header)

        # Cards scroll area for bus details
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFixedHeight(80)
        self.cards_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #F8FAFC;
            }
            QScrollArea > QWidget > QWidget {
                background: #F8FAFC;
            }
        """)
        if self.cards_scroll.viewport():
            self.cards_scroll.viewport().setStyleSheet("background: #F8FAFC;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: #F8FAFC;")
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_scroll.setWidget(self.cards_container)
        bottom_layout.addWidget(self.cards_scroll)

        main_layout.addWidget(self.bottom_panel)

        # Initialize with passed voltage data
        if voltage_data:
            self.update_voltage_data(voltage_data)

        # Auto-update timer from simulator
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_simulator)
        self.timer.start(1000)

    def _poll_simulator(self):
        if self.simulator and getattr(self.simulator, "_network", None) is not None:
            profile = getattr(self.simulator._network, "voltage_profile", None)
            if profile:
                self.update_voltage_data(profile)

    def update_voltage_data(self, bus_voltages: dict):
        if not bus_voltages:
            return
        self.canvas.update_voltage_data(bus_voltages)

        # Refresh cards
        # Clear existing card widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        crit_count = 0
        warn_count = 0
        for bus_name, volt in bus_voltages.items():
            try:
                v = float(volt)
            except Exception:
                v = 1.0

            base_kv = VoltageProfileCanvas.BUS_BASE_KV.get(bus_name, 0.433)
            act_v = v * base_kv * (1000.0 if base_kv < 1.0 else 1.0)
            v_unit = "V" if base_kv < 1.0 else "kV"

            if v > 1.10 or v < 0.90:
                card_border = "#EF4444"
                status_color = "#DC2626"
                status_pill = "TRIP"
                crit_count += 1
            elif v > 1.05 or v < 0.95:
                card_border = "#F59E0B"
                status_color = "#D97706"
                status_pill = "WARN"
                warn_count += 1
            else:
                card_border = "#E2E8F0"
                status_color = "#059669"
                status_pill = "OK"

            card = QFrame()
            card.setFixedSize(145, 68)
            card.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF;
                    border: 1px solid {card_border};
                    border-radius: 6px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(7, 5, 7, 5)
            c_layout.setSpacing(2)

            top_row = QHBoxLayout()
            b_lbl = QLabel(bus_name.replace("_", " "))
            b_lbl.setStyleSheet("color: #0F172A; font-size: 9px; font-weight: 700; border: none;")
            top_row.addWidget(b_lbl)
            top_row.addStretch()

            pill = QLabel(status_pill)
            pill.setStyleSheet(f"color: {status_color}; font-size: 8px; font-weight: 800; border: none;")
            top_row.addWidget(pill)
            c_layout.addLayout(top_row)

            val_lbl = QLabel(f"{v:.4f} p.u.")
            val_lbl.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 800; border: none;")
            c_layout.addWidget(val_lbl)

            act_lbl = QLabel(f"{act_v:.1f} {v_unit} (Base {base_kv}kV)")
            act_lbl.setStyleSheet("color: #64748B; font-size: 8px; font-weight: 500; border: none;")
            c_layout.addWidget(act_lbl)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

        if crit_count > 0:
            self.summary_stats.setText(f"Buses Monitored: {len(bus_voltages)} | ⚠️ {crit_count} Critical Out of Range")
            self.summary_stats.setStyleSheet("color: #DC2626; font-size: 9.5px; font-weight: 700; border: none;")
        elif warn_count > 0:
            self.summary_stats.setText(f"Buses Monitored: {len(bus_voltages)} | ⚡ {warn_count} in Warning Band")
            self.summary_stats.setStyleSheet("color: #D97706; font-size: 9.5px; font-weight: 700; border: none;")
        else:
            self.summary_stats.setText(f"Buses Monitored: {len(bus_voltages)} | All Nominal (1.000 p.u.)")
            self.summary_stats.setStyleSheet("color: #059669; font-size: 9.5px; font-weight: 600; border: none;")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class VoltageProfileWidget(QFrame):
    """
    Dedicated Bus Voltage Profile (p.u.) Widget with modern SCADA styling,
    clean non-overlapping bus labels, and full-screen expansion option.
    """

    def __init__(self, simulator=None, parent=None, width: int = 330, height: int = 300):
        super().__init__(parent)
        self.simulator = simulator
        self.last_voltage_profile: dict = {}
        self.fullscreen_dialog: VoltageProfileFullscreenDialog | None = None

        if width > 0:
            self.setFixedWidth(width)
        if height > 0:
            self.setFixedHeight(height)

        self.setStyleSheet("""
            VoltageProfileWidget {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        title = QLabel("VOLTAGE PROFILE (p.u.)")
        title.setStyleSheet("""
            color: #0F172A;
            font-size: 10.5px;
            font-weight: 800;
            font-family: 'Segoe UI', sans-serif;
            border: none;
        """)
        header_row.addWidget(title)

        limits_badge = QLabel("0.90 - 1.10")
        limits_badge.setStyleSheet("""
            QLabel {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 9px;
                font-size: 8.5px;
                font-weight: 700;
                padding: 1px 6px;
            }
        """)
        header_row.addWidget(limits_badge)

        header_row.addStretch()

        # Fullscreen Button (Identical to 1-HR TRENDS button)
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setFixedSize(22, 22)
        self.fullscreen_button.setCursor(Qt.PointingHandCursor)
        self.fullscreen_button.setToolTip("Fullscreen")
        self.fullscreen_button.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #E2E8F0;
                color: #2563EB;
            }
        """)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        header_row.addWidget(self.fullscreen_button)

        layout.addLayout(header_row)

        # Voltage Profile Canvas
        self.bus_canvas = VoltageProfileCanvas(self)
        layout.addWidget(self.bus_canvas, 1)

    def _toggle_fullscreen(self):
        if self.fullscreen_dialog is not None:
            try:
                self.fullscreen_dialog.close()
            except Exception:
                pass
            self.fullscreen_dialog = None
            return

        dialog = VoltageProfileFullscreenDialog(
            simulator=self.simulator,
            voltage_data=self.last_voltage_profile or self.bus_canvas.voltage_dict,
            parent=self.window(),
        )
        self.fullscreen_dialog = dialog

        def _on_closed(_result=None):
            self.fullscreen_dialog = None

        dialog.finished.connect(_on_closed)
        dialog.showFullScreen()

    def update_voltage_data(self, bus_voltages: dict):
        self.last_voltage_profile = bus_voltages
        self.bus_canvas.update_voltage_data(bus_voltages)
        if self.fullscreen_dialog is not None:
            try:
                self.fullscreen_dialog.update_voltage_data(bus_voltages)
            except Exception:
                pass

    def set_simulator(self, simulator):
        self.simulator = simulator