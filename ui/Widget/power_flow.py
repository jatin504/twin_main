from PySide6.QtCore import Qt, QPoint, QTimer, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
)

# from ui.Widget.icons.factory_icon import FactoryIcon
from ui.Widget.icons.grid_icon import GridIcon
from ui.Widget.icons.pcs_widget import PCSWidget
from ui.Widget.icons.power_value_widget import PowerValueWidget
from ui.Widget.icons.solar_plant_widget import SolarPlantWidget
from ui.Widget.icons.yellow_square_icon import YellowSquareIcon
from ui.Widget.icons.battery_box_icon import BatteryBoxIcon
from ui.Widget.icons.inverter_icon1 import InverterIcon1
from ui.Widget.icons.inverter_icon2 import InverterIcon2
from ui.Widget.icons.inverter_icon3 import InverterIcon3
from ui.Widget.icons.inverter_icon4 import InverterIcon4
from ui.Widget.icons.inverter_icon5 import InverterIcon5
from ui.Widget.icons.green_double_arrow import GreenDoubleArrow
from ui.Widget.icons.green_horizontal_line import GreenHorizontalLine
from ui.Widget.block_widget import BlockWidget
from ui.Widget.lt_panel_boxes import LTPanelGroup
from state.tags import Tags
from common.enums import FaultCode


class SmallStatusIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(22, 22)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QPen(QColor("#35C759"), 2))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(1, 1, 20, 20, 4, 4)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#111111"))
        p.drawEllipse(7, 7, 8, 8)

        p.setBrush(QColor("#35C759"))
        p.drawEllipse(9, 9, 4, 4)


class LTPanelWidget(QWidget):
    OVER_LOADING_LIMIT = 80.0  # 0.80 pu in % (matches models/plant_protection.py OVER_LOADING_LIMIT)
    UNDER_LOADING_LIMIT = 0.0  # 0.0 pu in % (matches models/plant_protection.py UNDER_LOADING_LIMIT)

    def __init__(self, panel_no, parent=None):
        super().__init__(parent)

        self.panel_no = panel_no
        self.loading = None
        self.current = None
        self.is_fault = False
        self.setFixedSize(180, 75)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_values(self, loading, current, is_fault=False):
        self.loading = loading
        self.current = current
        self.is_fault = is_fault
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QPen(QColor("#6B8295"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(7, 22, 30, 30)
        p.drawEllipse(25, 22, 30, 30)
        p.drawLine(55, 37, 75, 37)

        box_x = 75
        box_y = 8
        box_w = 100
        box_h = 57

        # Overloaded check based on OVER_LOADING_LIMIT (80.0%) / UNDER_LOADING_LIMIT (0.0%) or fault
        is_overloaded = bool(self.is_fault)
        if not is_overloaded and self.loading is not None:
            try:
                lf = float(self.loading)
                if lf > self.OVER_LOADING_LIMIT or lf < self.UNDER_LOADING_LIMIT:
                    is_overloaded = True
            except (ValueError, TypeError):
                pass

        if is_overloaded:
            # Highlight with bold red outline rectangle for transformer overload/underload fault
            p.setPen(QPen(QColor("#DC2626"), 2.5))
            p.setBrush(QColor("#FEF2F2"))  # subtle warning tint inside
        else:
            p.setPen(QPen(QColor("#F09A63"), 2))
            p.setBrush(Qt.NoBrush)

        p.drawRect(box_x, box_y, box_w, box_h)

        p.setPen(QColor("#DC2626") if is_overloaded else QColor("#E24A32"))
        font = QFont("Arial", 7)
        font.setBold(True)
        p.setFont(font)

        p.drawText(
            box_x + 5,
            box_y + 15,
            box_w - 10,
            10,
            Qt.AlignCenter,
            f"LT PANEL-{self.panel_no}"
        )

        font.setBold(False)
        p.setFont(font)
        loading_text = "--" if self.loading is None else f"{self.loading:.1f}%"
        current_text = "--" if self.current is None else f"{self.current:.1f} A"

        if is_overloaded:
            font.setBold(True)
            p.setFont(font)
            p.setPen(QColor("#DC2626"))
        else:
            p.setPen(QColor("#E24A32"))

        p.drawText(
            box_x + 5,
            box_y + 29,
            box_w - 10,
            10,
            Qt.AlignCenter,
            f"Loading: {loading_text}",
        )

        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor("#E24A32"))
        p.drawText(
            box_x + 5,
            box_y + 43,
            box_w - 10,
            10,
            Qt.AlignCenter,
            f"Current: {current_text}",
        )


class LineCanvas(QWidget):

    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

        self.line = {
            "name": "MAIN_BUS",
            "x1": 173,
            "y1": 128,
            "x2": 1003,
            "y2": 128,
        }

        self.main_bus_color = QColor("#D8A100")  # YELLOW initially
        self.main_bus_power = None
        self.battery_powers = {unit_id: 0.0 for unit_id in range(1, 6)}
        self.battery_line_map = {
            "RED_LINE_V10": 1,
            "RED_LINE_V9": 2,
            "RED_LINE_V8": 3,
            "RED_LINE_V7": 4,
            "RED_LINE_V11": 5,
            "RED_LINE_V15": 1,
            "RED_LINE_V13": 2,
            "RED_LINE_V14": 3,
            "RED_LINE_V12": 4,
            "RED_LINE_V16": 5,
        }
        self.pcs1_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs2_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs3_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs4_bus_color = QColor("#D8A100")  # YELLOW itially

        self.verticalLines = [
            {"name": "RED_LINE_V1", "x": 177, "y": 3, "h": 90, "color": "#E23C3C"},
            {"name": "RED_LINE_V2", "x": 228, "y": 4, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V3", "x": 402, "y": 4, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V4", "x": 579, "y": 3, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V5", "x": 1039, "y": 228, "h": 200, "color": "#E23C3C", "width": 4},
            {"name": "RED_LINE_V6", "x": 1041, "y": 5, "h": 200, "color": "#E23C3C", "width": 4},
            {"name": "RED_LINE_V7", "x": 627, "y": 265, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V8", "x": 486, "y": 265, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V9", "x": 340, "y": 262, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V10", "x": 199, "y": 260, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V11", "x": 769, "y": 268, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V12", "x": 625, "y": 195, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V13", "x": 338, "y": 194, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V14", "x": 483, "y": 195, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V15", "x": 202, "y": 190, "h": 30, "color": "#E23C3C"},
            {"name": "RED_LINE_V16", "x": 762, "y": 196, "h": 30, "color": "#E23C3C"},
            {"name": "BLUE_LINE_V1", "x": 484, "y": 153, "h": 30, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_V2", "x": 203, "y": 152, "h": 30, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_V3", "x": 626, "y": 172, "h": 30, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_V4", "x": 763, "y": 170, "h": 30, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_V5", "x": 338, "y": 152, "h": 30, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_V6", "x": 963, "y": 170, "h": 140, "color": "#168AAD", "width": 2},
            {"name": "YELLOW_LINE_V1", "x": 56, "y": 130, "h": 20, "color": "#D8A100", "width": 2},
            {"name": "SEA_BLUE_LINE_V1", "x": 1009, "y": 48, "h": 230, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_V2", "x": 401, "y": 70, "h": 38, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_V3", "x": 1019, "y": 108, "h": 128, "color": "#168AAD", "width": 2},
            {"name": "PINK_LINE_V1", "x": 227, "y": 68, "h": 25, "color": "#D51BFF", "width": 2},
            # {"name": "ARROW_DROP1", "x": 630, "y": 173, "h": 10, "arrow": True},
            # {"name": "ARROW_DROP2", "x": 479, "y": 171, "h": 10, "arrow": True},
            # {"name": "ARROW_DROP3", "x": 333, "y": 173, "h": 10, "arrow": True},
            # {"name": "ARROW_DROP4", "x": 773, "y": 173, "h": 10, "arrow": True},
            # {"name": "ARROW_DROP5", "x": 919, "y": 170, "h": 10, "arrow": True},
        ]

        self.horizontalLines = [
            {"name": "INV1_OUT", "x": 56, "y": 128, "w": 150},
            {"name": "RED_BUS", "x": 202, "y": 188, "w": 630, "color": "#E23C3C"},
            {"name": "RED_LINE_H1", "x": 177, "y": 2, "w": 550, "color": "#E23C3C"},
            {"name": "RED_LINE_H2", "x": 135, "y": 52, "w": 40, "color": "#E23C3C"},
            {"name": "RED_LINE_H3", "x": 135, "y": 92, "w": 40, "color": "#E23C3C"},
            {"name": "BLUE_LINE_H1", "x": 203, "y": 151, "w": 838, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_H2", "x": 626, "y": 170, "w": 336, "color": "#168AAD", "width": 2},
            {"name": "BLUE_LINE_H3", "x": 962, "y": 310, "w": 84, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_H1", "x": 932, "y": 47, "w": 75, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_H2", "x": 1009, "y": 278, "w": 30, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_H3", "x": 402, "y": 108, "w": 617, "color": "#168AAD", "width": 2},
            {"name": "SEA_BLUE_LINE_H4",  "x": 1019, "y": 237, "w": 20, "color": "#168AAD", "width": 2},
            {"name": "PINK_LINE_H1", "x": 932, "y": 30, "w": 108, "color": "#D51BFF", "width": 2},
            {"name": "PINK_LINE_H2", "x": 229, "y": 93, "w": 810, "color": "#D51BFF", "width": 2},
        ]

        self.selectedHorizontal = False
        self.selectedVertical = None
        self.selectedIcon = None
        self.selectedHLine = None
        self.selectedSquare = None
        self.selectedRedDrop = False
        self.import_power = 0.0
        self.export_power = 0.0

        self.setStyleSheet("""
        QWidget{
            background:white;
            border:none;
        }
        """)

        self.statusIcon1 = SmallStatusIcon(self)
        self.statusIcon1.move(147, 39)
        self.statusIcon1.show()

        self.statusIcon2 = SmallStatusIcon(self)
        self.statusIcon2.move(147, 80)
        self.statusIcon2.show()

        self.ltPanel1 = LTPanelWidget(1, self)
        self.ltPanel1.setObjectName("LTPANEL1")
        self.ltPanel1.move(193, 13)
        self.ltPanel1.show()

        self.ltPanel2 = LTPanelWidget(2, self)
        self.ltPanel2.setObjectName("LTPANEL2")
        self.ltPanel2.move(369, 17)
        self.ltPanel2.show()

        self.ltPanel3 = LTPanelWidget(3, self)
        self.ltPanel3.setObjectName("LTPANEL3")
        self.ltPanel3.move(547, 17)
        self.ltPanel3.show()

        self.grid = GridIcon()
        self.grid.setParent(self)
        self.grid.move(0, 2)
        self.grid.setObjectName("GRID_ICON")
        self.grid.show()
        self.statusIcon1.raise_()
        self.statusIcon2.raise_()

        # self.factory = FactoryIcon()
        # self.factory.setParent(self)
        # self.factory.move(1031, 27)
        # self.factory.setObjectName("FACTORY_ICON")
        # self.factory.show()

        self.inv1 = InverterIcon1()
        self.inv1.setParent(self)
        self.inv1.move(462, 222)
        self.inv1.setObjectName("INV1_ICON")
        self.inv1.show()

        self.inv2 = InverterIcon2()
        self.inv2.setParent(self)
        self.inv2.move(180, 218)
        self.inv2.setObjectName("INV2_ICON")
        self.inv2.show()

        self.inv3 = InverterIcon3()
        self.inv3.setParent(self)
        self.inv3.move(317, 222)
        self.inv3.setObjectName("INV3_ICON")
        self.inv3.show()

        self.inv4 = InverterIcon4()
        self.inv4.setParent(self)
        self.inv4.move(604, 224)
        self.inv4.setObjectName("INV4_ICON")
        self.inv4.show()

        self.inv5 = InverterIcon5()
        self.inv5.setParent(self)
        self.inv5.move(21, 234)
        self.inv5.setObjectName("INV5_ICON")
        self.inv5.show()

        self.inv6 = InverterIcon4()
        self.inv6.setParent(self)
        self.inv6.move(743, 225)
        self.inv6.setObjectName("INV6_ICON")
        self.inv6.show()

        self.greenDoubleArrow = GreenDoubleArrow()
        self.greenDoubleArrow.setParent(self)
        self.greenDoubleArrow.move(117, 128)
        self.greenDoubleArrow.setObjectName("GREEN_DOUBLE_ARROW")
        self.greenDoubleArrow.show()

        self.greenHLine = GreenHorizontalLine()
        self.greenHLine.setParent(self)
        self.greenHLine.move(723, 52)
        self.greenHLine.setObjectName("GREEN_HLINE")
        self.greenHLine.show()

        self.solar = SolarPlantWidget()
        self.solar.setParent(self)
        self.solar.move(-2, 144)
        self.solar.setObjectName("SOLAR_PLANT")
        self.solar.show()

        self.square1 = YellowSquareIcon()
        self.square2 = YellowSquareIcon()
        self.square3 = YellowSquareIcon()
        self.square4 = YellowSquareIcon()
        self.square5 = YellowSquareIcon()
        self.square6 = YellowSquareIcon()
        self.square7 = YellowSquareIcon()
        self.square8 = YellowSquareIcon()

        for sq in [
            self.square1,
            self.square2,
            self.square3,
            self.square4,
            self.square5,
            self.square6,
            self.square7,
            self.square8,
        ]:
            sq.setParent(self)
            sq.hide()

        self.squarePos = [
            {"name": "SQ1", "widget": self.square1, "x": 270, "y": 122},
            {"name": "SQ2", "widget": self.square2, "x": 476, "y": 179},
            {"name": "SQ3", "widget": self.square3, "x": 331, "y": 179},
            {"name": "SQ4", "widget": self.square4, "x": 618, "y": 179},
            {"name": "SQ5", "widget": self.square5, "x": 754, "y": 181},
            {"name": "SQ6", "widget": self.square6, "x": 196, "y": 180},
            {"name": "SQ7", "widget": self.square7, "x": 1260, "y": 74},
            {"name": "SQ8", "widget": self.square8, "x": 1430, "y": 74},
        ]

        for sq in self.squarePos:
            sq["widget"].move(sq["x"], sq["y"])

        self.bank1 = BatteryBoxIcon("BESS BANK-1")
        self.bank1.setParent(self)
        self.bank1.move(157,285)
        self.bank1.setObjectName("BATTERY1")
        self.bank1.show()

        self.bank2 = BatteryBoxIcon("BESS BANK-2")
        self.bank2.setParent(self)
        self.bank2.move(300,284)
        self.bank2.setObjectName("BATTERY2")
        self.bank2.show()

        self.bank3 = BatteryBoxIcon("BESS BANK-3")
        self.bank3.setParent(self)
        self.bank3.move(443,286)
        self.bank3.setObjectName("BATTERY3")
        self.bank3.show()

        self.bank4 = BatteryBoxIcon("BESS BANK-4")
        self.bank4.setParent(self)
        self.bank4.move(582,286)
        self.bank4.setObjectName("BATTERY4")
        self.bank4.show()

        self.bank5 = BatteryBoxIcon("BESS BANK-5")
        self.bank5.setParent(self)
        self.bank5.move(726,290)
        self.bank5.setObjectName("BATTERY5")
        self.bank5.show()

        self.pcs1 = PCSWidget("PCS-1")
        self.pcs1.setParent(self)
        self.pcs1.move(227,200)
        self.pcs1.setObjectName("PCS1")
        self.pcs1.show()

        self.pcs2 = PCSWidget("PCS-2")
        self.pcs2.setParent(self)
        self.pcs2.move(361,196)
        self.pcs2.setObjectName("PCS2")
        self.pcs2.show()

        self.pcs3 = PCSWidget("PCS-3")
        self.pcs3.setParent(self)
        self.pcs3.move(505,203)
        self.pcs3.setObjectName("PCS3")
        self.pcs3.show()

        self.pcs4 = PCSWidget("PCS-4")
        self.pcs4.setParent(self)
        self.pcs4.move(652,201)
        self.pcs4.setObjectName("PCS4")
        self.pcs4.show()

        self.pcs5 = PCSWidget("PCS-5")
        self.pcs5.setParent(self)
        self.pcs5.move(788,200)
        self.pcs5.setObjectName("PCS5")
        self.pcs5.show()

    def set_main_bus_power(self, power):
        try:
            if power is None:
                self.main_bus_power = None
                # Modbus/Grid data unavailable
                self.main_bus_color = QColor("#D8A100")  # YELLOW
            else:
                power = float(power)
                self.main_bus_power = power
                if power == 0:
                    self.main_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.main_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.main_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.main_bus_power = None
            self.main_bus_color = QColor("#D8A100")  # YELLOW
            self.update()

    def set_import_power(self, power):
        try:
            self.import_power = float(power or 0)
        except (TypeError, ValueError):
            self.import_power = 0.0
        self.update()

    def set_export_power(self, power):
        try:
            self.export_power = float(power or 0)
        except (TypeError, ValueError):
            self.export_power = 0.0
        self.update()

    def set_battery_power(self, unit_id, power):
        try:
            self.battery_powers[unit_id] = float(power or 0)
        except (TypeError, ValueError):
            self.battery_powers[unit_id] = 0.0
        self.update()

    def set_pcs1_bus_power(self, power):
        try:
            if power is None:
                self.pcs1_bus_color = QColor("#D8A100")  # YELLOW
            else:
                power = float(power)
                if power == 0:
                    self.pcs1_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.pcs1_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.pcs1_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.pcs1_bus_color = QColor("#D8A100")  # YELLOW
            self.update()

    def set_pcs2_bus_power(self, power):
        try:
            if power is None:
                self.pcs2_bus_color = QColor("#D8A100")  # YELLOW
            else:
                power = float(power)
                if power == 0:
                    self.pcs2_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.pcs2_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.pcs2_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.pcs2_bus_color = QColor("#D8A100")  # YELLOW
            self.update()

    def set_pcs3_bus_power(self, power):
        try:
            if power is None:
                self.pcs3_bus_color = QColor("#D8A100")
            else:
                power = float(power)
                if power == 0:
                    self.pcs3_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.pcs3_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.pcs3_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.pcs3_bus_color = QColor("#D8A100")
            self.update()

    def set_pcs4_bus_power(self, power):
        try:
            if power is None:
                self.pcs4_bus_color = QColor("#D8A100")
            else:
                power = float(power)
                if power == 0:
                    self.pcs4_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.pcs4_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.pcs4_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.pcs4_bus_color = QColor("#D8A100")
            self.update()

    def paintEvent(self, e):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # ================= MAIN BUS =================
        p.setPen(QPen(self.main_bus_color, 3))
        p.drawLine(
            self.line["x1"],
            self.line["y1"],
            self.line["x2"],
            self.line["y2"]
        )

        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint

        arrow = QPolygon([
            QPoint(self.line["x2"], self.line["y2"]),
            QPoint(self.line["x2"] - 12, self.line["y2"] - 6),
            QPoint(self.line["x2"] - 12, self.line["y2"] + 6),
        ])

        p.setBrush(self.main_bus_color)
        p.drawPolygon(arrow)

        if self.main_bus_power is not None:
            label_x = self.line["x2"] - 105
            label_y = self.line["y2"] - 19
            p.setPen(QColor("#111827"))
            label_font = QFont("Arial", 8)
            label_font.setBold(True)
            p.setFont(label_font)
            p.drawText(
                label_x,
                label_y,
                100,
                16,
                Qt.AlignRight | Qt.AlignVCenter,
                f"LOAD: {self.main_bus_power / 1000:.2f} MW",
            )

        for line in self.verticalLines:
            name = line["name"]
            is_import_v234 = (
                name in (
                    "RED_LINE_V2",
                    "RED_LINE_V3",
                    "RED_LINE_V4",
                )
            )
            is_import_vertical = is_import_v234 or name == "RED_LINE_V1"
            battery_id = self.battery_line_map.get(name)
            if battery_id is not None:
                battery_power = self.battery_powers[battery_id]
                line_color = QColor(
                    "#00ff00" if battery_power != 0 else "#ff0000"
                )
            elif is_import_vertical:
                line_color = QColor(
                    "#00ff00"
                    if self.import_power > 0 or self.export_power > 0
                    else "#ff0000"
                )
            else:
                line_color = QColor(line.get("color", "#D3A000"))
            p.setPen(QPen(line_color, line.get("width", 3)))
            p.drawLine(
                line["x"],
                line["y"],
                line["x"],
                line["y"] + line["h"],
            )

            if battery_id is not None and battery_power != 0:
                p.setBrush(line_color)
                p.setPen(Qt.NoPen)
                if battery_power > 0:
                    arrow = QPolygon([
                        QPoint(line["x"], line["y"]),
                        QPoint(line["x"] - 6, line["y"] + 9),
                        QPoint(line["x"] + 6, line["y"] + 9),
                    ])
                else:
                    arrow = QPolygon([
                        QPoint(line["x"], line["y"] + line["h"]),
                        QPoint(line["x"] - 6, line["y"] + line["h"] - 9),
                        QPoint(line["x"] + 6, line["y"] + line["h"] - 9),
                    ])
                p.drawPolygon(arrow)

            if line.get("arrow"):
                p.setBrush(QColor("#5F6368"))
                p.setPen(Qt.NoPen)

                arrow = QPolygon([
                    QPoint(line["x"], line["y"] + line["h"] + 10),
                    QPoint(line["x"] - 6, line["y"] + line["h"]),
                    QPoint(line["x"] + 6, line["y"] + line["h"]),
                ])

                p.drawPolygon(arrow)

        # ===== Horizontal Lines =====

        for hline in self.horizontalLines:
            name = hline["name"]
            if name == "RED_BUS":
                bus_active = any(
                    power != 0 for power in self.battery_powers.values()
                )
                line_color = QColor(
                    "#00ff00" if bus_active else "#ff0000"
                )
            else:
                is_import_line = name in (
                    "RED_LINE_H1",
                    "RED_LINE_H2",
                    "RED_LINE_H3",
                )
                if is_import_line and (
                    self.import_power > 0 or self.export_power > 0
                ):
                    line_color = QColor("#00ff00")
                elif is_import_line:
                    line_color = QColor("#ff0000")
                else:
                    line_color = QColor(
                        hline.get("color", "#D3A000")
                    )

            p.setPen(QPen(line_color, hline.get("width", 3)))
            p.drawLine(
                hline["x"],
                hline["y"],
                hline["x"] + hline["w"],
                hline["y"],
            )

            if hline.get("arrow"):
                p.setBrush(line_color)
                p.setPen(Qt.NoPen)
                arrow = QPolygon([
                    QPoint(hline["x"] + hline["w"], hline["y"]),
                    QPoint(hline["x"] + hline["w"] - 12, hline["y"] - 6),
                    QPoint(hline["x"] + hline["w"] - 12, hline["y"] + 6),
                ])
                p.drawPolygon(arrow)

        # ================= DYNAMIC PCS SQUARE BOXES =================
        square_color_map = {
            "SQ1": self.pcs1_bus_color,
            "SQ6": self.pcs1_bus_color,
            "SQ2": self.pcs2_bus_color,
            "SQ3": self.pcs2_bus_color,
            "SQ4": self.pcs3_bus_color,
            "SQ5": self.pcs3_bus_color,
            "SQ7": self.pcs4_bus_color,
            "SQ8": self.pcs4_bus_color,
        }
        for sq in self.squarePos:
            color = square_color_map.get(
                sq["name"],
                QColor("#D8A100")
            )
            p.setPen(QPen(color, 1))
            p.setBrush(color)
            widget = sq["widget"]
            p.drawRect(
                sq["x"],
                sq["y"],
                widget.width(),
                widget.height()
            )

class LegendItem(QWidget):

    def __init__(self, color, text):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        line = QLabel("━━")
        line.setStyleSheet(f"""
        QLabel{{
            color:{color};
            font-size:11px;
            font-weight:bold;
            border:none;
        }}
        """)

        lbl = QLabel(text)
        lbl.setStyleSheet("""
        QLabel{
            color:#4B5563;
            font-size:10px;
            border:none;
        }
        """)

        layout.addWidget(line)
        layout.addWidget(lbl)


class DisplayItem(QWidget):

    def __init__(self, text):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        box = QLabel()

        box.setFixedSize(10,10)

        box.setStyleSheet("""
        QLabel{
            background:#36B24A;
            border:1px solid #36B24A;
        }
        """)

        lbl = QLabel(text)

        lbl.setStyleSheet("""
        QLabel{
            color:#4B5563;
            font-size:10px;
            border:none;
        }
        """)

        layout.addWidget(box)
        layout.addWidget(lbl)


class PowerFlowWidget(QFrame):
    # Tag mappings from PPC database for Solar Plant & Solar Inverter
    SOLAR_PPC_TAGS = {
        "active_power": "Solar.ActivePower",        # PPC tag for Solar Plant MW
        "reactive_power": "Solar.ReactivePower",    # PPC tag for Solar Plant MVAr
        "power_factor": "Solar.PowerFactor",        # PPC tag for Solar Plant Power Factor
    }

    SOLAR_INVERTER_PPC_TAGS = {
        "active_power": "SolarInv.ActivePower",     # PPC tag for Solar Inverter MW
        "reactive_power": "SolarInv.ReactivePower", # PPC tag for Solar Inverter MVAr
        "power_factor": "SolarInv.PowerFactor",     # PPC tag for Solar Inverter Power Factor
        "loading": "SolarInv.Loading",              # PPC tag for Solar Inverter Loading %
    }

    LT_PANEL_PPC_TAGS = {
        1: {
            "loading": Tags.Transformer.T1_LOADING,
            "current": Tags.Transformer.T1_LV_CURRENT,
        },
        2: {
            "loading": Tags.Transformer.T2_LOADING,
            "current": Tags.Transformer.T2_LV_CURRENT,
        },
        3: {
            "loading": Tags.Transformer.T3_LOADING,
            "current": Tags.Transformer.T3_LV_CURRENT,
        },
    }

    BLOCK_PANEL_PPC_TAGS = {
        1: {
            "spare": Tags.Grid.ROCOF,
            "series_block_panel": Tags.Load.SERVICE_BLOCK_POWER,
            "stack_panel": Tags.Load.EV_STACK_POWER,
            "cooling_tower": Tags.Load.COOLING_TOWER_POWER,
            "chiller": Tags.Load.CHILLERS_POWER,
        },
        2: {
            "spare": Tags.Grid.ROCOF,
            "series_block_panel": Tags.Grid.ROCOF,
            "stack_panel": Tags.Grid.ROCOF,
            "cooling_tower": Tags.Grid.ROCOF,
            "chiller": Tags.Grid.ROCOF,
        },
    }

    def __init__(self, network_manager=None):
        super().__init__()

        self.network_manager = network_manager

        self.setFixedWidth(1180)
        self.setFixedHeight(500)

        self.setStyleSheet("""
        QFrame{
            background:#FFFFFF;
            border:1px solid #DCE3EC;
            border-radius:3px;
        }

        QLabel{
            background:transparent;
            color:#111827;
            border:none;
        }

        QComboBox{
            background:white;
            border:1px solid #C9D3DE;
            border-radius:2px;
            color:#111827;
            font-size:10px;
            padding-left:6px;
        }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 0, 8)
        root.setSpacing(6)

        # ---------------- Title ----------------

        title = QLabel("POWER FLOW DIAGRAM")
        title.setStyleSheet("""
        QLabel{
            font-size:15px;
            font-weight:700;
            color:#111827;
        }
        """)

        root.addWidget(title)

        # ---------------- Toolbar ----------------

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0,0,0,0)
        toolbar.setSpacing(12)

        lbl = QLabel("View By")
        lbl.setStyleSheet("font-size:10px;color:#4B5563;")
        toolbar.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.addItems(["Power (MW)"])
        self.combo.setFixedSize(120,24)

        toolbar.addWidget(self.combo)

        toolbar.addSpacing(18)

        display = QLabel("Display")
        display.setStyleSheet("font-size:10px;color:#4B5563;")
        toolbar.addWidget(display)

        toolbar.addWidget(DisplayItem("Voltage (kV)"))
        toolbar.addWidget(DisplayItem("Power (MW / MVAr)"))
        toolbar.addWidget(DisplayItem("Loading (%)"))

        toolbar.addStretch()

        loadLbl = QLabel("Loading %")
        loadLbl.setStyleSheet("font-size:10px;color:#4B5563;")
        toolbar.addWidget(loadLbl)

        toolbar.addSpacing(8)

        toolbar.addWidget(LegendItem("#38C74A","0-50"))
        toolbar.addWidget(LegendItem("#D8A100","50-80"))
        toolbar.addWidget(LegendItem("#F28B1D","80-100"))
        toolbar.addWidget(LegendItem("#E23C3C",">100"))

        root.addLayout(toolbar)

        # ---------------- Divider ----------------

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("""
        QFrame{
            background:#E5E7EB;
            border:none;
        }
        """)

        root.addWidget(divider)

        self.canvas = LineCanvas()
        root.addWidget(self.canvas, 1)

        self.solar = self.canvas.solar
        self.inv5 = self.canvas.inv5

        self.blockWidget = BlockWidget(1, self)
        self.blockWidget.setObjectName("BLOCK1")
        self.blockWidget.move(1052, 79)
        self.blockWidget.show()

        self.blockWidget2 = BlockWidget(2, self)
        self.blockWidget2.setObjectName("BLOCK2")
        self.blockWidget2.move(1052, 292)
        self.blockWidget2.show()

        self.ltPanelGroup = LTPanelGroup(self)
        self.ltPanelGroup.move(800, 83)
        self.ltPanelGroup.show()
        self.mainLTPanel1 = self.ltPanelGroup.mainLTPanel1
        self.mainLTPanel2 = self.ltPanelGroup.mainLTPanel2
        self.spaceProvision = self.ltPanelGroup.spaceProvision

        self.live_timer = QTimer(self)

        self.live_timer.timeout.connect(
            self.update_live_data
        )

        # Update every 1 second
        self.live_timer.start(1000)

        # First update immediately
        self.update_live_data()

    def update_live_data(self):

        if self.network_manager is None:
            return

        plant_db = self.network_manager.plant_database

        pcs_widgets = {
            1: self.canvas.pcs1,
            2: self.canvas.pcs2,
            3: self.canvas.pcs3,
            4: self.canvas.pcs4,
            5: self.canvas.pcs5,
        }

        bank_widgets = {
            1: self.canvas.bank1,
            2: self.canvas.bank2,
            3: self.canvas.bank3,
            4: self.canvas.bank4,
            5: self.canvas.bank5,
        }

        # ==================================================
        # PCS + BESS LIVE DATA
        # ==================================================

        for unit_id, widget in pcs_widgets.items():

            pcs_id = f"PCS{unit_id}"
            if pcs_id not in plant_db:
                continue

            try:

                db = plant_db.device(pcs_id)
                ah_tag = getattr(Tags.Battery, "AH_CAPACITY", None)
                battery_data = {
                    "soc": db.value(Tags.Battery.SOC),
                    "stored_energy": db.value(
                        Tags.Battery.STORED_ENERGY
                    ),
                    "stored_capacity_ah": db.value(ah_tag) if ah_tag else 0.0,
                    "power": db.value(
                        Tags.Battery.POWER
                    ),
                    "active_power": db.value(
                        Tags.PCS.ACTIVE_POWER
                    ),
                    "battery_voltage": db.value(
                        Tags.Battery.VOLTAGE
                    ),
                    "temperature": db.value(
                        Tags.Battery.TEMPERATURE
                    ),
                }

                bank_widgets[unit_id].update_data(
                    soc=battery_data["soc"],
                    stored_energy_kwh=battery_data["stored_energy"],
                    stored_capacity_ah=battery_data.get("stored_capacity_ah", 0.0),
                    battery_voltage=battery_data["battery_voltage"],
                    temperature=battery_data["temperature"],
                    power_kw=battery_data["power"],
                )
                self.canvas.set_battery_power(
                    unit_id,
                    battery_data["power"],
                )

                pcs_pwr = db.value(Tags.PCS.ACTIVE_POWER_OUTPUT)
                if pcs_pwr is None:
                    pcs_pwr = db.value(Tags.PCS.ACTIVE_POWER)

                data = {
                    "ac_voltage": db.value(
                        Tags.PCS.AC_VOLTAGE
                    ),
                    "active_power": pcs_pwr,
                    "pcs_state": db.value(Tags.PCS.STATE),
                    "fault_code": db.value(
                        Tags.Fault.CODE
                    )
                }

                if unit_id == 1:
                    self.canvas.set_pcs1_bus_power(
                        data.get("active_power")
                    )
                elif unit_id == 2:
                    self.canvas.set_pcs2_bus_power(
                        data.get("active_power")
                    )
                elif unit_id == 3:
                    self.canvas.set_pcs3_bus_power(
                        data.get("active_power")
                    )
                elif unit_id == 4:
                    self.canvas.set_pcs4_bus_power(
                        data.get("active_power")
                    )

                # print(
                #     f"PCS{unit_id} LIVE:",
                #     data
                # )

                widget.update_data(
                    power_kw=data["active_power"],
                    ac_voltage=data["ac_voltage"],
                    fault_code=data["fault_code"],
                    pcs_state=data["pcs_state"],
                )

            except Exception as e:

                print(
                    f"PCS{unit_id} ERROR:",
                    e
                )
                self.canvas.set_battery_power(unit_id, None)

                if unit_id == 1:
                    self.canvas.set_pcs1_bus_power(None)
                elif unit_id == 2:
                    self.canvas.set_pcs2_bus_power(None)
                elif unit_id == 3:
                    self.canvas.set_pcs3_bus_power(None)
                elif unit_id == 4:
                    self.canvas.set_pcs4_bus_power(None)

        # ==================================================
        # GRID LIVE DATA
        # ==================================================

        try:

            grid_db = plant_db.device("PPC")
            grid_data = {
                "grid_voltage": grid_db.value(
                    Tags.Grid.VOLTAGE
                ),
                "import_power": grid_db.value(
                    Tags.Grid.IMPORT_POWER
                ),
                "export_power": grid_db.value(
                    Tags.Grid.EXPORT_POWER
                ),
                "frequency": grid_db.value(
                    Tags.Grid.FREQUENCY
                ),
                "fault_code": grid_db.value(
                    Tags.Fault.CODE
                ),
                "load_power": grid_db.value(
                    Tags.Network.LOAD_POWER
                ),
                "block_panel_values": {
                    block_no: {
                        key: grid_db.value(tag)
                        for key, tag in box_tags.items()
                    }
                    for block_no, box_tags
                    in self.BLOCK_PANEL_PPC_TAGS.items()
                },
                "lt_panel_values": {
                    panel_no: {
                        key: grid_db.value(tag)
                        for key, tag in panel_tags.items()
                    }
                    for panel_no, panel_tags
                    in self.LT_PANEL_PPC_TAGS.items()
                },
                "grid_available": grid_db.value(Tags.Grid.AVAILABLE),
            }

            print(
                "GRID LIVE:",
                grid_data
            )

            self.canvas.set_import_power(
                grid_data["import_power"]
            )
            self.canvas.set_export_power(
                grid_data["export_power"]
            )

            self.canvas.grid.update_data(
                grid_voltage=grid_data["grid_voltage"],
                import_power=grid_data["import_power"],
                export_power=grid_data["export_power"],
                frequency=grid_data["frequency"],
                fault_code=grid_data["fault_code"],
                grid_available=grid_data["grid_available"],
            )
            self.blockWidget.set_box_values(
                grid_data["block_panel_values"][1]
            )
            self.blockWidget2.set_box_values(
                grid_data["block_panel_values"][2]
            )

            for panel_no, panel_widget in (
                (1, self.canvas.ltPanel1),
                (2, self.canvas.ltPanel2),
                (3, self.canvas.ltPanel3),
            ):
                panel_values = grid_data["lt_panel_values"][panel_no]
                loading_val = panel_values["loading"]
                panel_fault = False
                if loading_val is not None:
                    try:
                        lf = float(loading_val)
                        if lf > LTPanelWidget.OVER_LOADING_LIMIT or lf < LTPanelWidget.UNDER_LOADING_LIMIT:
                            panel_fault = True
                    except (ValueError, TypeError):
                        pass

                panel_widget.set_values(
                    loading=loading_val,
                    current=panel_values["current"],
                    is_fault=panel_fault,
                )

            # self.canvas.factory.update_data(
            #     load_power=grid_data["load_power"]
            # )

            # ==================================================
            # SOLAR PLANT & SOLAR INVERTER LIVE DATA
            # ==================================================
            try:
                def _get_ppc_val(tag_name, default=None):
                    if not tag_name or grid_db is None:
                        return default
                    try:
                        if grid_db.exists(tag_name):
                            v = grid_db.value(tag_name)
                            return v if v is not None else default
                    except Exception:
                        pass
                    return default

                solar_p = _get_ppc_val(self.SOLAR_PPC_TAGS.get("active_power"))
                solar_q = _get_ppc_val(self.SOLAR_PPC_TAGS.get("reactive_power"))
                solar_pf = _get_ppc_val(self.SOLAR_PPC_TAGS.get("power_factor"))

                p_solar_mw = (float(solar_p) / 1000.0 if float(solar_p) > 50.0 else float(solar_p)) if solar_p is not None else 2.15
                q_solar_mvar = float(solar_q) if solar_q is not None else 0.05
                pf_solar = float(solar_pf) if solar_pf is not None else 0.99

                self.canvas.solar.update_data(
                    active_power_mw=p_solar_mw,
                    reactive_power_mvar=q_solar_mvar,
                    power_factor=pf_solar,
                )

                inv_p = _get_ppc_val(self.SOLAR_INVERTER_PPC_TAGS.get("active_power"))
                inv_q = _get_ppc_val(self.SOLAR_INVERTER_PPC_TAGS.get("reactive_power"))
                inv_pf = _get_ppc_val(self.SOLAR_INVERTER_PPC_TAGS.get("power_factor"))
                inv_ld = _get_ppc_val(self.SOLAR_INVERTER_PPC_TAGS.get("loading"))

                p_inv_mw = (float(inv_p) / 1000.0 if float(inv_p) > 50.0 else float(inv_p)) if inv_p is not None else p_solar_mw
                q_inv_mvar = float(inv_q) if inv_q is not None else q_solar_mvar
                pf_inv = float(inv_pf) if inv_pf is not None else pf_solar
                loading_inv = float(inv_ld) if inv_ld is not None else 35.0

                self.canvas.inv5.update_data(
                    active_power_mw=p_inv_mw,
                    reactive_power_mvar=q_inv_mvar,
                    power_factor=pf_inv,
                    loading_pct=loading_inv,
                )
            except Exception as e_solar:
                pass

            # ================= MAIN BUS STATUS =================
            self.canvas.set_main_bus_power(
                grid_data.get("load_power")
            )

        except Exception as e:

            print(
                "GRID ERROR:",
                e
            )
            self.canvas.set_import_power(None)
            self.canvas.set_export_power(None)
            self.canvas.set_main_bus_power(None)
            empty_block_values = {
                block_no: {
                    key: None for key in box_tags
                }
                for block_no, box_tags
                in self.BLOCK_PANEL_PPC_TAGS.items()
            }
            self.blockWidget.set_box_values(empty_block_values[1])
            self.blockWidget2.set_box_values(empty_block_values[2])
            self.canvas.ltPanel1.set_values(None, None)
            self.canvas.ltPanel2.set_values(None, None)
            self.canvas.ltPanel3.set_values(None, None)
