from __future__ import annotations

from bisect import bisect_left
import copy
import json
import math
import numpy as np
import os
import time
from datetime import datetime
from common.constants import IST
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Signal, QEvent
from state.tags import Tags
from PySide6.QtWidgets import (
    QApplication,
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


class CheckableComboBox(QComboBox):
    selectionChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked_items: set[str] = set()
        self._updating = False
        self._keep_popup_open = False
        self._last_toggled_index = None
        self._toggle_reset_timer = QTimer(self)
        self._toggle_reset_timer.setSingleShot(True)
        self._toggle_reset_timer.timeout.connect(self._reset_toggle_state)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select metrics")
        self.currentIndexChanged.connect(
            lambda _index: self._update_display_text()
        )
        self.view().clicked.connect(self._toggle_item)
        self.view().pressed.connect(self._keep_popup_open_on_press)
        self.activated.connect(self._toggle_activated_item)

    def add_check_item(self, text: str, data: str):
        self.addItem(text, data)
        item = self.model().item(self.count() - 1)
        item.setFlags(
            (item.flags() | Qt.ItemIsEnabled) & ~Qt.ItemIsUserCheckable
        )
        item.setCheckState(Qt.Unchecked)

    def checked_data(self) -> set[str]:
        return set(self._checked_items)

    def set_checked_data(self, data):
        checked = set(data or ())
        if "ALL" in checked or not checked:
            checked = {"ALL"}

        self._updating = True
        try:
            self._checked_items = checked
            for index in range(self.count()):
                item = self.model().item(index)
                item.setCheckState(
                    Qt.Checked if self.itemData(index) in checked else Qt.Unchecked
                )
            self._update_display_text()
        finally:
            self._updating = False

    def _toggle_item(self, model_index):
        self._toggle_index(model_index.row())

    def _toggle_activated_item(self, index):
        self._toggle_index(index)

    def _toggle_index(self, index: int):
        if self._updating:
            return
        if (
            self._toggle_reset_timer.isActive()
            and self._last_toggled_index == index
        ):
            return
        self._last_toggled_index = index
        self._keep_popup_open = True
        key = self.itemData(index)
        if key == "ALL":
            self.set_checked_data({"ALL"})
        else:
            checked = self.checked_data()
            checked.discard("ALL")
            if key in checked:
                checked.remove(key)
            else:
                checked.add(key)
            self.set_checked_data(checked)

        self.selectionChanged.emit(self.checked_data())
        self._toggle_reset_timer.start(0)

    def _keep_popup_open_on_press(self, _model_index):
        self._keep_popup_open = True

    def _reset_toggle_state(self):
        self._last_toggled_index = None
        self._keep_popup_open = False

    def hidePopup(self):
        if self._keep_popup_open:
            self._keep_popup_open = False
            return
        super().hidePopup()

    def _update_display_text(self):
        if self._checked_items == {"ALL"}:
            index = self.findData("ALL")
            text = self.itemText(index) if index >= 0 else "All Trends"
        elif len(self._checked_items) == 1:
            key = next(iter(self._checked_items))
            index = self.findData(key)
            text = self.itemText(index) if index >= 0 else key
        else:
            text = f"{len(self._checked_items)} metrics selected"
        self.lineEdit().setText(text)


class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        labels = []
        for value in values:
            try:
                dt = datetime.fromtimestamp(float(value), tz=IST)
                labels.append(
                    dt.strftime("%H:%M:%S" if spacing < 60 else "%H:%M")
                )
            except (ValueError, TypeError, OSError, OverflowError):
                labels.append("")
        return labels


class SixIntervalAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyle(tickTextOffset=8, autoExpandTextSpace=True)

    def tickValues(self, minVal, maxVal, size):
        low, high = sorted((minVal, maxVal))
        if not math.isfinite(low) or not math.isfinite(high) or high <= low:
            return super().tickValues(minVal, maxVal, size)

        spacing = (high - low) / 6.0
        values = np.linspace(low, high, 7).tolist()
        return [(spacing, values)]


class TimeSeriesChartCanvas(QWidget):
    """
    PyQtGraph-based chart canvas for one-hour rolling historical trends.
    """

    TOOLTIP_BACKGROUND_ALPHA = 155

    AREA_CURVE_METRICS = {
        "BESS.ChargePower",
        "BESS.DischargePower",
    }

    METRIC_CONFIG = {
        Tags.SOLAR.PV_POWER: {
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
        self.history_data: dict[str, list[dict]] = {}
        self.selected_metric = "ALL"
        self.selected_metrics: set[str] = {"ALL"}
        self.anchor_ts = None
        self.window_seconds = 3600.0
        self.dashboard_style = False
        self._visible_metric_samples: dict[str, list[tuple[float, float]]] = {}
        self._curve_items = {}
        self._interaction_until = 0.0
        self._pending_history = None
        self._interaction_timer = QTimer(self)
        self._interaction_timer.setSingleShot(True)
        self._interaction_timer.timeout.connect(self._flush_pending_history)
        self._data_items: list[tuple[pg.ViewBox, pg.PlotDataItem]] = []
        self._hover_markers: dict[
            str, tuple[pg.ViewBox, pg.ScatterPlotItem, str, dict]
        ] = {}

        self.plot = pg.PlotWidget(
            axisItems={
                "bottom": TimeAxisItem(orientation="bottom"),
                "left": SixIntervalAxisItem(orientation="left"),
            }
        )
        self.plot.setBackground("#FFFFFF")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot_item = self.plot.getPlotItem()
        self.plot_item.layout.setContentsMargins(8, 16, 8, 16)
        self.main_view = self.plot_item.getViewBox()
        self._manual_navigation = False
        self.main_view.sigRangeChangedManually.connect(self._on_manual_navigation)
        self.main_view.setMouseMode(pg.ViewBox.RectMode)
        self.main_view.rbScaleBox.setPen(pg.mkPen("#2563EB", width=1.5))
        self.main_view.rbScaleBox.setBrush(pg.mkBrush(59, 130, 246, 40))
        self._chart_column = 1
        self._overlay_slots: list[tuple[pg.AxisItem, pg.ViewBox]] = []
        self.plot_item.hideAxis("right")
        self.plot_item.layout.removeItem(self.plot_item.getAxis("right"))
        self._sync_overlay_views()
        self.main_view.sigResized.connect(self._sync_overlay_views)
        self.v_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#64748B", width=1, style=Qt.DashLine),
        )
        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.v_line.hide()
        self._hover_tooltip = QLabel(self.plot)
        self._hover_tooltip.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._hover_tooltip.setWordWrap(True)
        self._hover_tooltip.setMaximumWidth(360)
        self._hover_tooltip.setStyleSheet(
            "QLabel {"
            f"background-color: rgba(255, 255, 255, {self.TOOLTIP_BACKGROUND_ALPHA});"
            "color: #0F172A;"
            "border: 1px solid #CBD5E1;"
            "border-radius: 6px;"
            "padding: 8px;"
            "font-size: 10px;"
            "}"
        )
        self._hover_tooltip.hide()
        self._mouse_proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved, rateLimit=30, slot=self._on_mouse_proxy)
        self.plot.viewport().installEventFilter(self)
        self.plot.installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)

    def set_selected_metric(self, metric):
        if isinstance(metric, (list, set, tuple)):
            selected = set(metric)
            if "ALL" in selected or not selected:
                selected = {"ALL"}
            self.selected_metrics = selected
            if selected == {"ALL"}:
                self.selected_metric = "ALL"
            elif len(selected) == 1:
                self.selected_metric = next(iter(selected))
            else:
                self.selected_metric = "MULTI"
        else:
            self.selected_metric = metric
            self.selected_metrics = {metric}
        self.update_history(self.history_data, self.window_seconds)

    @staticmethod
    def _unit_group(key: str, config: dict) -> str:
        unit = config.get("unit", "")
        if unit == "kW":
            return "power"
        if unit in ("V", "kV"):
            return "voltage"
        if unit == "%":
            return "soc"
        if unit == "Hz":
            return "frequency"
        return f"unit:{unit}" if unit else f"metric:{key}"

    @staticmethod
    def _group_label(group: str, config: dict) -> str:
        labels = {
            "power": "Power (kW)",
            "voltage": "Voltage (V)",
            "soc": "SOC (%)",
            "frequency": "Frequency (Hz)",
        }
        if group in labels:
            return labels[group]
        unit = config.get("unit", "")
        return f"Value ({unit})" if unit else config.get("label", "Value")

    @staticmethod
    def _plot_value(group: str, config: dict, value: float) -> float:
        if group == "voltage" and config.get("unit") == "kV":
            return value * 1000.0
        return value

    def _ensure_overlay_slot(self, index: int) -> tuple[pg.AxisItem, pg.ViewBox]:
        while len(self._overlay_slots) <= index:
            layout = self.plot_item.layout
            center_items = [
                (row, layout.itemAt(row, self._chart_column))
                for row in range(layout.rowCount())
            ]
            center_items = [
                (row, item) for row, item in center_items if item is not None
            ]
            axes = [axis for axis, _ in self._overlay_slots]
            for _, item in center_items:
                layout.removeItem(item)
            for axis in axes:
                layout.removeItem(axis)
            for row, item in center_items:
                layout.addItem(item, row, self._chart_column + 1)
            for slot_index, (axis, _) in enumerate(self._overlay_slots):
                layout.addItem(
                    axis,
                    2,
                    len(self._overlay_slots) + 1 - slot_index,
                )
            self._chart_column += 1
            axis = SixIntervalAxisItem(orientation="left")
            layout.addItem(axis, 2, 1)
            view = pg.ViewBox(enableMenu=False)
            view.setMouseEnabled(x=False, y=False)
            self.plot_item.scene().addItem(view)
            axis.linkToView(view)
            view.setXLink(self.main_view)
            self._overlay_slots.append((axis, view))
            self._sync_overlay_views()
        return self._overlay_slots[index]

    def _sync_overlay_views(self):
        if not hasattr(self, "main_view"):
            return
        geometry = self.main_view.sceneBoundingRect()
        for _, view in self._overlay_slots:
            view.setGeometry(geometry)
            view.linkedViewChanged(self.main_view, view.XAxis)

    def update_history(
        self,
        history_data: dict[str, list[dict]] | None,
        window_seconds: float = 3600.0,
    ):
        if history_data and time.monotonic() < self._interaction_until:
            self._pending_history = (history_data, window_seconds)
            self._interaction_timer.start(220)
            return
        self._pending_history = None
        previous_range = self.main_view.viewRange()
        self.history_data = history_data or {}
        self.window_seconds = max(1.0, float(window_seconds))

        plot_item = self.plot.getPlotItem()
        active_item_keys = set()

        all_metrics_selected = self.selected_metrics == {"ALL"}
        multiple_metrics_selected = all_metrics_selected or len(self.selected_metrics) > 1
        if all_metrics_selected:
            active_keys = [
                key for key in self.METRIC_CONFIG
                if self.history_data.get(key)
            ]
            if not active_keys:
                active_keys = [
                    key for key, points in self.history_data.items() if points
                ][:8]
        elif self.selected_metrics:
            active_keys = [
                key for key in self.selected_metrics
                if self.history_data.get(key)
            ]
        else:
            active_keys = []

        if not multiple_metrics_selected:
            config = self.METRIC_CONFIG.get(self.selected_metric, {})
            label = config.get("label", self.selected_metric)
            unit = config.get("unit", "")
            plot_item.setLabel("left", f"{label} ({unit})" if unit else label)

        valid_series = []
        for key in active_keys:
            points = self.history_data.get(key, [])
            samples = []
            for point in points:
                try:
                    timestamp = float(point.get("time"))
                    value = float(point.get("value"))
                except (AttributeError, TypeError, ValueError):
                    continue
                if math.isfinite(timestamp) and math.isfinite(value):
                    samples.append((timestamp, value))

            if not samples:
                continue
            samples.sort(key=lambda sample: sample[0])
            config = self.METRIC_CONFIG.get(key, {})
            valid_series.append((key, config, samples))

        timestamps = [timestamp for points in self.history_data.values() for point in points
                      if isinstance(point, dict)
                      for timestamp in [point.get("time")]
                      if isinstance(timestamp, (int, float)) and math.isfinite(timestamp)]
        anchor = self.anchor_ts if self.anchor_ts is not None else (max(timestamps) if timestamps else time.time())
        cutoff = anchor - self.window_seconds
        valid_series = [(key, config, [(t, v) for t, v in samples if cutoff <= t <= anchor])
                        for key, config, samples in valid_series]
        valid_series = [(key, config, samples) for key, config, samples in valid_series if samples]
        self._visible_metric_samples = {
            key: [(timestamp, value) for timestamp, value in samples]
            for key, _, samples in valid_series
        }

        groups: dict[str, list[tuple[str, dict, list[tuple[float, float]]]]] = {}
        for key, config, samples in valid_series:
            group = self._unit_group(key, config)
            groups.setdefault(group, []).append((key, config, samples))

        if multiple_metrics_selected and groups:
            primary_group = "power" if "power" in groups else next(iter(groups))
            primary_config = groups[primary_group][0][1]
            plot_item.setLabel(
                "left",
                self._group_label(primary_group, primary_config),
            )
            overlay_groups = [
                group for group in groups if group != primary_group
            ]
        else:
            primary_group = None
            overlay_groups = []
            if multiple_metrics_selected:
                plot_item.setLabel("left", "Value")
            for _, view in self._overlay_slots:
                view.setVisible(False)
            for axis, _ in self._overlay_slots:
                axis.hide()

        active_views: dict[str, pg.ViewBox] = {}
        ranges: dict[str, tuple[float, float]] = {}
        if primary_group is not None:
            active_views[primary_group] = self.main_view

        for key, config, samples in valid_series:
            group = self._unit_group(key, config)
            group_values = [
                self._plot_value(
                    group,
                    config,
                    self._area_curve_value(key, value),
                )
                for _, value in samples
            ]
            ranges.setdefault(group, (min(group_values), max(group_values)))
            if group_values:
                old_low, old_high = ranges[group]
                ranges[group] = (
                    min(old_low, min(group_values)),
                    max(old_high, max(group_values)),
                )

        for slot_index, group in enumerate(overlay_groups):
            axis, view = self._ensure_overlay_slot(slot_index)
            config = groups[group][0][1]
            axis.setLabel(self._group_label(group, config))
            axis.setTextPen(pg.mkPen(config.get("color", "#475569")))
            axis.show()
            view.setVisible(True)
            active_views[group] = view

        for slot_index in range(len(overlay_groups), len(self._overlay_slots)):
            axis, view = self._overlay_slots[slot_index]
            axis.hide()
            view.setVisible(False)

        if not multiple_metrics_selected and valid_series:
            key, config, samples = valid_series[0]
            group = self._unit_group(key, config)
            active_views[group] = self.main_view
            values = [
                self._area_curve_value(key, value)
                for _, value in samples
            ]
            ranges[group] = (min(values), max(values))

        for group, view in active_views.items():
            low, high = ranges[group]
            if low == high:
                padding = max(abs(low) * 0.05, 1.0)
            else:
                padding = (high - low) * 0.10
            low -= padding
            high += padding
            view.enableAutoRange(view.YAxis, False)
            if not self._manual_navigation or view is not self.main_view:
                view.setYRange(low, high, padding=0)

        for key, config, samples in valid_series:
            group = self._unit_group(key, config)
            view = active_views.get(group)
            if view is None:
                continue
            color = config.get("color", "#3B82F6")
            label = config.get("label", key)
            x_values = np.asarray([sample[0] for sample in samples], dtype=float)
            y_values = np.asarray(
                [
                    self._plot_value(
                        group,
                        config,
                        self._area_curve_value(key, sample[1]),
                    )
                    for sample in samples
                ],
                dtype=float,
            )
            existing = self._curve_items.get(key)
            if existing is not None and existing[0] is not view:
                existing[0].removeItem(existing[1])
                existing = None
            if existing is None:
                curve = pg.PlotDataItem(
                    pen=pg.mkPen(color, width=1), name=label,
                    antialias=False, connect="finite",
                )
                curve.setDownsampling(auto=True, method="peak")
                curve.setClipToView(True)
                if key in self.AREA_CURVE_METRICS:
                    curve.setFillLevel(0)
                    curve.setBrush(pg.mkBrush(color + "40"))
                view.addItem(curve)
                self._curve_items[key] = (view, curve)
            else:
                curve = existing[1]
            curve.setData(x_values, y_values)
            active_item_keys.add(key)
            old_marker = self._hover_markers.get(key)
            if old_marker is None or old_marker[0] is not view:
                if old_marker is not None:
                    old_marker[0].removeItem(old_marker[1])
                marker = pg.ScatterPlotItem(
                    size=7, symbol="o", brush=pg.mkBrush(color),
                    pen=pg.mkPen("#FFFFFF", width=1),
                )
                marker.setZValue(10)
                view.addItem(marker)
            else:
                marker = old_marker[1]
            marker.hide()
            self._hover_markers[key] = (view, marker, group, config)

        for key in list(self._curve_items):
            if key not in active_item_keys:
                view, curve = self._curve_items.pop(key)
                view.removeItem(curve)
        for key in list(self._hover_markers):
            if key not in active_item_keys:
                view, marker, _, _ = self._hover_markers.pop(key)
                view.removeItem(marker)
        self._data_items = list(self._curve_items.values())

        if self._manual_navigation:
            self.main_view.setRange(xRange=previous_range[0], yRange=previous_range[1], padding=0)
        else:
            plot_item.setXRange(cutoff, anchor, padding=0)
        self._sync_overlay_views()

    @classmethod
    def _area_curve_value(cls, key: str, value: float) -> float:
        if key == "BESS.ChargePower":
            return -abs(value)
        if key == "BESS.DischargePower":
            return abs(value)
        return value

    def _hide_hover(self):
        self.v_line.hide()
        self._hover_tooltip.hide()
        for _, marker, _, _ in self._hover_markers.values():
            marker.hide()

    def _flush_pending_history(self):
        if self._pending_history is not None:
            data, window = self._pending_history
            self.update_history(data, window)

    def _on_manual_navigation(self, *_args):
        self._manual_navigation = True
        self._interaction_until = time.monotonic() + 0.2

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Leave:
            self._hide_hover()
        return super().eventFilter(obj, event)

    def _on_mouse_proxy(self, args):
        if QApplication.mouseButtons() != Qt.NoButton:
            self._hide_hover()  # Do not rebuild tooltip HTML during a pan/zoom drag.
            return
        self._on_mouse_moved(args[0])

    def _on_mouse_moved(self, pos):
        plot_item = self.plot.getPlotItem()
        view_box = plot_item.getViewBox()
        if not view_box.sceneBoundingRect().contains(pos):
            self._hide_hover()
            return

        mouse_point = view_box.mapSceneToView(pos)
        cursor_x = mouse_point.x()
        self.v_line.setPos(cursor_x)
        self.v_line.show()

        if self.selected_metrics == {"ALL"}:
            keys = list(self._visible_metric_samples)
        else:
            keys = [
                key for key in self.selected_metrics
                if key in self._visible_metric_samples
            ]

        tooltip_lines = []
        for _, marker, _, _ in self._hover_markers.values():
            marker.hide()
        for key in keys:
            config = self.METRIC_CONFIG.get(key, {})
            samples = self._visible_metric_samples[key]
            if not samples:
                continue

            # Mark the drawn curve at the cursor time, not the nearest sample
            # (which can be visibly far away when sampling is sparse).
            if cursor_x < samples[0][0] or cursor_x > samples[-1][0]:
                continue
            index = bisect_left(samples, (cursor_x, -math.inf))
            if index == 0 or samples[index][0] == cursor_x:
                value = self._area_curve_value(key, samples[index][1])
            else:
                left_t, left_v = samples[index - 1]
                right_t, right_v = samples[index]
                fraction = (cursor_x - left_t) / (right_t - left_t)
                left_v = self._area_curve_value(key, left_v)
                right_v = self._area_curve_value(key, right_v)
                value = left_v + fraction * (right_v - left_v)
            timestamp = cursor_x
            marker_data = self._hover_markers.get(key)
            if marker_data is not None:
                _, marker, group, marker_config = marker_data
                marker_value = self._plot_value(
                    group,
                    marker_config,
                    self._area_curve_value(key, value),
                )
                marker.setData([timestamp], [marker_value])
                marker.show()
            label = config.get("label", key)
            unit = config.get("unit", "")
            value = self._area_curve_value(key, value)
            if len(self.selected_metrics) > 1 or self.selected_metrics == {"ALL"}:
                if unit == "kV":
                    value *= 1000.0
                    unit = "V"
            color = config.get("color", "#3B82F6")
            tooltip_lines.append(
                f'<span style="color:{color}; font-weight:bold;">●</span> '
                f'<span style="color:#0F172A;">{label}: '
                f'{value:.2f} {unit}</span>'
            )

        if not tooltip_lines:
            self._hover_tooltip.hide()
            return

        try:
            time_text = datetime.fromtimestamp(
                cursor_x, tz=IST
            ).strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError, OSError, OverflowError):
            time_text = "Unknown time"
        tooltip_text = (
            '<span style="color:#0F172A; font-weight:bold;">'
            f"Time: {time_text} IST</span><br>"
            + "<br>".join(tooltip_lines)
        )
        self._hover_tooltip.setTextFormat(Qt.RichText)
        self._hover_tooltip.setText(tooltip_text)
        self._hover_tooltip.adjustSize()

        cursor_pos = self.plot.mapFromScene(pos)
        tooltip_x = cursor_pos.x() + 14
        tooltip_y = cursor_pos.y() + 14
        if tooltip_x + self._hover_tooltip.width() > self.plot.width():
            tooltip_x = cursor_pos.x() - self._hover_tooltip.width() - 14
        if tooltip_y + self._hover_tooltip.height() > self.plot.height():
            tooltip_y = cursor_pos.y() - self._hover_tooltip.height() - 14
        self._hover_tooltip.move(max(0, tooltip_x), max(0, tooltip_y))
        self._hover_tooltip.raise_()
        self._hover_tooltip.show()

class TimeSeriesWidget(QFrame):
    """
    Dedicated 1-Hour Time Series Chart Widget for Plant Digital Twin.
    Supports compact embedding in Row 1 (Voltage Profile slot) and full-screen display.
    """

    METRIC_FILTERS = [
        ("All Trends (Overview)", "ALL"),
        ("Solar Generation (kW)", Tags.SOLAR.PV_POWER),
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
        (Tags.SOLAR.PV_POWER, "Solar", "#F97316"),
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
        self._syncing_metric_controls = False

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

            self.metric_combo = CheckableComboBox()
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
                self.metric_combo.add_check_item(label, key)
            self.metric_combo.set_checked_data({"ALL"})
            self.metric_combo.selectionChanged.connect(self._on_combo_changed)
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
            self.metric_combo = CheckableComboBox()
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
                self.metric_combo.add_check_item(label, key)
            self.metric_combo.set_checked_data({"ALL"})
            self.metric_combo.selectionChanged.connect(self._on_combo_changed)
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
            self.button_group.setExclusive(False)
            self.metric_buttons = {}

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
                btn.toggled.connect(
                    lambda checked, key=metric_key:
                    self._on_filter_button_toggled(key, checked)
                )
                self.button_group.addButton(btn, idx)
                self.metric_buttons[metric_key] = btn
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

        self._frozen = False
        self._reset_after_ts = None
        self.history_button = QPushButton("15 min mode")
        self.history_button.setCheckable(True)
        self.history_button.setCursor(Qt.PointingHandCursor)
        self.history_button.setMinimumWidth(115)
        self.history_button.setFixedHeight(24)
        self.history_button.setStyleSheet("""
            QPushButton {
                background: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #93C5FD;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #DBEAFE;
                border-color: #2563EB;
            }
            QPushButton:checked {
                background: #1D4ED8;
                color: #FFFFFF;
                border-color: #1D4ED8;
            }
        """)
        self.history_button.setToolTip(
            "Freeze the last 15 minutes of recorded data. Click again to resume live trends.")
        self.history_button.toggled.connect(self._set_history_mode)
        # Place the mode next to the one-hour label, before metric selection.
        header_row.insertWidget(2 if self.dashboard else 1, self.history_button)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedHeight(24)
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.setStyleSheet("QPushButton {background: #FEF2F2; color: #B91C1C; border: 1px solid #FCA5A5; border-radius: 4px; padding: 2px 10px; font-weight: 600;} QPushButton:hover {background: #FEE2E2;}")
        self.reset_button.setToolTip("Clear plotted history and start showing only new samples")
        self.reset_button.clicked.connect(self.reset_graph)
        header_row.insertWidget(3 if self.dashboard else 2, self.reset_button)
        self.navigation_combo = QComboBox()
        self.navigation_combo.addItems(["Zoom Area", "Pan"])
        self.navigation_combo.setFixedHeight(24)
        self.navigation_combo.setToolTip("Zoom Area: left-drag a rectangle to zoom. Pan: drag to move the chart.")
        self.navigation_combo.currentTextChanged.connect(self._set_navigation_mode)
        header_row.insertWidget(4 if self.dashboard else 3, self.navigation_combo)
        self.fit_button = QPushButton("Reset Zoom")
        self.fit_button.setFixedHeight(24)
        self.fit_button.setCursor(Qt.PointingHandCursor)
        self.fit_button.setStyleSheet("QPushButton {background: #EFF6FF; color: #1D4ED8; border: 1px solid #93C5FD; border-radius: 4px; padding: 2px 10px; font-weight: 600;} QPushButton:hover {background: #DBEAFE;}")
        self.fit_button.setToolTip("Restore the full time window without clearing any data")
        self.fit_button.clicked.connect(self._fit_graph_view)
        header_row.insertWidget(header_row.indexOf(self.fullscreen_button), self.fit_button)
        self._set_navigation_mode("Zoom Area")

        # Initial load & auto-update timer
        self.update_from_simulator()
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.update_from_simulator)
        self.auto_timer.start(1000)

    def _set_navigation_mode(self, mode):
        """Choose rectangle selection or chart dragging explicitly."""
        self.canvas.main_view.setMouseMode(
            pg.ViewBox.RectMode if mode == "Zoom Area" else pg.ViewBox.PanMode)
        self.canvas.plot.setToolTip(
            "Left-drag a rectangle to zoom into that area; mouse wheel also zooms."
            if mode == "Zoom Area" else "Left-drag to pan; mouse wheel zooms.")

    def _fit_graph_view(self):
        """Restore automatic bounds without deleting plotted history."""
        self.canvas._manual_navigation = False
        self.canvas._interaction_until = 0.0
        self.canvas._pending_history = None
        self.canvas._interaction_timer.stop()
        self.canvas.main_view.rbScaleBox.hide()
        self.canvas.update_history(self.canvas.history_data, self.canvas.window_seconds)

    def reset_graph(self):
        """Clear this graph without deleting shared database or disk history."""
        times = [float(point["time"]) for points in self.canvas.history_data.values()
                 for point in points if isinstance(point, dict)
                 and isinstance(point.get("time"), (int, float))
                 and math.isfinite(point["time"])]
        self._reset_after_ts = max([time.time()] + times)
        self.canvas._manual_navigation = False
        self.canvas._interaction_until = 0.0
        self.canvas._pending_history = None
        self.canvas._interaction_timer.stop()
        self.canvas._hide_hover()
        self.canvas.update_history({}, self.canvas.window_seconds)
        for name, label in getattr(self, "legend_labels", {}).values():
            label.setText(f"{name}: --")
        if hasattr(self, "compact_status"):
            self.compact_status.setText("Graph reset — waiting for new samples")
        if hasattr(self, "stats_badge"):
            self.stats_badge.setText("Graph reset — waiting for new samples")
        self._last_poll_time = 0

    def _set_history_mode(self, frozen):
        """Freeze the currently recorded trailing fifteen minutes until toggled off."""
        self._frozen = frozen
        self.canvas._manual_navigation = False
        self.canvas._interaction_until = 0.0
        self.canvas._pending_history = None
        self.canvas._interaction_timer.stop()
        if frozen:
            self.canvas.history_data = copy.deepcopy(self.canvas.history_data)
            times = [float(p["time"]) for pts in self.canvas.history_data.values()
                     for p in pts if p.get("time") is not None]
            self.canvas.anchor_ts = max(times) if times else time.time()
            self.canvas.window_seconds = 900.0
            self.auto_timer.stop()
            if hasattr(self, "stats_badge"):
                self.stats_badge.setText("● HISTORY SNAPSHOT: Last 15 min | Paused")
            if hasattr(self, "compact_status"):
                self.compact_status.setText("● Last 15 min | Paused")
        else:
            self.canvas.anchor_ts = None
            self._last_poll_time = 0
            self.update_from_simulator()
            self.auto_timer.start(1000)
        self.history_button.setText("15 min mode (paused)" if frozen else "15 min mode")
        self.canvas.update_history(self.canvas.history_data, self.canvas.window_seconds)

    def _on_combo_changed(self, selected_metrics):
        self.on_metric_selected(selected_metrics)

    def on_metric_selected(self, metric_keys):
        self.canvas.set_selected_metric(metric_keys)
        selected = set(self.canvas.selected_metrics)
        self._syncing_metric_controls = True
        try:
            if hasattr(self, "metric_combo"):
                self.metric_combo.set_checked_data(selected)
            for key, button in getattr(self, "metric_buttons", {}).items():
                button.setChecked(key in selected)
        finally:
            self._syncing_metric_controls = False

    def _on_filter_button_toggled(self, metric_key: str, checked: bool):
        if self._syncing_metric_controls:
            return

        self._syncing_metric_controls = True
        try:
            if metric_key == "ALL" and checked:
                selected = {"ALL"}
            else:
                if checked:
                    self.metric_buttons["ALL"].setChecked(False)
                selected = {
                    key for key, button in self.metric_buttons.items()
                    if key != "ALL" and button.isChecked()
                }
                if not selected:
                    selected = {"ALL"}
            for key, button in self.metric_buttons.items():
                button.setChecked(key in selected)
        finally:
            self._syncing_metric_controls = False
        self.on_metric_selected(selected)

    def _toggle_fullscreen(self):
        # Open dedicated full-screen dialog without reparenting (avoids black screen & keeps tabs intact)
        if hasattr(self, "fullscreen_dialog") and self.fullscreen_dialog is not None:
            try:
                self.fullscreen_dialog.close()
            except Exception:
                pass
            self.fullscreen_dialog = None
            return

        current_metrics = set(self.canvas.selected_metrics)
        dialog = TimeSeriesFullscreenDialog(
            simulator=self.simulator,
            selected_metric=current_metrics,
            parent=self.window(),
        )
        target = dialog.chart_widget
        target._reset_after_ts = self._reset_after_ts
        target.canvas.update_history(copy.deepcopy(self.canvas.history_data), self.canvas.window_seconds)
        if self._frozen:
            target.canvas.history_data = copy.deepcopy(self.canvas.history_data)
            target.history_button.setChecked(True)
            target.canvas.anchor_ts = self.canvas.anchor_ts
            target.canvas.update_history(target.canvas.history_data, 900.0)
        self.fullscreen_dialog = dialog

        def _on_closed(_result=None):
            self.fullscreen_dialog = None
            try:
                if hasattr(dialog, "chart_widget") and hasattr(dialog.chart_widget, "canvas"):
                    if dialog.chart_widget._reset_after_ts != self._reset_after_ts:
                        self._reset_after_ts = dialog.chart_widget._reset_after_ts
                        self.canvas.history_data = copy.deepcopy(dialog.chart_widget.canvas.history_data)
                        self.canvas._manual_navigation = False
                    metrics = set(dialog.chart_widget.canvas.selected_metrics)
                    self.on_metric_selected(metrics)
                    if hasattr(self, "metric_combo"):
                        self.metric_combo.set_checked_data(metrics)
            except Exception:
                pass

        dialog.finished.connect(_on_closed)
        dialog.showFullScreen()

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
        if self._frozen:
            return
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
                    history_data = copy.deepcopy(ppc_data)
                else:
                    for d_id, d_data in all_devices.items():
                        history_data.update(copy.deepcopy(d_data))
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

        # Device databases are recreated on simulation restart. Keep already
        # plotted real samples inside the rolling window and merge new samples.
        merged = {}
        cutoff = time.time() - 3600.0
        for key in self.canvas.history_data.keys() | history_data.keys():
            by_time = {}
            for point in self.canvas.history_data.get(key, []) + history_data.get(key, []):
                if not isinstance(point, dict):
                    continue
                timestamp = point.get("time")
                if isinstance(timestamp, (int, float)) and math.isfinite(timestamp) and timestamp >= cutoff:
                    by_time[timestamp] = point
            merged[key] = [by_time[timestamp] for timestamp in sorted(by_time)]
        history_data = merged

        if self._reset_after_ts is not None:
            history_data = {
                key: [point for point in points if isinstance(point, dict)
                      and isinstance(point.get("time"), (int, float))
                      and point["time"] > self._reset_after_ts]
                for key, points in history_data.items()
            }

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

        for key, sign in (("BESS.ChargePower", -1), ("BESS.DischargePower", 1)):
            for point in history_data.get(key, []):
                try:
                    value = float(point.get("value"))
                    if math.isfinite(value):
                        point["value"] = sign * abs(value)
                except (TypeError, ValueError):
                    pass

        if history_data:
            if history_data != self.canvas.history_data or self.canvas.window_seconds != 3600.0:
                self.canvas.update_history(history_data, window_seconds=3600.0)

            if self.compact:
                grid_v = self._get_latest_val(history_data, "Grid.Voltage", "kV")
                load_p = self._get_latest_val(history_data, "Network.LoadPower", "kW")
                bus_a = self._get_latest_val(history_data, "Grid.BUS_A_Voltage", "V")
                soc = self._get_latest_val(history_data, "SOC", "%")
                if self.canvas.selected_metrics != {"ALL"} and len(self.canvas.selected_metrics) == 1:
                    selected_key = next(iter(self.canvas.selected_metrics))
                    cfg = self.canvas.METRIC_CONFIG.get(selected_key, {})
                    sel_lbl = cfg.get("label", selected_key)
                    sel_val = self._get_latest_val(history_data, selected_key, cfg.get("unit", ""))
                    self.compact_status.setText(f"● {sel_lbl}: {sel_val}")
                elif self.canvas.selected_metrics != {"ALL"}:
                    self.compact_status.setText(
                        f"● {len(self.canvas.selected_metrics)} metrics selected"
                    )
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
                                    unit = self.canvas.METRIC_CONFIG.get(key, {}).get("unit", "")
                                    lbl.setText(f"{name}: {float(latest):.1f} {unit}")
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
