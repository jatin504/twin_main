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
            "label": "Load",
            "unit": "kW",
            "color": "#F59E0B",
            "scale": 1.0,
            "nominal": (1500.0, 4500.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "Solar.ActivePower": {
            "label": "Solar Generation",
            "unit": "kW",
            "color": "#FB923C",
            "scale": 1.0,
            "nominal": (0.0, 1500.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "BESS.ChargePower": {
            "label": "BESS Charge",
            "unit": "kW",
            "color": "#22C55E",
            "scale": 1.0,
            "nominal": (0.0, 2500.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "BESS.DischargePower": {
            "label": "BESS Discharge",
            "unit": "kW",
            "color": "#16A34A",
            "scale": 1.0,
            "nominal": (0.0, 2500.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "Grid.ImportPower": {
            "label": "Grid Import",
            "unit": "kW",
            "color": "#2563EB",
            "scale": 1.0,
            "nominal": (0.0, 4000.0),
            "tier": (0.05, 0.25),
            "fill": True,
        },
        "Grid.ExportPower": {
            "label": "Grid Export",
            "unit": "kW",
            "color": "#7C3AED",
            "scale": 1.0,
            "nominal": (0.0, 4000.0),
            "tier": (0.05, 0.25),
            "fill": True,
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
        self.dashboard_style: bool = False

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        if self.hover_pos and abs(self.hover_pos.x() - pos.x()) < 2:
            return
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

        # Canvas bounds (Multiple Y-axes: reserve space on Left for Power [kW] and Right for SOC [%]/Voltage [V])
        is_all_mode = (self.selected_metric == "ALL")

        if is_all_mode:
            left = 32 if is_compact else 52
            right = w - (68 if is_compact else 80)
            top = 18 if is_compact else 28
            bottom = h - (24 if is_compact else 38)
        else:
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
            default_keys = [
                "Network.LoadPower",
                "Solar.ActivePower",
                "BESS.ChargePower",
                "BESS.DischargePower",
                "Grid.ImportPower",
                "Grid.ExportPower",
                "SOC",
                "Grid.Voltage",
                "PCS.AC_Voltage",
                "Grid.Frequency",
                "Grid.BUS_A_Voltage",
                "Battery.Power",
            ]
            active_keys = [k for k in default_keys if k in self.history_data and self.history_data[k]]
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

        # Power Axis Range (Left) - stabilized with step rounding to eliminate vertical jitter
        if power_vals:
            power_min = min(power_vals)
            power_max = max(power_vals)
            if power_min == power_max:
                power_min, power_max = (power_min * 0.9, power_min * 1.1)
            else:
                p_pad = max(100.0, (power_max - power_min) * 0.12)
                power_min = power_min - p_pad
                power_max = power_max + p_pad
            power_min = math.floor(power_min / 250.0) * 250.0
            power_max = math.ceil(power_max / 250.0) * 250.0
        else:
            power_min, power_max = (0.0, 5000.0)
        power_range = max(1e-6, power_max - power_min)

        # SOC Axis Range (Right) - stabilized to 10% steps
        if soc_vals:
            soc_min = max(0.0, math.floor((min(soc_vals) - 5.0) / 10.0) * 10.0)
            soc_max = min(100.0, math.ceil((max(soc_vals) + 5.0) / 10.0) * 10.0)
            if soc_min >= soc_max:
                soc_min, soc_max = (0.0, 100.0)
        else:
            soc_min, soc_max = (0.0, 100.0)
        soc_range = max(1e-6, soc_max - soc_min)

        # Voltage Axis Range - stabilized to 5V steps
        if volt_vals:
            v_low = min(volt_vals)
            v_high = max(volt_vals)
            v_pad = max(5.0, (v_high - v_low) * 0.15) if v_low != v_high else 10.0
            volt_min = math.floor((v_low - v_pad) / 5.0) * 5.0
            volt_max = math.ceil((v_high + v_pad) / 5.0) * 5.0
        else:
            volt_min, volt_max = (380.0, 440.0)
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
                # 1. Left Y-Axis: Power (MW on dashboard, kW otherwise)
                val_power = power_min + frac * (power_max - power_min)
                p.setPen(QColor("#D97706"))
                if self.dashboard_style:
                    p.drawText(2, int(y + 4), f"{val_power / 1000.0:.2f}")
                elif is_compact:
                    p.drawText(2, int(y + 4), f"{val_power:.0f}")
                else:
                    p.drawText(4, int(y + 4), f"{val_power:.0f} kW")

                # 2. Right Y-Axis Column 1: Voltage (V)
                val_volt = volt_min + frac * (volt_max - volt_min)
                p.setPen(QColor("#2563EB"))  # Royal Blue for Voltage
                p.drawText(right + (7 if is_compact else 10), int(y + 4), f"{val_volt:.0f}V" if is_compact else f"{val_volt:.0f} V")

                # 3. Right Y-Axis Column 2: SOC (%)
                val_soc = soc_min + frac * (soc_max - soc_min)
                p.setPen(QColor("#16A34A"))  # Green for SOC
                p.drawText(right + (36 if is_compact else 44), int(y + 4), f"{val_soc:.0f}%")
            else:
                val_at_y = min_val + frac * (max_val - min_val)
                p.setPen(QColor("#64748B"))
                if is_compact and len(unit) > 2:
                    p.drawText(2, int(y + 4), f"{val_at_y:.0f}")
                else:
                    p.drawText(2 if is_compact else 8, int(y + 4), f"{val_at_y:.1f} {unit}")

        # Top Axis Headers in ALL mode (Left=Power, Right=Voltage & SOC)
        if is_all_mode:
            p.setFont(QFont("Segoe UI", 6 if is_compact else 7, QFont.Bold))
            p.setPen(QColor("#D97706"))
            p.drawText(2, top - 4, "MW" if self.dashboard_style else "kW (Power)")
            p.setPen(QColor("#2563EB"))
            p.drawText(right + (4 if is_compact else 8), top - 4, "V (Volt)")
            p.setPen(QColor("#16A34A"))
            p.drawText(right + (34 if is_compact else 42), top - 4, "% (SOC)")
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
                if clock_str:
                    p.drawText(int(x - 16), bottom + 16, clock_str)
                    p.drawText(int(x - 14), bottom + 28, f"({label})")
                else:
                    p.drawText(int(x - 14), bottom + 18, label)

        # Baseline axis borders
        p.setPen(QPen(QColor("#CBD5E1"), 1.2))
        p.drawLine(left, bottom, right, bottom)
        p.drawLine(left, top, left, bottom)
        if is_all_mode:
            p.setPen(QPen(QColor("#A7F3D0"), 1.2))
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

        # Filled power bands first, then strokes on top
        for metric_key in active_keys:
            cfg, line_color, curve_points = _curve_for(metric_key)
            if not cfg or len(curve_points) < 2:
                continue
            if not (is_all_mode and cfg.get("fill")):
                continue
            fill_path = QPainterPath()
            fill_path.moveTo(curve_points[0].x(), bottom)
            for pt in curve_points:
                fill_path.lineTo(pt)
            fill_path.lineTo(curve_points[-1].x(), bottom)
            fill_path.closeSubpath()
            fill_color = QColor(line_color)
            fill_color.setAlpha(70 if self.dashboard_style else 46)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(fill_color))
            p.drawPath(fill_path)

        for metric_key in active_keys:
            cfg, line_color, curve_points = _curve_for(metric_key)
            if not cfg:
                continue
            if len(curve_points) >= 2:
                p.setPen(QPen(line_color, 2.0 if is_compact else 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawPolyline(curve_points)

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
                    clock_str = datetime.fromtimestamp(target_t, tz=IST).strftime("%H:%M:%S")
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
                    clock_str = datetime.fromtimestamp(target_t, tz=IST).strftime("%H:%M:%S")
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
                            vf_plot = (vf / 33.0) * 433.0 if cfg.get("unit") == "kV" and vf > 0 else vf
                            norm_y = min(1.0, max(0.0, (vf_plot - m_min) / m_range))
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
        ("Load (kW)", "Network.LoadPower"),
        ("Solar Generation (kW)", "Solar.ActivePower"),
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
        ("Network.LoadPower", "Load", "#F59E0B"),
        ("Solar.ActivePower", "Solar Generation", "#FB923C"),
        ("BESS.ChargePower", "BESS Charge", "#22C55E"),
        ("BESS.DischargePower", "BESS Discharge", "#16A34A"),
        ("Grid.ImportPower", "Grid Import", "#2563EB"),
        ("Grid.ExportPower", "Grid Export", "#7C3AED"),
        ("SOC", "SOC", "#16A34A"),
        ("Grid.Voltage", "Grid Voltage", "#2563EB"),
        ("PCS.AC_Voltage", "PCS Voltage", "#F59E0B"),
        ("Grid.Frequency", "Frequency", "#0284C7"),
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
            legend_row.setSpacing(10)
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
            frac = i / count
            iso_time = datetime.fromtimestamp(t, tz=IST).isoformat()

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

            solar_p = round(max(0.0, 1150.0 + 80.0 * math.sin(i * 0.07)), 1)
            bess_chg = round(max(0.0, 950.0 + 100.0 * math.sin(i * 0.11)), 1) if frac < 0.45 else 0.0
            bess_disch = round(max(0.0, 1200.0 + 120.0 * math.cos(i * 0.09)), 1) if frac >= 0.45 else 0.0
            grid_imp = round(max(0.0, load_p - solar_p - bess_disch + bess_chg), 1)
            grid_exp = round(max(0.0, solar_p + bess_disch - load_p), 1)

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
                    iso_t = datetime.fromtimestamp(cur_t, tz=IST).isoformat()

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
