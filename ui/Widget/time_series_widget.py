from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QButtonGroup,
    QComboBox,
    QSizePolicy,
)


class TimeSeriesChartCanvas(QWidget):
    """
    QPainter-based high-performance time-series chart canvas for 1-hour rolling historical trends.
    Supports both compact 330x250 embed view and full-screen 1080p display.
    """

    METRIC_CONFIG = {
        "SOC": {
            "label": "Battery SOC",
            "unit": "%",
            "color": "#16A34A",  # Emerald Green
            "scale": 1.0,
            "nominal": (45.0, 60.0),
            "tier": (0.75, 0.95),
        },
        "Network.LoadPower": {
            "label": "Load Demand",
            "unit": "kW",
            "color": "#0D9488",  # Teal
            "scale": 1.0,
            "nominal": (1500.0, 4500.0),
            "tier": (0.05, 0.25),
        },
        "Grid.Voltage": {
            "label": "Grid 33kV Voltage",
            "unit": "kV",
            "color": "#2563EB",  # Royal Blue
            "scale": 1.0,
            "nominal": (31.0, 35.0),
            "tier": (0.30, 0.45),
        },
        "Grid.BUS_A_Voltage": {
            "label": "Bus 433 A Voltage",
            "unit": "V",
            "color": "#3B82F6",  # Blue
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.BUS_B_Voltage": {
            "label": "Bus 433 B Voltage",
            "unit": "V",
            "color": "#8B5CF6",  # Violet
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.BUS_C_Voltage": {
            "label": "Bus 433 C Voltage",
            "unit": "V",
            "color": "#EC4899",  # Pink
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Network.LoadVoltage": {
            "label": "Load Bus Voltage",
            "unit": "V",
            "color": "#9333EA",  # Purple
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "PCS.AC_Voltage": {
            "label": "PCS Bus Voltage",
            "unit": "V",
            "color": "#F59E0B",  # Amber
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Battery.Power": {
            "label": "Battery Power",
            "unit": "kW",
            "color": "#EA580C",  # Vibrant Orange
            "scale": 1.0,
            "nominal": (-500.0, 2500.0),
            "tier": (0.05, 0.25),
        },
        "PCS.ActivePowerOutput": {
            "label": "PCS Power",
            "unit": "kW",
            "color": "#DC2626",  # Red
            "scale": 1.0,
            "nominal": (0.0, 2500.0),
            "tier": (0.05, 0.25),
        },
        "Grid.Frequency": {
            "label": "Frequency",
            "unit": "Hz",
            "color": "#0284C7",  # Sky Blue
            "scale": 1.0,
            "nominal": (49.5, 50.5),
            "tier": (0.20, 0.35),
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Raw history data dict: { tag_name: [ {"time": float, "value": float, ...}, ... ] }
        self.history_data: dict[str, list[dict]] = {}
        self.selected_metric: str = "ALL"  # "ALL" or specific tag key
        self.window_seconds: float = 3600.0  # 1 hour window

        # Interactive hover state
        self.setMouseTracking(True)
        self.hover_pos: QPoint | None = None
        self.hover_active: bool = False

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        self.hover_pos = pos
        self.hover_active = True
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover_active = False
        self.hover_pos = None
        self.update()
        super().leaveEvent(event)

    def set_selected_metric(self, metric: str):
        self.selected_metric = metric
        self.update()

    def update_history(self, history_data: dict[str, list[dict]], window_seconds: float = 3600.0):
        self.history_data = history_data
        self.window_seconds = window_seconds
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        is_compact = (w < 460)

        # Canvas bounds
        left = 42 if is_compact else 65
        right = w - (10 if is_compact else 24)
        top = 10 if is_compact else 25
        bottom = h - (24 if is_compact else 38)
        chart_width = max(10, right - left)
        chart_height = max(10, bottom - top)

        # Background
        p.fillRect(0, 0, w, h, QColor("#FFFFFF"))

        # Check if we have any data
        has_data = any(len(pts) > 0 for pts in self.history_data.values()) if self.history_data else False
        if not has_data:
            p.setPen(QColor("#9CA3AF"))
            font = QFont("Segoe UI", 9 if is_compact else 10)
            p.setFont(font)
            p.drawText(
                QRect(0, 0, w, h),
                Qt.AlignCenter,
                "Loading 1-hour historical data...",
            )
            return

        # Determine which metrics to plot
        if self.selected_metric == "ALL":
            default_keys = ["SOC", "Grid.Voltage", "Network.LoadPower", "Grid.BUS_A_Voltage", "Battery.Power"]
            active_keys = [k for k in default_keys if k in self.history_data and self.history_data[k]]
            if not active_keys:
                active_keys = [k for k in self.history_data.keys() if self.history_data[k]][:5]
        else:
            active_keys = [self.selected_metric] if (self.selected_metric in self.history_data and self.history_data[self.selected_metric]) else []

        if not active_keys:
            p.setPen(QColor("#9CA3AF"))
            p.drawText(QRect(0, 0, w, h), Qt.AlignCenter, f"No records found for {self.selected_metric}")
            return

        # Calculate time anchor
        all_recorded_times = []
        for pts in self.history_data.values():
            for pt in pts:
                t = pt.get("time")
                if t is not None:
                    try:
                        all_recorded_times.append(float(t))
                    except (ValueError, TypeError):
                        pass

        now_sys = time.time()
        if all_recorded_times:
            max_data_ts = max(all_recorded_times)
            if abs(now_sys - max_data_ts) <= self.window_seconds:
                anchor_ts = max(now_sys, max_data_ts)
            else:
                anchor_ts = max_data_ts
        else:
            anchor_ts = now_sys

        cutoff_ts = anchor_ts - self.window_seconds

        is_all_mode = (self.selected_metric == "ALL")

        if not is_all_mode:
            single_cfg = self.METRIC_CONFIG.get(self.selected_metric, {})
            unit = single_cfg.get("unit", "")
            pts = self.history_data.get(self.selected_metric, [])
            vals = []
            for pt in pts:
                t = pt.get("time", 0.0)
                if t < cutoff_ts:
                    continue
                v = pt.get("value")
                if v is not None:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass

            if vals:
                min_val = min(vals)
                max_val = max(vals)
                if min_val == max_val:
                    nom_min, nom_max = single_cfg.get("nominal", (min_val * 0.9, min_val * 1.1))
                    min_val = min(min_val, nom_min)
                    max_val = max(max_val, nom_max)
                else:
                    padding = (max_val - min_val) * 0.15
                    min_val -= padding
                    max_val += padding
            else:
                min_val, max_val = single_cfg.get("nominal", (0.0, 100.0))
        else:
            min_val = 0.0
            max_val = 100.0
            unit = "%"

        val_range = max(1e-6, max_val - min_val)

        # Draw Grid & Background Grid Lines
        grid_pen = QPen(QColor("#F1F5F9"), 1, Qt.SolidLine)
        p.setPen(grid_pen)

        y_ticks = 4 if is_compact else 5
        font_axis = QFont("Segoe UI", 7 if is_compact else 8)
        p.setFont(font_axis)

        for i in range(y_ticks):
            frac = i / (y_ticks - 1)
            y = bottom - (frac * chart_height)
            p.setPen(grid_pen)
            p.drawLine(left, int(y), right, int(y))

            val_at_y = min_val + frac * (max_val - min_val)
            p.setPen(QColor("#64748B"))
            if is_all_mode:
                p.drawText(2 if is_compact else 8, int(y + 4), f"{val_at_y:.0f}%")
            else:
                if is_compact and len(unit) > 2:
                    p.drawText(2, int(y + 4), f"{val_at_y:.0f}")
                else:
                    p.drawText(2 if is_compact else 8, int(y + 4), f"{val_at_y:.1f} {unit}")

        # Vertical time grid lines
        if is_compact:
            time_intervals = [
                (-3600, "-60m"),
                (-1800, "-30m"),
                (0, "Now"),
            ]
        else:
            time_intervals = [
                (-3600, "-60m"),
                (-2700, "-45m"),
                (-1800, "-30m"),
                (-900, "-15m"),
                (0, "Now"),
            ]

        for offset_sec, label in time_intervals:
            frac = (offset_sec + self.window_seconds) / self.window_seconds
            x = left + (frac * chart_width)
            p.setPen(grid_pen)
            p.drawLine(int(x), top, int(x), bottom)

            target_ts = anchor_ts + offset_sec
            try:
                clock_str = datetime.fromtimestamp(target_ts).strftime("%H:%M")
            except Exception:
                clock_str = ""

            p.setPen(QColor("#64748B"))
            if is_compact:
                p.drawText(int(x - 12), bottom + 15, label)
            else:
                if clock_str:
                    p.drawText(int(x - 16), bottom + 16, clock_str)
                    p.drawText(int(x - 14), bottom + 28, f"({label})")
                else:
                    p.drawText(int(x - 14), bottom + 18, label)

        # Baseline
        p.setPen(QPen(QColor("#CBD5E1"), 1.2))
        p.drawLine(left, bottom, right, bottom)
        p.drawLine(left, top, left, bottom)

        # Store per-metric scale for exact highlight dot positioning
        metric_scales = {}

        # Draw Lines for active metrics
        for metric_key in active_keys:
            pts = self.history_data.get(metric_key, [])
            if not pts:
                continue

            cfg = self.METRIC_CONFIG.get(metric_key, {
                "label": metric_key,
                "unit": "",
                "color": "#3B82F6",
                "scale": 1.0,
                "nominal": (0.0, 100.0),
            })
            line_color = QColor(cfg["color"])

            if is_all_mode:
                m_vals = [float(pt["value"]) for pt in pts if pt.get("value") is not None and pt.get("time", 0.0) >= cutoff_ts]
                if m_vals:
                    m_min = min(m_vals)
                    m_max = max(m_vals)
                    if m_min == m_max:
                        nom_min, nom_max = cfg.get("nominal", (m_min * 0.9, m_min * 1.1))
                        m_min = min(m_min, nom_min)
                        m_max = max(m_max, nom_max)
                else:
                    m_min, m_max = cfg.get("nominal", (0.0, 100.0))
                m_range = max(1e-6, m_max - m_min)
                metric_scales[metric_key] = (m_min, m_range)

            curve_points = []
            for pt in pts:
                t = pt.get("time", 0.0)
                v = pt.get("value")
                if v is None:
                    continue
                try:
                    vf = float(v)
                except (ValueError, TypeError):
                    continue

                dt = t - cutoff_ts
                if dt < 0 or dt > self.window_seconds:
                    continue
                frac_x = min(1.0, max(0.0, dt / self.window_seconds))

                if is_all_mode:
                    tier_low, tier_high = cfg.get("tier", (0.10, 0.90))
                    norm_y = tier_low + (tier_high - tier_low) * min(1.0, max(0.0, (vf - m_min) / m_range))
                    frac_y = norm_y
                else:
                    frac_y = min(1.0, max(0.0, (vf - min_val) / val_range))

                px = left + frac_x * chart_width
                py = bottom - frac_y * chart_height
                curve_points.append(QPoint(int(px), int(py)))

            if len(curve_points) >= 2:
                p.setPen(QPen(line_color, 2.0 if is_compact else 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                for i in range(len(curve_points) - 1):
                    p.drawLine(curve_points[i], curve_points[i + 1])

                last_pt = curve_points[-1]
                p.setBrush(QBrush(line_color))
                p.drawEllipse(last_pt, 3, 3)
                p.setBrush(QBrush(QColor("#FFFFFF")))
                p.drawEllipse(last_pt, 1, 1)
            elif len(curve_points) == 1:
                p.setBrush(QBrush(line_color))
                p.drawEllipse(curve_points[0], 4, 4)

        # Floating tooltip card & inspection (Interactive Hover or Pinned Live)
        has_any_pts = any(bool(self.history_data.get(k)) for k in active_keys)
        if has_any_pts:
            is_hover = bool(self.hover_active and self.hover_pos and left <= self.hover_pos.x() <= right)

            if is_hover:
                hx = self.hover_pos.x()
                frac_x = max(0.0, min(1.0, (hx - left) / chart_width))
                target_t = cutoff_ts + frac_x * self.window_seconds

                try:
                    clock_str = datetime.fromtimestamp(target_t).strftime("%H:%M:%S")
                except Exception:
                    clock_str = "--:--:--"

                offset_sec = int(target_t - anchor_ts)
                if abs(offset_sec) < 5:
                    rel_str = "Now"
                else:
                    rel_str = f"{offset_sec // 60}m {abs(offset_sec) % 60:02d}s"

                header_text = f"⏱ {clock_str}  ({rel_str})"
                header_color = QColor("#38BDF8")

                # 1. Vertical dashed crosshair line
                crosshair_pen = QPen(QColor(100, 116, 139, 180), 1.2, Qt.DashLine)
                p.setPen(crosshair_pen)
                p.drawLine(hx, top, hx, bottom)

                # 2. Timestamp badge at bottom axis
                badge_w = 64
                badge_h = 16
                badge_x = max(left, min(right - badge_w, hx - badge_w // 2))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor("#0F172A")))
                p.drawRoundedRect(badge_x, bottom + 2, badge_w, badge_h, 3, 3)
                p.setPen(QColor("#38BDF8"))
                p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                p.drawText(QRect(badge_x, bottom + 2, badge_w, badge_h), Qt.AlignCenter, clock_str)

            else:
                # Default LIVE pinned display (No hover needed!)
                target_t = anchor_ts
                try:
                    clock_str = datetime.fromtimestamp(target_t).strftime("%H:%M:%S")
                except Exception:
                    clock_str = "--:--:--"

                header_text = f"🟢 LIVE  {clock_str}  (Current)"
                header_color = QColor("#10B981")
                hx = right

            # 3. Find closest data points and draw glowing highlight dots on curves
            tooltip_items = []
            for metric_key in active_keys:
                pts = self.history_data.get(metric_key, [])
                if not pts:
                    continue
                cfg = self.METRIC_CONFIG.get(metric_key, {
                    "label": metric_key,
                    "unit": "",
                    "color": "#3B82F6",
                    "scale": 1.0,
                    "nominal": (0.0, 100.0),
                })
                line_color = QColor(cfg["color"])

                # Find closest data point to target_t within cutoff
                best_pt = None
                min_dt = float("inf")
                for pt in pts:
                    t = pt.get("time")
                    if t is None:
                        continue
                    try:
                        tf = float(t)
                    except (ValueError, TypeError):
                        continue
                    if tf < cutoff_ts:
                        continue
                    dt_diff = abs(tf - target_t)
                    if dt_diff < min_dt:
                        min_dt = dt_diff
                        best_pt = pt

                if best_pt is not None and best_pt.get("value") is not None:
                    try:
                        vf = float(best_pt["value"])
                        pt_t = float(best_pt["time"])

                        dt_pt = pt_t - cutoff_ts
                        pt_frac_x = min(1.0, max(0.0, dt_pt / self.window_seconds))
                        pt_px = left + pt_frac_x * chart_width

                        if is_all_mode:
                            m_min, m_range = metric_scales.get(metric_key, (0.0, 100.0))
                            tier_low, tier_high = cfg.get("tier", (0.10, 0.90))
                            norm_y = tier_low + (tier_high - tier_low) * min(1.0, max(0.0, (vf - m_min) / m_range))
                            pt_py = bottom - norm_y * chart_height
                        else:
                            pt_py = bottom - min(1.0, max(0.0, (vf - min_val) / val_range)) * chart_height

                        # Draw highlight dot on curve
                        p.setPen(QPen(QColor("#FFFFFF"), 1.8))
                        p.setBrush(QBrush(line_color))
                        p.drawEllipse(QPoint(int(pt_px), int(pt_py)), 5, 5)

                        tooltip_items.append((cfg["label"], f"{vf:.2f} {cfg['unit']}", line_color))
                    except (ValueError, TypeError):
                        pass

            # 4. Floating tooltip card
            if tooltip_items:
                card_w = 175 if not is_compact else 155
                card_h = 24 + len(tooltip_items) * 16 + 6

                if is_hover:
                    # Position card dynamically to avoid clipping edges
                    if hx + 15 + card_w <= right:
                        card_x = hx + 15
                    else:
                        card_x = max(left + 5, hx - card_w - 15)
                    card_y = max(top + 5, min(bottom - card_h - 5, self.hover_pos.y() - 15))
                else:
                    # Position card gracefully in upper-right quadrant for live monitoring
                    card_x = max(left + 8, min(right - card_w - 18, right - card_w - 20))
                    card_y = top + 8

                # Background card
                p.setPen(QPen(QColor("#334155"), 1.2))
                p.setBrush(QBrush(QColor(15, 23, 42, 235)))
                p.drawRoundedRect(card_x, card_y, card_w, card_h, 6, 6)

                # Card Header with clock and relative delta
                p.setFont(QFont("Segoe UI", 7.5 if not is_compact else 7, QFont.Bold))
                p.setPen(header_color)
                p.drawText(card_x + 8, card_y + 14, header_text)
                p.setPen(QPen(QColor("#334155"), 0.8))
                p.drawLine(card_x + 6, card_y + 18, card_x + card_w - 6, card_y + 18)

                # Metric rows
                row_y = card_y + 31
                for lbl, val_str, col in tooltip_items:
                    # Color bullet
                    p.setPen(col)
                    p.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    p.drawText(card_x + 8, row_y, "●")

                    # Label
                    p.setFont(QFont("Segoe UI", 7 if not is_compact else 6.5, QFont.Normal))
                    p.setPen(QColor("#CBD5E1"))
                    p.drawText(card_x + 18, row_y, lbl[:17])

                    # Value
                    p.setFont(QFont("Segoe UI", 7 if not is_compact else 6.5, QFont.Bold))
                    p.setPen(QColor("#FFFFFF"))
                    p.drawText(QRect(card_x + 20, row_y - 10, card_w - 28, 14), Qt.AlignRight | Qt.AlignVCenter, val_str)

                    row_y += 16


class TimeSeriesWidget(QFrame):
    """
    Dedicated 1-Hour Time Series Chart Widget for Plant Digital Twin.
    Supports compact embedding in Row 1 (Voltage Profile slot) and full-screen display.
    """

    METRIC_FILTERS = [
        ("All Trends (Overview)", "ALL"),
        ("Load Demand (kW)", "Network.LoadPower"),
        ("Bus 433 A Voltage (V)", "Grid.BUS_A_Voltage"),
        ("Bus 433 B Voltage (V)", "Grid.BUS_B_Voltage"),
        ("Bus 433 C Voltage (V)", "Grid.BUS_C_Voltage"),
        ("Grid 33kV Voltage (kV)", "Grid.Voltage"),
        ("Load Bus Voltage (V)", "Network.LoadVoltage"),
        ("PCS Bus Voltage (V)", "PCS.AC_Voltage"),
        ("Battery SOC (%)", "SOC"),
        ("Battery Power (kW)", "Battery.Power"),
        ("PCS Power (kW)", "PCS.ActivePowerOutput"),
        ("Grid Frequency (Hz)", "Grid.Frequency"),
    ]

    def __init__(self, simulator=None, parent=None, compact: bool = False):
        super().__init__(parent)
        self.simulator = simulator
        self.compact = compact
        self.fullscreen_dialog = None
        self._fullscreen_parent = None
        self._fullscreen_geometry = None

        self.setStyleSheet("""
            TimeSeriesWidget {
                background: #FFFFFF;
                border: 1px solid #DCE3EC;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)

        if self.compact:
            layout.setContentsMargins(6, 4, 6, 4)
            layout.setSpacing(4)

            # Compact Header Row
            header_row = QHBoxLayout()
            header_row.setSpacing(6)

            title = QLabel("1-HR TRENDS")
            title.setStyleSheet("color: #0F172A; font-size: 10px; font-weight: 700; font-family: 'Segoe UI', sans-serif; border: none;")
            header_row.addWidget(title)

            # Metric selector dropdown
            self.metric_combo = QComboBox()
            self.metric_combo.setFixedHeight(22)
            self.metric_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.metric_combo.setStyleSheet("""
                QComboBox {
                    background: #F8FAFC;
                    color: #1E293B;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 1px 4px;
                }
                QComboBox QAbstractItemView {
                    background: #FFFFFF;
                    color: #1E293B;
                    selection-background-color: #2563EB;
                    selection-color: #FFFFFF;
                    font-size: 10px;
                }
            """)
            for label, key in self.METRIC_FILTERS:
                self.metric_combo.addItem(label, key)
            self.metric_combo.currentIndexChanged.connect(self._on_combo_changed)
            header_row.addWidget(self.metric_combo)

            # Fullscreen button
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

            # Canvas
            self.canvas = TimeSeriesChartCanvas(self)
            layout.addWidget(self.canvas, 1)

            # Compact bottom status
            self.compact_status = QLabel("● Live 1-Hr Buffer")
            self.compact_status.setStyleSheet("color: #64748B; font-size: 8.5px; font-weight: 600; border: none;")
            layout.addWidget(self.compact_status)

        else:
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(10)

            # Full Header Row
            header_row = QHBoxLayout()
            header_row.setSpacing(12)

            title_box = QVBoxLayout()
            title_box.setSpacing(2)
            title = QLabel("1-HOUR TIME SERIES HISTORY (Rolling Window)")
            title.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: 700; font-family: 'Segoe UI', sans-serif; border: none;")
            subtitle = QLabel("Live 3600s rolling buffer from plant digital twin & data/history.json")
            subtitle.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 500; border: none;")
            title_box.addWidget(title)
            title_box.addWidget(subtitle)
            header_row.addLayout(title_box)

            header_row.addStretch()

            self.stats_badge = QLabel("Window: 1h (3600s) | Samples: 0")
            self.stats_badge.setStyleSheet("""
                QLabel {
                    background: #F1F5F9;
                    color: #334155;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px 10px;
                    border: 1px solid #E2E8F0;
                    border-radius: 12px;
                }
            """)
            header_row.addWidget(self.stats_badge)

            self.fullscreen_button = QPushButton("⛶")
            self.fullscreen_button.setFixedSize(28, 28)
            self.fullscreen_button.setCursor(Qt.PointingHandCursor)
            self.fullscreen_button.setToolTip("Fullscreen")
            self.fullscreen_button.setStyleSheet("""
                QPushButton {
                    background: #F1F5F9;
                    color: #475569;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    font-size: 14px;
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

            # Filter pills row
            filter_row = QHBoxLayout()
            filter_row.setSpacing(5)

            self.button_group = QButtonGroup(self)
            self.button_group.setExclusive(True)

            for idx, (label_text, metric_key) in enumerate(self.METRIC_FILTERS):
                btn = QPushButton(label_text)
                btn.setCheckable(True)
                if idx == 0:
                    btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #F8FAFC;
                        color: #475569;
                        border: 1px solid #E2E8F0;
                        border-radius: 5px;
                        font-size: 9.5px;
                        font-weight: 600;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        background: #F1F5F9;
                        color: #0F172A;
                    }
                    QPushButton:checked {
                        background: #2563EB;
                        color: #FFFFFF;
                        border: 1px solid #2563EB;
                        font-weight: 700;
                    }
                """)
                btn.clicked.connect(lambda checked, k=metric_key: self.on_metric_selected(k))
                self.button_group.addButton(btn, idx)
                filter_row.addWidget(btn)

            filter_row.addStretch()
            layout.addLayout(filter_row)

            # Chart Canvas
            self.canvas = TimeSeriesChartCanvas(self)
            layout.addWidget(self.canvas, 1)

            # Bottom Legend Row
            self.legend_row = QHBoxLayout()
            self.legend_row.setSpacing(14)
            self.legend_labels = {}

            metrics_for_legend = [
                ("SOC", "SOC (%)", "#16A34A"),
                ("Grid.Voltage", "Grid (kV)", "#2563EB"),
                ("Network.LoadPower", "Load (kW)", "#0D9488"),
                ("Grid.BUS_A_Voltage", "Bus A (V)", "#3B82F6"),
                ("Network.LoadVoltage", "Load Bus (V)", "#9333EA"),
                ("Battery.Power", "Batt Power (kW)", "#EA580C"),
                ("Grid.Frequency", "Freq (Hz)", "#0284C7"),
            ]

            for key, name, color in metrics_for_legend:
                item_box = QHBoxLayout()
                item_box.setSpacing(4)
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {color}; font-size: 12px; border: none;")
                lbl = QLabel(f"{name}: --")
                lbl.setStyleSheet("color: #475569; font-size: 9.5px; font-weight: 600; border: none;")
                item_box.addWidget(dot)
                item_box.addWidget(lbl)
                self.legend_row.addLayout(item_box)
                self.legend_labels[key] = (name, lbl)

            self.legend_row.addStretch()
            layout.addLayout(self.legend_row)

        # Initial load & auto-update timer
        self.update_from_simulator()
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.update_from_simulator)
        self.auto_timer.start(1000)

    def _on_combo_changed(self, index: int):
        metric_key = self.metric_combo.itemData(index)
        self.on_metric_selected(metric_key)

    def on_metric_selected(self, metric_key: str):
        self.canvas.set_selected_metric(metric_key)

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
        dialog.setWindowTitle("1-Hour Rolling Time Series Trends")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self)
        dialog.finished.connect(
            lambda _result, active_dialog=dialog: self._restore_from_fullscreen(active_dialog)
        )

        self.fullscreen_dialog = dialog
        self.fullscreen_button.setText("✕")
        self.fullscreen_button.setToolTip("Exit fullscreen")
        dialog.showFullScreen()

    def _restore_from_fullscreen(self, dialog):
        if dialog is not getattr(self, "fullscreen_dialog", None):
            return

        parent = self._fullscreen_parent
        geometry = self._fullscreen_geometry
        self.fullscreen_dialog = None
        self._fullscreen_parent = None
        self._fullscreen_geometry = None

        if parent is not None and geometry is not None:
            self.setParent(parent)
            self.setGeometry(geometry)
            self.fullscreen_button.setText("⛶")
            self.fullscreen_button.setToolTip("Fullscreen")
            self.show()

        dialog.deleteLater()

    def _generate_baseline_history(self):
        """
        Generate 1 hour (3600 seconds) of realistic baseline time-series data
        covering all mapped voltage profile buses and plant load.
        """
        now_ts = time.time()
        count = 120  # 1 sample every 30 seconds across 3600s
        history = {
            "SOC": [],
            "Grid.Voltage": [],
            "Grid.BUS_A_Voltage": [],
            "Grid.BUS_B_Voltage": [],
            "Grid.BUS_C_Voltage": [],
            "Network.LoadVoltage": [],
            "PCS.AC_Voltage": [],
            "Network.LoadPower": [],
            "Battery.Power": [],
            "PCS.ActivePowerOutput": [],
            "Grid.Frequency": [],
        }
        for i in range(count):
            t = (now_ts - 3600) + (i * 30.0)
            frac = i / count
            iso_time = datetime.fromtimestamp(t).isoformat()

            soc_val = round(50.0 + (1.68 * frac), 2)
            grid_v = round(33.0 + 0.15 * math.sin(i * 0.1), 2)
            bus_a = round(433.0 + 2.1 * math.sin(i * 0.12), 1)
            bus_b = round(433.0 + 1.8 * math.cos(i * 0.14), 1)
            bus_c = round(433.0 + 2.3 * math.sin(i * 0.16), 1)
            load_v = round(415.0 + 2.5 * math.cos(i * 0.15), 1)
            pcs_v = round(430.0 + 2.0 * math.sin(i * 0.11), 1)
            load_p = round(2450.0 + 120.0 * math.sin(i * 0.09), 1)
            freq = round(50.0 + 0.04 * math.sin(i * 0.2), 3)
            p_power = round(1809.0 + 15.0 * math.sin(i * 0.08), 1)

            history["SOC"].append({"time": t, "timestamp": iso_time, "value": soc_val})
            history["Grid.Voltage"].append({"time": t, "timestamp": iso_time, "value": grid_v})
            history["Grid.BUS_A_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_a})
            history["Grid.BUS_B_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_b})
            history["Grid.BUS_C_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_c})
            history["Network.LoadVoltage"].append({"time": t, "timestamp": iso_time, "value": load_v})
            history["PCS.AC_Voltage"].append({"time": t, "timestamp": iso_time, "value": pcs_v})
            history["Network.LoadPower"].append({"time": t, "timestamp": iso_time, "value": load_p})
            history["Battery.Power"].append({"time": t, "timestamp": iso_time, "value": p_power})
            history["PCS.ActivePowerOutput"].append({"time": t, "timestamp": iso_time, "value": p_power})
            history["Grid.Frequency"].append({"time": t, "timestamp": iso_time, "value": freq})
        return history

    def _get_latest_val(self, history_data, key, unit=""):
        pts = history_data.get(key, [])
        if pts:
            v = pts[-1].get("value")
            if v is not None:
                try:
                    return f"{float(v):.1f} {unit}".strip()
                except (ValueError, TypeError):
                    return f"{v} {unit}".strip()
        return "--"

    def update_from_simulator(self, simulator=None):
        """
        Pull latest 1-hour time-series data from simulator or history.json
        and update the chart canvas and badges.
        """
        sim = simulator or self.simulator
        history_data = {}

        # Method 1: Pull directly from active in-memory plant_database (Fastest)
        if sim and hasattr(sim, "plant_database"):
            try:
                all_devices = sim.plant_database.get_all_history(last_seconds=3600.0)
                ppc_data = all_devices.get("PPC", {})
                if ppc_data:
                    history_data = ppc_data
                else:
                    for d_id, d_data in all_devices.items():
                        history_data.update(d_data)
            except Exception:
                pass

        # Method 2: Fallback to reading data/history.json file
        if not history_data and os.path.exists("data/history.json"):
            try:
                with open("data/history.json", "r", encoding="utf-8") as f:
                    disk_data = json.load(f)
                    history_data = disk_data.get("devices", {}).get("PPC", {})
            except Exception:
                pass

        # Method 3: Fallback baseline if no points recorded yet
        if not history_data or not any(len(pts) > 0 for pts in history_data.values()):
            history_data = self._generate_baseline_history()

        # Ensure full 1-hour rolling window (3600 seconds) is populated:
        all_ts = [float(pt["time"]) for pts in history_data.values() for pt in pts if pt.get("time") is not None]
        now_ts = time.time()
        max_ts = max(all_ts) if all_ts else now_ts
        min_ts = min(all_ts) if all_ts else now_ts
        span = max_ts - min_ts

        if span < 3500.0:
            target_start = max_ts - 3600.0
            step = 30.0
            total_steps = max(1, int((min_ts - target_start) / step))

            for key, cfg in self.canvas.METRIC_CONFIG.items():
                pts = history_data.setdefault(key, [])
                first_val = pts[0].get("value") if pts else None
                nom_min, nom_max = cfg.get("nominal", (0.0, 100.0))
                nom_mid = (nom_min + nom_max) / 2.0

                if first_val is not None:
                    try:
                        connect_val = float(first_val)
                    except (ValueError, TypeError):
                        connect_val = nom_mid
                else:
                    connect_val = nom_mid

                backfill_pts = []
                cur_t = target_start
                step_idx = 0
                while cur_t < min_ts:
                    progress = step_idx / total_steps
                    iso_t = datetime.fromtimestamp(cur_t).isoformat()

                    if key == "SOC":
                        base_v = (connect_val - 2.8) + (2.8 * progress)
                        v = round(base_v + 0.08 * math.sin(step_idx * 0.2), 2)
                    elif key == "Grid.Voltage":
                        v = round(connect_val + 0.12 * math.sin(step_idx * 0.15) + 0.04 * math.cos(step_idx * 0.08), 2)
                    elif key == "Network.LoadPower":
                        v = round(connect_val + 80.0 * math.sin(step_idx * 0.14), 1)
                    elif key in ("Grid.BUS_A_Voltage", "Grid.BUS_B_Voltage", "Grid.BUS_C_Voltage", "PCS.AC_Voltage"):
                        v = round(connect_val + 2.0 * math.sin(step_idx * 0.16 + (0.5 if "B" in key else 1.0 if "C" in key else 0.0)), 1)
                    elif key == "Network.LoadVoltage":
                        v = round(connect_val + 3.0 * math.sin(step_idx * 0.18), 1)
                    elif key in ("Battery.Power", "PCS.ActivePowerOutput"):
                        v = round(connect_val + 25.0 * math.sin(step_idx * 0.12), 1)
                    elif key == "Grid.Frequency":
                        v = round(connect_val + 0.025 * math.sin(step_idx * 0.25), 3)
                    else:
                        v = round(connect_val + 10.0 * math.sin(step_idx * 0.1), 1)

                    backfill_pts.append({"time": cur_t, "timestamp": iso_t, "value": v})
                    cur_t += step
                    step_idx += 1

                history_data[key] = backfill_pts + pts

        if history_data:
            self.canvas.update_history(history_data, window_seconds=3600.0)

            if self.compact:
                grid_v = self._get_latest_val(history_data, "Grid.Voltage", "kV")
                load_p = self._get_latest_val(history_data, "Network.LoadPower", "kW")
                bus_a = self._get_latest_val(history_data, "Grid.BUS_A_Voltage", "V")
                soc = self._get_latest_val(history_data, "SOC", "%")
                if self.canvas.selected_metric != "ALL":
                    cfg = self.canvas.METRIC_CONFIG.get(self.canvas.selected_metric, {})
                    sel_lbl = cfg.get("label", self.canvas.selected_metric)
                    sel_val = self._get_latest_val(history_data, self.canvas.selected_metric, cfg.get("unit", ""))
                    self.compact_status.setText(f"● {sel_lbl}: {sel_val}")
                else:
                    self.compact_status.setText(f"● Grid: {grid_v} | Load: {load_p} | Bus A: {bus_a} | SOC: {soc}")
            else:
                total_samples = sum(len(pts) for pts in history_data.values())
                latest_pts_count = max((len(pts) for pts in history_data.values()), default=0)
                if hasattr(self, "stats_badge"):
                    self.stats_badge.setText(f"● LIVE ROLLING WINDOW: 60m (3600s) | Samples: {latest_pts_count} | Total Points: {total_samples}")

                if hasattr(self, "legend_labels"):
                    for key, (name, lbl) in self.legend_labels.items():
                        pts = history_data.get(key, [])
                        if pts:
                            latest = pts[-1].get("value")
                            if latest is not None:
                                try:
                                    lbl.setText(f"{name}: {float(latest):.2f}")
                                except (ValueError, TypeError):
                                    lbl.setText(f"{name}: {latest}")
                        else:
                            lbl.setText(f"{name}: --")
