"""Single plant-wide utility availability switch backed by the plant YAML."""

from pathlib import Path
import os
import tempfile

import yaml
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton


class GridAvailabilityControl(QFrame):
    availability_changed = Signal(bool)

    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = Path(config_path)
        self.available = True
        self.setStyleSheet("QFrame {background: #F8FAFC; border: 1px solid #DDE5EE; border-radius: 8px;}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel("Grid Availability")
        label.setStyleSheet("border: none; color: #172B4D; font-size: 13px; font-weight: 700;")
        layout.addWidget(label)
        layout.addStretch()
        self.button = QPushButton()
        self.button.setMinimumSize(180, 34)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(self.toggle)
        layout.addWidget(self.button)
        self.reload()

    def reload(self):
        """Read the persisted utility state without changing the file."""
        try:
            data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
            value = data["plant"]["utility"].get("available", True)
            if not isinstance(value, bool):
                raise ValueError("plant.utility.available must be true or false")
            self.available = value
            self.button.setEnabled(True)
        except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
            self.button.setEnabled(False)
            self.button.setText("Configuration error")
            self.button.setToolTip(str(error))
            return
        self._refresh()

    def _refresh(self):
        self.button.setText("Available" if self.available else "Unavailable")
        self.button.setToolTip("Click to disconnect the utility grid" if self.available else "Click to reconnect the utility grid")
        background, color, border = (("#DCFCE7", "#166534", "#86EFAC") if self.available
                                     else ("#FEE2E2", "#991B1B", "#FCA5A5"))
        self.button.setStyleSheet(f"QPushButton {{background: {background}; color: {color}; border: 1px solid {border}; border-radius: 6px; font-size: 12px; font-weight: 700; padding: 4px 12px;}} QPushButton:hover {{border: 2px solid {color};}}")

    def toggle(self):
        """Change just the utility boolean, preserving all other YAML text."""
        temporary = None
        try:
            text = self.config_path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            current = data["plant"]["utility"].get("available", True)
            if not isinstance(current, bool):
                raise ValueError("plant.utility.available must be true or false")
            available = not current
            node = yaml.compose(text)
            for key in ("plant", "utility"):
                node = next(value for name, value in node.value if name.value == key)
            field = next((value for name, value in node.value if name.value == "available"), None)
            literal = "true" if available else "false"
            if field is not None:
                text = text[:field.start_mark.index] + literal + text[field.end_mark.index:]
            else:
                index = text.rfind("\n", 0, node.start_mark.index) + 1
                text = text[:index] + " " * node.start_mark.column + f"available: {literal}\n" + text[index:]
            yaml.safe_load(text)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.config_path.parent,
                                             delete=False, suffix=".tmp") as output:
                temporary = output.name
                output.write(text)
            os.replace(temporary, self.config_path)
        except (OSError, ValueError, KeyError, TypeError, StopIteration, yaml.YAMLError) as error:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
            QMessageBox.warning(self, "Grid availability", f"Could not save grid availability:\n{error}")
            return
        self.available = available
        self._refresh()
        self.availability_changed.emit(available)
