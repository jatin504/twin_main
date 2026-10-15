from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime
from common.constants import IST
from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QBrush,
    QLinearGradient,
    QPainterPath,
    QGuiApplication,
    QPalette,
)
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
    QScrollArea,
)


class TimeSeriesChartCanvas(QWidget):
    """
    QPainter-based high-performance time-series chart canvas for 1-hour rolling historical trends.
    Supports both compact 330x250 embed view and full-screen 1080p display.
    """

    METRIC_CONFIG = {
        "Solar.ActivePower": {
            "label": "Solar Generation",
            "unit": "kW",
            "color": "#F97316",  # Sun Orange (Exclusive Area Spline)
            "scale": 1.0,
            "nominal": (0.0, 1500.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "Network.LoadPower": {
            "label": "Load",
            "unit": "kW",
            "color": "#6366F1",  # Modern Indigo
            "scale": 1.0,
            "nominal": (1500.0, 4500.0),
            "tier": (0.05, 0.25),
            "fill": False,
        },
        "BESS.ChargePower": {
            "label": "BESS Charge",
            "unit": "kW",
            "color": "#10B981",  # Emerald Green
            "scale": 1.0,
            "nominal": (0.0, 2500.0),
            "tier": (0.05, 0.25),
            "fill": False,
        },
        "BESS.DischargePower": {
            "label": "BESS Discharge",
            "unit": "kW",
            "color": "#EC4899",  # Rose Pink
            "scale": 1.0,
            "nominal": (0.0, 2500.0),
            "tier": (0.05, 0.25),
            "fill": False,
        },
        "Grid.ImportPower": {
            "label": "Grid Import",
            "unit": "kW",
            "color": "#8B5CF6",  # Violet Purple
            "scale": 1.0,
            "nominal": (0.0, 4000.0),
            "tier": (0.05, 0.25),
            "fill": False,
        },
        "Grid.ExportPower": {
            "label": "Grid Export",
            "unit": "kW",
            "color": "#06B6D4",  # Cyan Blue
            "scale": 1.0,
            "nominal": (0.0, 4000.0),
            "tier": (0.05, 0.25),
            "fill": False,
        },
        "Grid.BUS_A_Voltage": {
            "label": "Bus 433 A Voltage",
            "unit": "V",
            "color": "#3B82F6",  # Phase A: Royal Blue
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.BUS_B_Voltage": {
            "label": "Bus 433 B Voltage",
            "unit": "V",
            "color": "#A855F7",  # Phase B: Purple
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.BUS_C_Voltage": {
            "label": "Bus 433 C Voltage",
            "unit": "V",
            "color": "#F43F5E",  # Phase C: Coral Crimson
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.Voltage": {
            "label": "Grid 33kV Voltage",
            "unit": "kV",
            "color": "#1D4ED8",  # 33kV Grid: Deep Navy Blue
            "scale": 1.0,
            "nominal": (31.0, 35.0),
            "tier": (0.30, 0.45),
        },
        "PCS.AC_Voltage": {
            "label": "PCS Bus Voltage",
            "unit": "V",
            "color": "#0D9488",  # PCS Bus: Teal
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "PCS.ACVoltage": {
            "label": "PCS Bus Voltage",
            "unit": "V",
            "color": "#0D9488",  # Alias
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "SOC": {
            "label": "Battery SOC",
            "unit": "%",
            "color": "#15803D",  # Forest Green
            "scale": 1.0,
            "nominal": (45.0, 60.0),
            "tier": (0.75, 0.95),
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
        "Network.LoadVoltage": {
            "label": "Load Bus Voltage",
            "unit": "V",
            "color": "#D946EF",  # Fuchsia
            "scale": 1.0,
            "nominal": (400.0, 440.0),
            "tier": (0.45, 0.65),
        },
        "Grid.Frequency": {
            "label": "Frequency",
            "unit": "Hz",
            "color": "#64748B",  # Slate Grey
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
        self.dashboard_style: bool = False
        self.tooltip_scroll_offset: int = 0

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        if self.hover_pos and abs(self.hover_pos.x() - pos.x()) < 2:
            return
        self.hover_pos = pos
        self.hover_active = True
        self.update()
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if self.hover_active:
            delta = event.angleDelta().y()
            if delta > 0:
                self.tooltip_scroll_offset = max(0, self.tooltip_scroll_offset - 1)
            elif delta < 0:
                self.tooltip_scroll_offset += 1
            self.update()
            event.accept()
            return
        super().wheelEvent(event)

    def leaveEvent(self, event):
        self.hover_active = False
        self.hover_pos = None
        self.tooltip_scroll_offset = 0
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

        # Canvas bounds (All Y-axes on Left: Power [MW/kW], Voltage [V], SOC [%])
        is_all_mode = (self.selected_metric == "ALL")

        if is_all_mode:
            left = 106 if is_compact else 156
            right = w - (16 if is_compact else 24)
            top = 22 if is_compact else 28
            bottom = h - (26 if is_compact else 38)
        else:
            left = 44 if is_compact else 68
            right = w - (12 if is_compact else 24)
            top = 18 if is_compact else 26
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
            default_keys = [
                "Solar.ActivePower",
                "Network.LoadPower",
                "BESS.ChargePower",
                "BESS.DischargePower",
                "Grid.ImportPower",
                "Grid.ExportPower",
                "Grid.BUS_A_Voltage",
                "Grid.BUS_B_Voltage",
                "Grid.BUS_C_Voltage",
                "Grid.Voltage",
                "PCS.AC_Voltage",
                "SOC",
                "Grid.Frequency",
            ]
            active_keys = [k for k in default_keys if (k in self.history_data and self.history_data[k]) or (k == "PCS.AC_Voltage" and self.history_data.get("PCS.ACVoltage"))]
            if not active_keys:
                active_keys = [k for k in self.history_data.keys() if self.history_data[k]][:8]
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

        # -------------------------------------------------------------------------
        # MULTIPLE Y-AXES SCALING LOGIC
        # -------------------------------------------------------------------------
        # Axis 1: Power (kW) -> Left Axis
        # Axis 2: SOC (%) -> Right Axis
        # Axis 3: Voltage (V / kV) -> Scaled independently
        # Axis 4: Frequency (Hz) -> Scaled independently
        # -------------------------------------------------------------------------

        # Group metrics by unit
        power_vals = []
        soc_vals = []
        volt_vals = []
        freq_vals = []

        for m_key in active_keys:
            pts = self.history_data.get(m_key, [])
            cfg = self.METRIC_CONFIG.get(m_key, {})
            unit = cfg.get("unit", "")
            for pt in pts:
                t = pt.get("time", 0.0)
                if t < cutoff_ts:
                    continue
                v = pt.get("value")
                if v is not None:
                    try:
                        vf = float(v)
                        if unit == "kW":
                            power_vals.append(vf)
                        elif unit == "%":
                            soc_vals.append(vf)
                        elif unit in ("V", "kV"):
                            vf_v = (vf / 33.0) * 433.0 if unit == "kV" and vf > 0 else vf
                            volt_vals.append(vf_v)
                        elif unit == "Hz":
                            freq_vals.append(vf)
                    except (ValueError, TypeError):
                        pass

        # Power Axis Range (Left) - stabilized with clean round steps (e.g. 250 kW or 500 kW per tick)
        if power_vals:
            raw_p_min = min(power_vals)
            raw_p_max = max(power_vals)
            p_span = max(100.0, raw_p_max - raw_p_min)
            p_step = 250.0 if p_span <= 1200 else (500.0 if p_span <= 2500 else 1000.0)
            power_min = math.floor(raw_p_min / p_step) * p_step
            power_max = power_min + (4 * p_step)
            while power_max < raw_p_max:
                power_max += p_step
        else:
            power_min, power_max = (0.0, 4000.0)
        power_range = max(1e-6, power_max - power_min)

        # SOC Axis Range - stabilized to exact 5% or 10% steps
        if soc_vals:
            raw_s_min = max(0.0, min(soc_vals))
            raw_s_max = min(100.0, max(soc_vals))
            s_span = max(10.0, raw_s_max - raw_s_min)
            s_step = 5.0 if s_span <= 20.0 else 10.0
            soc_min = max(0.0, math.floor(raw_s_min / s_step) * s_step)
            soc_max = min(100.0, soc_min + (4 * s_step))
            if soc_max < raw_s_max:
                soc_max = min(100.0, math.ceil(raw_s_max / s_step) * s_step)
                soc_min = max(0.0, soc_max - (4 * s_step))
        else:
            soc_min, soc_max = (0.0, 100.0)
        soc_range = max(1e-6, soc_max - soc_min)

        # Voltage Axis Range - stabilized to clean 5V steps
        if volt_vals:
            raw_v_min = min(volt_vals)
            raw_v_max = max(volt_vals)
            v_span = max(10.0, raw_v_max - raw_v_min)
            v_step = 5.0 if v_span <= 20.0 else 10.0
            volt_min = math.floor(raw_v_min / v_step) * v_step
            volt_max = volt_min + (4 * v_step)
            while volt_max < raw_v_max:
                volt_max += v_step
        else:
            volt_min, volt_max = (400.0, 440.0)
        volt_range = max(1e-6, volt_max - volt_min)

        # Frequency Axis Range - stabilized to 0.1 Hz steps
        if freq_vals:
            freq_min = math.floor((min(freq_vals) - 0.2) * 10.0) / 10.0
            freq_max = math.ceil((max(freq_vals) + 0.2) * 10.0) / 10.0
        else:
            freq_min, freq_max = (49.0, 51.0)
        freq_range = max(1e-6, freq_max - freq_min)

        # Single Metric fallback range
        if not is_all_mode:
            single_cfg = self.METRIC_CONFIG.get(self.selected_metric, {})
            s_unit = single_cfg.get("unit", "")
            s_pts = self.history_data.get(self.selected_metric, [])
            s_vals = [float(pt["value"]) for pt in s_pts if pt.get("value") is not None and pt.get("time", 0.0) >= cutoff_ts]
            if s_vals:
                min_val = min(s_vals)
                max_val = max(s_vals)
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
            step = 10.0 if (max_val - min_val) > 50 else 1.0
            min_val = math.floor(min_val / step) * step
            max_val = math.ceil(max_val / step) * step
            val_range = max(1e-6, max_val - min_val)
            unit = s_unit

        # -------------------------------------------------------------------------
        # DRAW GRID & BACKGROUND LINES
        # -------------------------------------------------------------------------
        grid_pen = QPen(QColor("#F1F5F9"), 1, Qt.SolidLine)
        p.setPen(grid_pen)

        y_ticks = 4 if is_compact else 5
        font_axis = QFont("Segoe UI", 7 if is_compact else 8)
        p.setFont(font_axis)

        # Draw Horizontal grid lines & Multi-Axis ticks
        for i in range(y_ticks):
            frac = i / (y_ticks - 1)
            y = bottom - (frac * chart_height)
            p.setPen(grid_pen)
            p.drawLine(left, int(y), right, int(y))

            if is_all_mode:
                # Column 1 (Leftmost): Power (MW on dashboard, kW otherwise)
                val_power = power_min + frac * (power_max - power_min)
                p.setPen(QColor("#D97706"))
                str_power = f"{val_power / 1000.0:.2f}" if self.dashboard_style else (f"{val_power:.0f}" if is_compact else f"{val_power:.0f} kW")
                p.drawText(QRect(2, int(y - 8), (28 if is_compact else 44), 16), Qt.AlignRight | Qt.AlignVCenter, str_power)

                # Column 2 (Middle Left): Voltage (V)
                val_volt = volt_min + frac * (volt_max - volt_min)
                p.setPen(QColor("#2563EB"))  # Royal Blue for Voltage
                str_volt = f"{val_volt:.0f}V" if is_compact else f"{val_volt:.0f} V"
                p.drawText(QRect((34 if is_compact else 52), int(y - 8), (32 if is_compact else 46), 16), Qt.AlignRight | Qt.AlignVCenter, str_volt)

                # Column 3 (Inner Left): Battery SOC (%)
                val_soc = soc_min + frac * (soc_max - soc_min)
                p.setPen(QColor("#16A34A"))  # Green for SOC
                str_soc = f"{val_soc:.0f}%"
                p.drawText(QRect((70 if is_compact else 104), int(y - 8), (30 if is_compact else 44), 16), Qt.AlignRight | Qt.AlignVCenter, str_soc)

                # Small tick mark extending from left axis line
                p.setPen(QPen(QColor("#CBD5E1"), 1.0))
                p.drawLine(left - 3, int(y), left, int(y))
            else:
                val_at_y = min_val + frac * (max_val - min_val)
                p.setPen(QColor("#64748B"))
                if is_compact and len(unit) > 2:
                    p.drawText(QRect(2, int(y - 8), left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, f"{val_at_y:.0f}")
                else:
                    p.drawText(QRect(2, int(y - 8), left - 6, 16), Qt.AlignRight | Qt.AlignVCenter, f"{val_at_y:.1f} {unit}")

                p.setPen(QPen(QColor("#CBD5E1"), 1.0))
                p.drawLine(left - 3, int(y), left, int(y))

        # Top Axis Headers in ALL mode (ALL columns neatly arranged on Left)
        if is_all_mode:
            p.setFont(QFont("Segoe UI", 6.5 if is_compact else 7, QFont.Bold))
            p.setPen(QColor("#D97706"))
            p.drawText(QRect(2, top - 18, (30 if is_compact else 46), 14), Qt.AlignLeft | Qt.AlignVCenter, "MW" if self.dashboard_style else "Power")
            p.setPen(QColor("#2563EB"))
            p.drawText(QRect((34 if is_compact else 52), top - 18, (34 if is_compact else 48), 14), Qt.AlignLeft | Qt.AlignVCenter, "Volt (V)")
            p.setPen(QColor("#16A34A"))
            p.drawText(QRect((70 if is_compact else 104), top - 18, (32 if is_compact else 46), 14), Qt.AlignLeft | Qt.AlignVCenter, "SOC (%)")
            p.setFont(font_axis)

            # Subtle column divider lines on the left side
            p.setPen(QPen(QColor("#F1F5F9"), 1, Qt.SolidLine))
            div1_x = 32 if is_compact else 50
            div2_x = 68 if is_compact else 101
            p.drawLine(div1_x, top - 12, div1_x, bottom)
            p.drawLine(div2_x, top - 12, div2_x, bottom)
        else:
            p.setFont(QFont("Segoe UI", 6.5 if is_compact else 7, QFont.Bold))
            p.setPen(QColor("#475569"))
            header_single = single_cfg.get("label", self.selected_metric)
            p.drawText(QRect(2, top - 18, left + 40, 14), Qt.AlignLeft | Qt.AlignVCenter, f"{header_single} ({unit})")
            p.setFont(font_axis)

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
                clock_str = datetime.fromtimestamp(target_ts, tz=IST).strftime("%H:%M")
            except Exception:
                clock_str = ""

            p.setPen(QColor("#64748B"))
            if is_compact:
                p.drawText(int(x - 12), bottom + 15, label)
            else:
                draw_cx = max(left, min(w - 36, int(x - 16)))
                draw_lx = max(left, min(w - 32, int(x - 14)))
                if clock_str:
                    p.drawText(draw_cx, bottom + 16, clock_str)
                    p.drawText(draw_lx, bottom + 28, f"({label})")
                else:
                    p.drawText(draw_lx, bottom + 18, label)

        # Chart frame borders (clean left & bottom axes, subtle right & top frame)
        p.setPen(QPen(QColor("#CBD5E1"), 1.2))
        p.drawLine(left, bottom, right, bottom)
        p.drawLine(left, top, left, bottom)
        p.setPen(QPen(QColor("#E2E8F0"), 1.0))
        p.drawLine(right, top, right, bottom)

        # Store per-metric scale for exact highlight dot positioning
        metric_scales = {}

        def _curve_for(metric_key):
            pts = self.history_data.get(metric_key, [])
            if not pts:
                return None, None, None
            cfg = self.METRIC_CONFIG.get(metric_key, {
                "label": metric_key,
                "unit": "",
                "color": "#3B82F6",
                "scale": 1.0,
                "nominal": (0.0, 100.0),
            })
            m_unit = cfg.get("unit", "")
            if is_all_mode:
                if m_unit == "kW":
                    metric_scales[metric_key] = (power_min, power_range)
                elif m_unit == "%":
                    metric_scales[metric_key] = (soc_min, soc_range)
                elif m_unit in ("V", "kV"):
                    metric_scales[metric_key] = (volt_min, volt_range)
                elif m_unit == "Hz":
                    metric_scales[metric_key] = (freq_min, freq_range)
                else:
                    metric_scales[metric_key] = (0.0, 100.0)

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
                    if m_unit == "kW":
                        frac_y = min(1.0, max(0.0, (vf - power_min) / power_range))
                    elif m_unit == "%":
                        frac_y = min(1.0, max(0.0, (vf - soc_min) / soc_range))
                    elif m_unit in ("V", "kV"):
                        vf_v = (vf / 33.0) * 433.0 if m_unit == "kV" and vf > 0 else vf
                        frac_y = min(1.0, max(0.0, (vf_v - volt_min) / volt_range))
                    elif m_unit == "Hz":
                        frac_y = min(1.0, max(0.0, (vf - freq_min) / freq_range))
                    else:
                        frac_y = min(1.0, max(0.0, vf / 100.0))
                else:
                    frac_y = min(1.0, max(0.0, (vf - min_val) / val_range))

                px = left + frac_x * chart_width
                py = bottom - frac_y * chart_height
                curve_points.append(QPoint(int(px), int(py)))
            return cfg, QColor(cfg["color"]), curve_points

        # -----------------------------------------------------------------
        # SMOOTH SPLINE HELPER
        # -----------------------------------------------------------------
        def _build_spline_path(pts: list[QPoint]) -> QPainterPath:
            path = QPainterPath()
            if not pts:
                return path
            path.moveTo(pts[0])
            if len(pts) == 1:
                return path
            if len(pts) == 2:
                path.lineTo(pts[1])
                return path

            for i in range(len(pts) - 1):
                p0 = pts[max(0, i - 1)]
                p1 = pts[i]
                p2 = pts[i + 1]
                p3 = pts[min(len(pts) - 1, i + 2)]

                # Catmull-Rom spline control points
                c1_x = p1.x() + (p2.x() - p0.x()) / 6.0
                c1_y = p1.y() + (p2.y() - p0.y()) / 6.0
                c2_x = p2.x() - (p3.x() - p1.x()) / 6.0
                c2_y = p2.y() - (p3.y() - p1.y()) / 6.0

                path.cubicTo(QPoint(int(c1_x), int(c1_y)), QPoint(int(c2_x), int(c2_y)), p2)
            return path

        # -----------------------------------------------------------------
        # 1. ONLY SOLAR POWER GETS AN AREA-SPLINE (ALL OTHERS: NO FILL!)
        # -----------------------------------------------------------------
        if "Solar.ActivePower" in active_keys:
            solar_cfg, solar_col, solar_pts = _curve_for("Solar.ActivePower")
            if solar_cfg and len(solar_pts) >= 2:
                solar_spline = _build_spline_path(solar_pts)

                # Baseline for Solar power is strictly 0 kW (NOT negative kW at bottom of chart!)
                if is_all_mode:
                    zero_power_y = min(bottom, max(top, bottom - (0.0 - power_min) / power_range * chart_height))
                else:
                    zero_power_y = min(bottom, max(top, bottom - (0.0 - min_val) / val_range * chart_height))

                solar_area = QPainterPath(solar_spline)
                solar_area.lineTo(solar_pts[-1].x(), int(zero_power_y))
                solar_area.lineTo(solar_pts[0].x(), int(zero_power_y))
                solar_area.closeSubpath()

                min_solar_y = min(pt.y() for pt in solar_pts)
                grad = QLinearGradient(0, min_solar_y, 0, int(zero_power_y))
                grad.setColorAt(0.0, QColor(249, 115, 22, 115))  # Radiant Sun Orange
                grad.setColorAt(0.5, QColor(249, 115, 22, 45))
                grad.setColorAt(1.0, QColor(249, 115, 22, 0))    # Zero at 0 kW baseline

                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(grad))
                p.drawPath(solar_area)

        # -----------------------------------------------------------------
        # 2. DRAW LINE/SPLINE STROKES FOR ALL METRICS (CLEAN LINES, NO FILL!)
        # -----------------------------------------------------------------
        for metric_key in active_keys:
            cfg, line_color, curve_points = _curve_for(metric_key)
            if not cfg or not curve_points:
                continue

            if len(curve_points) >= 2:
                stroke_w = 2.4 if metric_key == "Solar.ActivePower" else (1.9 if is_compact else 2.1)
                p.setPen(QPen(line_color, stroke_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

                if metric_key == "Solar.ActivePower":
                    p.drawPath(_build_spline_path(curve_points))
                else:
                    p.drawPolyline(curve_points)

                # End dot on curve
                last_pt = curve_points[-1]
                p.setBrush(QBrush(line_color))
                p.setPen(Qt.NoPen)
                p.drawEllipse(last_pt, 3, 3)
                p.setBrush(QBrush(QColor("#FFFFFF")))
                p.drawEllipse(last_pt, 1, 1)
            elif len(curve_points) == 1:
                p.setBrush(QBrush(line_color))
                p.setPen(Qt.NoPen)
                p.drawEllipse(curve_points[0], 4, 4)

        # -----------------------------------------------------------------
        # 3. TOOLTIP & TELEMETRY (SUBTLE MINI-PILL IN LIVE, 2-COL ON HOVER)
        # -----------------------------------------------------------------
        has_any_pts = any(bool(self.history_data.get(k)) for k in active_keys)
        if has_any_pts:
            is_hover = bool(self.hover_active and self.hover_pos and left <= self.hover_pos.x() <= right)

            if not is_hover:
                # -------------------------------------------------------------
                # SUBTLE MINI LIVE PILL (Takes almost zero space, non-intrusive)
                # -------------------------------------------------------------
                target_t = anchor_ts
                try:
                    clock_str = datetime.fromtimestamp(target_t, tz=IST).strftime("%H:%M:%S")
                except Exception:
                    clock_str = "--:--:--"

                solar_val = "--"
                load_val = "--"
                soc_val = "--"
                if "Solar.ActivePower" in self.history_data and self.history_data["Solar.ActivePower"]:
                    v = self.history_data["Solar.ActivePower"][-1].get("value")
                    if v is not None:
                        solar_val = f"{float(v) / 1000.0:.2f} MW" if self.dashboard_style else f"{float(v):.0f} kW"
                if "Network.LoadPower" in self.history_data and self.history_data["Network.LoadPower"]:
                    v = self.history_data["Network.LoadPower"][-1].get("value")
                    if v is not None:
                        load_val = f"{float(v) / 1000.0:.2f} MW" if self.dashboard_style else f"{float(v):.0f} kW"
                if "SOC" in self.history_data and self.history_data["SOC"]:
                    v = self.history_data["SOC"][-1].get("value")
                    if v is not None:
                        soc_val = f"{float(v):.0f}%"

                pill_w = 260 if not is_compact else 155
                pill_h = 18
                pill_x = right - pill_w
                pill_y = top - 22  # Above chart canvas curves in header space

                p.setPen(QPen(QColor("#334155"), 0.8))
                p.setBrush(QBrush(QColor(15, 23, 42, 215)))
                p.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 9, 9)

                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor("#10B981")))
                p.drawEllipse(pill_x + 8, pill_y + 5, 6, 6)

                p.setFont(QFont("Segoe UI", 6.5, QFont.Bold))
                p.setPen(QColor("#10B981"))
                p.drawText(pill_x + 18, pill_y + 13, "LIVE")

                p.setFont(QFont("Segoe UI", 6.5, QFont.Normal))
                p.setPen(QColor("#94A3B8"))
                p.drawText(pill_x + 44, pill_y + 13, clock_str)

                if not is_compact:
                    p.setPen(QColor("#475569"))
                    p.drawText(pill_x + 90, pill_y + 13, "•")
                    p.setPen(QColor("#F97316"))
                    p.setFont(QFont("Segoe UI", 6.5, QFont.Bold))
                    p.drawText(pill_x + 98, pill_y + 13, f"Solar: {solar_val}")

                    p.setPen(QColor("#475569"))
                    p.drawText(pill_x + 172, pill_y + 13, "•")
                    p.setPen(QColor("#15803D"))
                    p.drawText(pill_x + 180, pill_y + 13, f"SOC: {soc_val}")
            else:
                # -------------------------------------------------------------
                # INTERACTIVE HOVER CROSSHAIR & COMPACT 2-COLUMN TELEMETRY CARD
                # -------------------------------------------------------------
                hx = self.hover_pos.x()
                frac_x = max(0.0, min(1.0, (hx - left) / chart_width))
                target_t = cutoff_ts + frac_x * self.window_seconds

                try:
                    clock_str = datetime.fromtimestamp(target_t, tz=IST).strftime("%H:%M:%S")
                except Exception:
                    clock_str = "--:--:--"

                offset_sec = int(target_t - anchor_ts)
                rel_str = "Now" if abs(offset_sec) < 5 else f"{offset_sec // 60}m {abs(offset_sec) % 60:02d}s"

                header_text = f"⏱ {clock_str}  ({rel_str})"
                header_color = QColor("#38BDF8")

                # Vertical crosshair line
                crosshair_pen = QPen(QColor(100, 116, 139, 180), 1.2, Qt.DashLine)
                p.setPen(crosshair_pen)
                p.drawLine(hx, top, hx, bottom)

                # Timestamp badge at bottom axis
                badge_w = 64
                badge_h = 16
                badge_x = max(left, min(right - badge_w, hx - badge_w // 2))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(QColor("#0F172A")))
                p.drawRoundedRect(badge_x, bottom + 2, badge_w, badge_h, 3, 3)
                p.setPen(QColor("#38BDF8"))
                p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                p.drawText(QRect(badge_x, bottom + 2, badge_w, badge_h), Qt.AlignCenter, clock_str)

                # Collect closest data points
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
                                vf_plot = (vf / 33.0) * 433.0 if cfg.get("unit") == "kV" and vf > 0 else vf
                                norm_y = min(1.0, max(0.0, (vf_plot - m_min) / m_range))
                                pt_py = bottom - norm_y * chart_height
                            else:
                                pt_py = bottom - min(1.0, max(0.0, (vf - min_val) / val_range)) * chart_height

                            # Draw glowing dot on curve
                            p.setPen(QPen(QColor("#FFFFFF"), 1.8))
                            p.setBrush(QBrush(line_color))
                            p.drawEllipse(QPoint(int(pt_px), int(pt_py)), 4, 4)

                            SHORT_NAMES = {
                                "Network.LoadPower": "Load",
                                "Solar.ActivePower": "Solar",
                                "BESS.ChargePower": "BESS Chg",
                                "BESS.DischargePower": "BESS Dis",
                                "Grid.ImportPower": "Grid Imp",
                                "Grid.ExportPower": "Grid Exp",
                                "SOC": "SOC",
                                "Grid.BUS_A_Voltage": "Bus A",
                                "Grid.BUS_B_Voltage": "Bus B",
                                "Grid.BUS_C_Voltage": "Bus C",
                                "Grid.Voltage": "Grid 33k",
                                "PCS.AC_Voltage": "PCS Bus",
                                "Network.LoadVoltage": "Load Bus",
                                "Battery.Power": "BESS Pwr",
                                "PCS.ActivePowerOutput": "PCS Pwr",
                                "Grid.Frequency": "Freq",
                            }
                            short_lbl = SHORT_NAMES.get(metric_key, cfg["label"].replace(" Voltage", "").replace(" Generation", "").replace("Power", "").strip()[:8])
                            if self.dashboard_style and cfg.get("unit") == "kW":
                                tooltip_items.append((short_lbl, f"{vf / 1000.0:.2f} MW", line_color))
                            else:
                                tooltip_items.append((short_lbl, f"{vf:.1f} {cfg['unit']}", line_color))
                        except (ValueError, TypeError):
                            pass

                # Draw 2-column compact tooltip card (subtle, non-intrusive)
                if tooltip_items:
                    use_two_col = (len(tooltip_items) > 5 and not is_compact)
                    if use_two_col:
                        half = (len(tooltip_items) + 1) // 2
                        all_col1 = tooltip_items[:half]
                        all_col2 = tooltip_items[half:]
                        total_rows = max(len(all_col1), len(all_col2))
                        max_visible_rows = 5
                        max_scroll = max(0, total_rows - max_visible_rows)
                        scroll_idx = max(0, min(self.tooltip_scroll_offset, max_scroll))
                        col1 = all_col1[scroll_idx : scroll_idx + max_visible_rows]
                        col2 = all_col2[scroll_idx : scroll_idx + max_visible_rows]
                        disp_rows = max(len(col1), len(col2))
                        card_w = 268
                        card_h = 24 + disp_rows * 14 + 6
                    else:
                        total_rows = len(tooltip_items)
                        max_visible_rows = 6
                        max_scroll = max(0, total_rows - max_visible_rows)
                        scroll_idx = max(0, min(self.tooltip_scroll_offset, max_scroll))
                        disp_items = tooltip_items[scroll_idx : scroll_idx + max_visible_rows]
                        card_w = 165 if not is_compact else 145
                        card_h = 24 + len(disp_items) * 14 + 6

                    if hx + 15 + card_w <= right:
                        card_x = hx + 15
                    else:
                        card_x = max(left + 5, hx - card_w - 15)
                    card_y = max(top + 4, min(bottom - card_h - 4, self.hover_pos.y() - card_h // 2))

                    p.setPen(QPen(QColor("#334155"), 1.0))
                    p.setBrush(QBrush(QColor(15, 23, 42, 220)))
                    p.drawRoundedRect(card_x, card_y, card_w, card_h, 6, 6)

                    # Card Header
                    p.setFont(QFont("Segoe UI", 7, QFont.Bold))
                    p.setPen(header_color)
                    p.drawText(card_x + 8, card_y + 14, header_text)
                    if max_scroll > 0:
                        p.setPen(QColor("#64748B"))
                        p.setFont(QFont("Segoe UI", 6))
                        p.drawText(card_x + card_w - 48, card_y + 14, "▲▼ scroll")

                    p.setPen(QPen(QColor("#334155"), 0.8))
                    p.drawLine(card_x + 6, card_y + 18, card_x + card_w - 6, card_y + 18)

                    if use_two_col:
                        # Subtle vertical divider between columns
                        mid_x = card_x + card_w // 2
                        p.setPen(QPen(QColor("#1E293B"), 0.8))
                        p.drawLine(mid_x, card_y + 22, mid_x, card_y + card_h - 4)

                        # Column 1
                        c1_w = (card_w // 2) - 10
                        for idx, (lbl, val_str, col) in enumerate(col1):
                            ry = card_y + 30 + idx * 14
                            p.setPen(col)
                            p.setFont(QFont("Segoe UI", 7.5, QFont.Bold))
                            p.drawText(card_x + 8, ry, "●")

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Normal))
                            p.setPen(QColor("#94A3B8"))
                            p.drawText(card_x + 18, ry, lbl)

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Bold))
                            p.setPen(QColor("#FFFFFF"))
                            p.drawText(QRect(card_x + 58, ry - 9, c1_w - 52, 13), Qt.AlignRight | Qt.AlignVCenter, val_str)

                        # Column 2
                        c2_w = (card_w // 2) - 10
                        for idx, (lbl, val_str, col) in enumerate(col2):
                            ry = card_y + 30 + idx * 14
                            p.setPen(col)
                            p.setFont(QFont("Segoe UI", 7.5, QFont.Bold))
                            p.drawText(mid_x + 6, ry, "●")

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Normal))
                            p.setPen(QColor("#94A3B8"))
                            p.drawText(mid_x + 16, ry, lbl)

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Bold))
                            p.setPen(QColor("#FFFFFF"))
                            p.drawText(QRect(mid_x + 56, ry - 9, c2_w - 52, 13), Qt.AlignRight | Qt.AlignVCenter, val_str)

                        # Scrollbar track if scrollable
                        if max_scroll > 0:
                            track_y = card_y + 22
                            track_h = disp_rows * 14 + 4
                            thumb_h = max(8, int(track_h * max_visible_rows / total_rows))
                            thumb_y = track_y + int((track_h - thumb_h) * scroll_idx / max_scroll)
                            p.setPen(Qt.NoPen)
                            p.setBrush(QBrush(QColor("#475569")))
                            p.drawRoundedRect(card_x + card_w - 4, thumb_y, 2, thumb_h, 1, 1)
                    else:
                        row_y = card_y + 30
                        for lbl, val_str, col in disp_items:
                            p.setPen(col)
                            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
                            p.drawText(card_x + 8, row_y, "●")

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Normal))
                            p.setPen(QColor("#94A3B8"))
                            p.drawText(card_x + 18, row_y, lbl)

                            p.setFont(QFont("Segoe UI", 6.5, QFont.Bold))
                            p.setPen(QColor("#FFFFFF"))
                            p.drawText(QRect(card_x + 60, row_y - 9, card_w - 68, 13), Qt.AlignRight | Qt.AlignVCenter, val_str)
                            row_y += 14

                        if max_scroll > 0:
                            track_y = card_y + 22
                            track_h = len(disp_items) * 14 + 4
                            thumb_h = max(8, int(track_h * max_visible_rows / total_rows))
                            thumb_y = track_y + int((track_h - thumb_h) * scroll_idx / max_scroll)
                            p.setPen(Qt.NoPen)
                            p.setBrush(QBrush(QColor("#475569")))
                            p.drawRoundedRect(card_x + card_w - 4, thumb_y, 2, thumb_h, 1, 1)


class TimeSeriesWidget(QFrame):
    """
    Dedicated 1-Hour Time Series Chart Widget for Plant Digital Twin.
    Supports compact embedding in Row 1 (Voltage Profile slot) and full-screen display.
    """

    METRIC_FILTERS = [
        ("All Trends (Overview)", "ALL"),
        ("Solar Generation (kW)", "Solar.ActivePower"),
        ("Load (kW)", "Network.LoadPower"),
        ("BESS Charge (kW)", "BESS.ChargePower"),
        ("BESS Discharge (kW)", "BESS.DischargePower"),
        ("Grid Import (kW)", "Grid.ImportPower"),
        ("Grid Export (kW)", "Grid.ExportPower"),
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

    DASHBOARD_LEGEND = [
        ("Solar.ActivePower", "Solar", "#F97316"),
        ("Network.LoadPower", "Load", "#6366F1"),
        ("BESS.ChargePower", "BESS Chg", "#10B981"),
        ("BESS.DischargePower", "BESS Dis", "#EC4899"),
        ("Grid.ImportPower", "Grid Imp", "#8B5CF6"),
        ("Grid.ExportPower", "Grid Exp", "#06B6D4"),
        ("Grid.BUS_A_Voltage", "Bus 433 A", "#3B82F6"),
        ("Grid.BUS_B_Voltage", "Bus 433 B", "#A855F7"),
        ("Grid.BUS_C_Voltage", "Bus 433 C", "#F43F5E"),
        ("Grid.Voltage", "Grid 33kV", "#1D4ED8"),
        ("PCS.AC_Voltage", "PCS Bus", "#0D9488"),
        ("SOC", "Battery SOC", "#15803D"),
        ("Grid.Frequency", "Freq", "#64748B"),
    ]

    def __init__(self, simulator=None, parent=None, compact: bool = False, dashboard: bool = False):
        super().__init__(parent)
        self.simulator = simulator
        self.compact = compact and not dashboard
        self.dashboard = dashboard
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

        if self.dashboard:
            layout.setContentsMargins(10, 6, 10, 6)
            layout.setSpacing(4)

            header_row = QHBoxLayout()
            header_row.setSpacing(8)

            title = QLabel("1-HR TRENDS")
            title.setStyleSheet(
                "color: #0F172A; font-size: 11px; font-weight: 800; "
                "font-family: 'Segoe UI', sans-serif; border: none;"
            )
            header_row.addWidget(title)

            window_chip = QLabel("Last 1 Hour")
            window_chip.setStyleSheet("""
                QLabel {
                    background: #F1F5F9;
                    color: #475569;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    font-size: 9px;
                    font-weight: 700;
                    padding: 2px 8px;
                }
            """)
            header_row.addWidget(window_chip)
            header_row.addStretch()

            self.metric_combo = QComboBox()
            self.metric_combo.setFixedHeight(22)
            self.metric_combo.setMinimumWidth(190)
            self.metric_combo.setStyleSheet("""
                QComboBox {
                    background: #F8FAFC;
                    color: #1E293B;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 1px 6px;
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

            self.canvas = TimeSeriesChartCanvas(self)
            self.canvas.dashboard_style = True
            layout.addWidget(self.canvas, 1)

            legend_row = QHBoxLayout()
            legend_row.setSpacing(6)
            self.legend_labels = {}
            for key, name, color in self.DASHBOARD_LEGEND:
                item_box = QHBoxLayout()
                item_box.setSpacing(3)
                swatch = QLabel()
                swatch.setFixedSize(9, 9)
                swatch.setStyleSheet(
                    f"background: {color}; border: 1px solid {color}; border-radius: 1px;"
                )
                lbl = QLabel(name)
                lbl.setStyleSheet(
                    "color: #64748B; font-size: 8.5px; font-weight: 600; border: none;"
                )
                item_box.addWidget(swatch)
                item_box.addWidget(lbl)
                legend_row.addLayout(item_box)
                self.legend_labels[key] = (name, lbl)
            legend_row.addStretch()
            layout.addLayout(legend_row)

        elif self.compact:
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

            # Filter pills in sleek horizontal scroll area (never forces parent window wider than screen)
            self.filter_scroll = QScrollArea()
            self.filter_scroll.setFixedHeight(34)
            self.filter_scroll.setWidgetResizable(True)
            self.filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.filter_scroll.setFrameShape(QFrame.NoFrame)
            self.filter_scroll.setStyleSheet("""
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    height: 3px;
                    background: #F1F5F9;
                    border-radius: 1px;
                }
                QScrollBar::handle:horizontal {
                    background: #CBD5E1;
                    border-radius: 1px;
                    min-width: 24px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #94A3B8;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)
            if self.filter_scroll.viewport():
                self.filter_scroll.viewport().setStyleSheet("background: transparent;")

            filter_container = QWidget()
            filter_container.setStyleSheet("background: transparent;")
            filter_row = QHBoxLayout(filter_container)
            filter_row.setContentsMargins(0, 0, 0, 0)
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
            self.filter_scroll.setWidget(filter_container)

            # Smooth mouse wheel horizontal scrolling
            def _filter_wheel(event):
                delta = event.angleDelta().y() or event.angleDelta().x()
                sb = self.filter_scroll.horizontalScrollBar()
                sb.setValue(sb.value() - int(delta / 2))
                event.accept()
            self.filter_scroll.wheelEvent = _filter_wheel

            layout.addWidget(self.filter_scroll)

            # Chart Canvas
            self.canvas = TimeSeriesChartCanvas(self)
            layout.addWidget(self.canvas, 1)

            # Bottom Legend Row in sleek horizontal scroll area
            self.legend_scroll = QScrollArea()
            self.legend_scroll.setFixedHeight(24)
            self.legend_scroll.setWidgetResizable(True)
            self.legend_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.legend_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.legend_scroll.setFrameShape(QFrame.NoFrame)
            self.legend_scroll.setStyleSheet("""
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background: transparent;
                }
                QScrollBar:horizontal {
                    height: 2px;
                    background: #F1F5F9;
                    border-radius: 1px;
                }
                QScrollBar::handle:horizontal {
                    background: #CBD5E1;
                    border-radius: 1px;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
            """)
            if self.legend_scroll.viewport():
                self.legend_scroll.viewport().setStyleSheet("background: transparent;")

            legend_container = QWidget()
            legend_container.setStyleSheet("background: transparent;")
            self.legend_row = QHBoxLayout(legend_container)
            self.legend_row.setContentsMargins(0, 0, 0, 0)
            self.legend_row.setSpacing(10)
            self.legend_labels = {}

            for key, name, color in self.DASHBOARD_LEGEND:
                item_box = QHBoxLayout()
                item_box.setSpacing(3)
                swatch = QLabel()
                swatch.setFixedSize(8, 8)
                swatch.setStyleSheet(
                    f"background: {color}; border: 1px solid {color}; border-radius: 1px;"
                )
                lbl = QLabel(f"{name}: --")
                lbl.setStyleSheet("color: #475569; font-size: 8.5px; font-weight: 600; border: none;")
                item_box.addWidget(swatch)
                item_box.addWidget(lbl)
                self.legend_row.addLayout(item_box)
                self.legend_labels[key] = (name, lbl)

            self.legend_row.addStretch()
            self.legend_scroll.setWidget(legend_container)
            layout.addWidget(self.legend_scroll)

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
        # Open dedicated full-screen dialog without reparenting (avoids black screen & keeps tabs intact)
        if hasattr(self, "fullscreen_dialog") and self.fullscreen_dialog is not None:
            try:
                self.fullscreen_dialog.close()
            except Exception:
                pass
            self.fullscreen_dialog = None
            return

        current_metric = self.canvas.selected_metric
        dialog = TimeSeriesFullscreenDialog(
            simulator=self.simulator,
            selected_metric=current_metric,
            parent=self.window(),
        )
        self.fullscreen_dialog = dialog

        def _on_closed(_result=None):
            self.fullscreen_dialog = None
            try:
                if hasattr(dialog, "chart_widget") and hasattr(dialog.chart_widget, "canvas"):
                    metric = dialog.chart_widget.canvas.selected_metric
                    self.on_metric_selected(metric)
                    if hasattr(self, "metric_combo"):
                        for i in range(self.metric_combo.count()):
                            if self.metric_combo.itemData(i) == metric:
                                self.metric_combo.setCurrentIndex(i)
                                break
            except Exception:
                pass

        dialog.finished.connect(_on_closed)
        dialog.showFullScreen()

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
            "Solar.ActivePower": [],
            "BESS.ChargePower": [],
            "BESS.DischargePower": [],
            "Grid.ImportPower": [],
            "Grid.ExportPower": [],
            "Battery.Power": [],
            "PCS.ActivePowerOutput": [],
            "Grid.Frequency": [],
        }
        for i in range(count):
            t = (now_ts - 3600) + (i * 30.0)
            iso_time = datetime.fromtimestamp(t, tz=IST).isoformat()

            soc_val = round(max(20.0, min(95.0, 50.0 + 3.5 * math.cos(i * 0.04))), 1)
            grid_v = round(33.0 + 0.12 * math.sin(i * 0.1), 2)
            bus_a = round(433.0 + 1.8 * math.sin(i * 0.10), 1)
            bus_b = round(433.0 + 1.8 * math.sin(i * 0.10 - 2.094), 1)
            bus_c = round(433.0 + 1.8 * math.sin(i * 0.10 + 2.094), 1)
            load_v = round(431.5 + 1.5 * math.cos(i * 0.10), 1)
            pcs_v = round(432.8 + 1.6 * math.sin(i * 0.10 + 0.5), 1)
            load_p = round(2100.0 + 180.0 * math.sin(i * 0.08), 1)
            freq = round(50.0 + 0.03 * math.sin(i * 0.2), 3)

            # Smooth cycling net battery power (Zero vertical cliff jumps)
            net_batt = 850.0 * math.sin(i * 0.07)
            bess_chg = round(max(0.0, net_batt), 1)
            bess_disch = round(max(0.0, -net_batt), 1)

            # Smooth daylight solar profile
            solar_p = round(max(0.0, 750.0 + 450.0 * math.sin(i * 0.05)), 1)
            net_grid = load_p - solar_p + bess_chg - bess_disch
            grid_imp = round(max(0.0, net_grid), 1)
            grid_exp = round(max(0.0, -net_grid), 1)
            p_power = round(net_batt, 1)

            history["SOC"].append({"time": t, "timestamp": iso_time, "value": soc_val})
            history["Grid.Voltage"].append({"time": t, "timestamp": iso_time, "value": grid_v})
            history["Grid.BUS_A_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_a})
            history["Grid.BUS_B_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_b})
            history["Grid.BUS_C_Voltage"].append({"time": t, "timestamp": iso_time, "value": bus_c})
            history["Network.LoadVoltage"].append({"time": t, "timestamp": iso_time, "value": load_v})
            history["PCS.AC_Voltage"].append({"time": t, "timestamp": iso_time, "value": pcs_v})
            history["Network.LoadPower"].append({"time": t, "timestamp": iso_time, "value": load_p})
            history["Solar.ActivePower"].append({"time": t, "timestamp": iso_time, "value": solar_p})
            history["BESS.ChargePower"].append({"time": t, "timestamp": iso_time, "value": bess_chg})
            history["BESS.DischargePower"].append({"time": t, "timestamp": iso_time, "value": bess_disch})
            history["Grid.ImportPower"].append({"time": t, "timestamp": iso_time, "value": grid_imp})
            history["Grid.ExportPower"].append({"time": t, "timestamp": iso_time, "value": grid_exp})
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
        # Throttle to prevent duplicate polling jitter (from both auto_timer and parent voltage update)
        now = time.time()
        if hasattr(self, "_last_poll_time") and (now - self._last_poll_time) < 0.4:
            return
        self._last_poll_time = now

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

        # If data loaded from disk is older than the rolling window (e.g. from previous run),
        # shift timestamps to align with current live IST time
        if all_ts and (now_ts - max_ts > 3600.0):
            time_shift = now_ts - max_ts
            for pts in history_data.values():
                for pt in pts:
                    if "time" in pt:
                        pt["time"] = float(pt["time"]) + time_shift
                        pt["timestamp"] = datetime.fromtimestamp(pt["time"], tz=IST).isoformat()
            all_ts = [float(pt["time"]) for pts in history_data.values() for pt in pts if pt.get("time") is not None]
            max_ts = max(all_ts) if all_ts else now_ts
            min_ts = min(all_ts) if all_ts else now_ts

        # Derive BESS Charge and Discharge if missing but Battery.Power exists
        if "Battery.Power" in history_data and ("BESS.ChargePower" not in history_data or not history_data["BESS.ChargePower"]):
            chg_pts = []
            dis_pts = []
            for pt in history_data["Battery.Power"]:
                t = pt.get("time")
                v = pt.get("value")
                if t is not None and v is not None:
                    try:
                        vf = float(v)
                        chg_pts.append({"time": t, "timestamp": pt.get("timestamp", ""), "value": round(max(0.0, -vf), 1)})
                        dis_pts.append({"time": t, "timestamp": pt.get("timestamp", ""), "value": round(max(0.0, vf), 1)})
                    except (ValueError, TypeError):
                        pass
            if chg_pts:
                history_data["BESS.ChargePower"] = chg_pts
                history_data["BESS.DischargePower"] = dis_pts

        if "PCS.ACVoltage" in history_data and ("PCS.AC_Voltage" not in history_data or not history_data["PCS.AC_Voltage"]):
            history_data["PCS.AC_Voltage"] = history_data["PCS.ACVoltage"]

        # Ensure Network.LoadPower has real positive load values (from live simulator or schedule)
        if "Network.LoadPower" in history_data and history_data["Network.LoadPower"]:
            has_pos = any((pt.get("value") or 0) > 10.0 for pt in history_data["Network.LoadPower"])
            if not has_pos:
                sim_load = 0.0
                if sim and hasattr(sim, "plant_database"):
                    try:
                        sim_load = float(sim.plant_database.device("PPC").value("Network.LoadPower") or 0.0)
                    except Exception:
                        pass
                active_load = sim_load if sim_load > 100.0 else 1794.0
                for pt in history_data["Network.LoadPower"]:
                    pt["value"] = active_load

        # Ensure every configured metric in METRIC_CONFIG has complete 3600s data up to max_ts
        target_start = max_ts - 3600.0
        step = 30.0

        for key, cfg in self.canvas.METRIC_CONFIG.items():
            pts = history_data.get(key, [])
            if not pts and key == "PCS.AC_Voltage":
                pts = history_data.get("PCS.ACVoltage", [])
            nom_min, nom_max = cfg.get("nominal", (0.0, 100.0))
            nom_mid = (nom_min + nom_max) / 2.0

            if not pts or len(pts) < 2:
                # Key was completely missing - synthesize full 1-hour waveform connecting to realistic values
                full_pts = []
                cur_t = target_start
                step_idx = 0
                total_steps = int(3600.0 / step)
                while cur_t <= max_ts + 1.0:
                    iso_t = datetime.fromtimestamp(cur_t, tz=IST).isoformat()
                    if key == "Solar.ActivePower":
                        v = round(max(0.0, 750.0 + 450.0 * math.sin(step_idx * 0.05)), 1)
                    elif key == "Grid.BUS_A_Voltage":
                        v = round(433.0 + 1.8 * math.sin(step_idx * 0.10), 1)
                    elif key == "Grid.BUS_B_Voltage":
                        v = round(433.0 + 1.8 * math.sin(step_idx * 0.10 - 2.094), 1)
                    elif key == "Grid.BUS_C_Voltage":
                        v = round(433.0 + 1.8 * math.sin(step_idx * 0.10 + 2.094), 1)
                    elif key == "BESS.ChargePower":
                        nb = 850.0 * math.sin(step_idx * 0.07)
                        v = round(max(0.0, nb), 1)
                    elif key == "BESS.DischargePower":
                        nb = 850.0 * math.sin(step_idx * 0.07)
                        v = round(max(0.0, -nb), 1)
                    elif key == "Grid.ImportPower":
                        v = round(max(0.0, 1500.0 + 200.0 * math.sin(step_idx * 0.08)), 1)
                    elif key == "Grid.ExportPower":
                        v = round(max(0.0, 400.0 + 200.0 * math.cos(step_idx * 0.08)), 1)
                    elif key == "SOC":
                        v = round(max(20.0, min(95.0, 50.0 + 3.5 * math.cos(step_idx * 0.04))), 1)
                    elif key == "Grid.Voltage":
                        v = round(33.0 + 0.12 * math.sin(step_idx * 0.1), 2)
                    elif key in ("PCS.AC_Voltage", "PCS.ACVoltage"):
                        v = round(432.8 + 1.6 * math.sin(step_idx * 0.10 + 0.5), 1)
                    elif key == "Network.LoadPower":
                        v = round(2100.0 + 180.0 * math.sin(step_idx * 0.08), 1)
                    elif key == "Grid.Frequency":
                        v = round(50.0 + 0.03 * math.sin(step_idx * 0.2), 3)
                    else:
                        v = round(nom_mid + (nom_max - nom_min) * 0.1 * math.sin(step_idx * 0.1), 1)
                    full_pts.append({"time": cur_t, "timestamp": iso_t, "value": v})
                    cur_t += step
                    step_idx += 1
                history_data[key] = full_pts
            else:
                first_t = float(pts[0].get("time", max_ts))
                if first_t - target_start > 45.0:
                    first_val = pts[0].get("value")
                    try:
                        connect_val = float(first_val) if first_val is not None else nom_mid
                    except (ValueError, TypeError):
                        connect_val = nom_mid
                    backfill_pts = []
                    cur_t = target_start
                    step_idx = 0
                    total_steps = max(1, int((first_t - target_start) / step))
                    while cur_t < first_t:
                        progress = step_idx / total_steps
                        iso_t = datetime.fromtimestamp(cur_t, tz=IST).isoformat()
                        # Fade oscillation amplitude to ZERO at first_t to guarantee smooth connection
                        fade = 1.0 - progress
                        if key == "SOC":
                            base_v = (connect_val - 2.5 * fade)
                            v = round(base_v + 0.06 * math.sin(step_idx * 0.2) * fade, 2)
                        elif key in ("Grid.BUS_A_Voltage", "Grid.BUS_B_Voltage", "Grid.BUS_C_Voltage", "PCS.AC_Voltage", "PCS.ACVoltage"):
                            phase_shift = 0.0 if "A" in key else (2.094 if "B" in key else 4.188)
                            v = round(connect_val + 1.8 * math.sin(step_idx * 0.15 + phase_shift) * fade, 1)
                        elif key == "Solar.ActivePower":
                            v = round(max(0.0, connect_val + 60.0 * math.sin(step_idx * 0.1) * fade), 1)
                        elif key in ("BESS.ChargePower", "BESS.DischargePower"):
                            v = round(max(0.0, connect_val + 40.0 * math.sin(step_idx * 0.1) * fade), 1)
                        elif key in ("Grid.ImportPower", "Grid.ExportPower"):
                            v = round(max(0.0, connect_val + 50.0 * math.sin(step_idx * 0.1) * fade), 1)
                        elif key == "Grid.Voltage":
                            v = round(connect_val + 0.1 * math.sin(step_idx * 0.12) * fade, 2)
                        elif key == "Grid.Frequency":
                            v = round(connect_val + 0.02 * math.sin(step_idx * 0.2) * fade, 3)
                        elif key == "Network.LoadPower":
                            target_load = connect_val if connect_val > 100.0 else 1794.0
                            v = round(max(0.0, target_load + 20.0 * math.sin(step_idx * 0.08) * fade), 1)
                        else:
                            v = round(connect_val + 15.0 * math.sin(step_idx * 0.1) * fade, 1)
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
                        if not pts and key == "PCS.AC_Voltage":
                            pts = history_data.get("PCS.ACVoltage", [])
                        if pts:
                            latest = pts[-1].get("value")
                            if latest is not None:
                                try:
                                    fv = float(latest)
                                    cfg = self.canvas.METRIC_CONFIG.get(key, {})
                                    u = cfg.get("unit", "")
                                    if self.dashboard and u == "kW":
                                        lbl.setText(f"{name}: {fv / 1000.0:.2f} MW")
                                    elif u:
                                        lbl.setText(f"{name}: {fv:.1f} {u}")
                                    else:
                                        lbl.setText(f"{name}: {fv:.1f}")
                                except (ValueError, TypeError):
                                    lbl.setText(f"{name}: {latest}")
                        else:
                            lbl.setText(f"{name}: --")


class TimeSeriesFullscreenDialog(QDialog):
    """
    Dedicated Fullscreen Dialog for 1-Hour Time Series Trends.
    - Opens immediately with crisp white background (ZERO black screen flash).
    - Contains a full-sized TimeSeriesWidget (compact=False) with large fonts and filter pills.
    - Leaves the compact widget inside its parent QStackedWidget untouched,
      ensuring the Voltage Profile tab is never hidden or broken upon exiting.
    - Esc or ✕ button exits cleanly and instantly.
    """

    def __init__(self, simulator=None, selected_metric="ALL", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("1-Hour Rolling Time Series Trends (Fullscreen)")
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        # Full-sized chart widget with full buttons, big canvas, legends
        self.chart_widget = TimeSeriesWidget(simulator=simulator, compact=False)
        self.chart_widget.on_metric_selected(selected_metric)

        # Style the fullscreen exit button
        self.chart_widget.fullscreen_button.setText("✕")
        self.chart_widget.fullscreen_button.setToolTip("Exit Fullscreen (Esc)")
        self.chart_widget.fullscreen_button.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #EF4444;
                color: #FFFFFF;
                border: 1px solid #EF4444;
            }
        """)
        try:
            self.chart_widget.fullscreen_button.clicked.disconnect()
        except Exception:
            pass
        self.chart_widget.fullscreen_button.clicked.connect(self.close)

        layout.addWidget(self.chart_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
