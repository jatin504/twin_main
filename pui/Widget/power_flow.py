from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
)

from ui.Widget.icons.factory_icon import FactoryIcon
from ui.Widget.icons.grid_icon import GridIcon
from ui.Widget.icons.breaker_icon import BreakerIcon
from ui.Widget.icons.cb_solar_icon import CBSolarIcon
from ui.Widget.icons.pcs_widget import PCSWidget
from ui.Widget.icons.power_value_widget import PowerValueWidget
from ui.Widget.icons.solar_plant_widget import SolarPlantWidget
from ui.Widget.icons.yellow_square_icon import YellowSquareIcon
from ui.Widget.icons.bus_drop_icon import BusDropIcon
from ui.Widget.icons.red_bus_drop_icon import RedBusDropIcon
from ui.Widget.icons.green_bus_drop_icon import GreenBusDropIcon
from ui.Widget.icons.battery_box_icon import BatteryBoxIcon
from ui.Widget.icons.inverter_icon1 import InverterIcon1
from ui.Widget.icons.inverter_icon2 import InverterIcon2
from ui.Widget.icons.inverter_icon3 import InverterIcon3
from ui.Widget.icons.inverter_icon4 import InverterIcon4
from ui.Widget.icons.inverter_icon5 import InverterIcon5
from ui.Widget.icons.green_double_arrow import GreenDoubleArrow
from ui.Widget.icons.pcs_power_delta import PCSPowerDelta
from ui.Widget.icons.green_horizontal_line import GreenHorizontalLine
from state.tags import Tags


class LineCanvas(QWidget):

    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

        self.line = {
            "name": "MAIN_BUS",
            "x1": 212,
            "y1": 76,
            "x2": 1042,
            "y2": 76,
        }

        self.main_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs1_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs2_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs3_bus_color = QColor("#D8A100")  # YELLOW initially
        self.pcs4_bus_color = QColor("#D8A100")  # YELLOW initially

        self.verticalLines = [
            {"name": "INV1_DROP", "x": 289, "y": 76, "h": 80},
            {"name": "INV2_DROP", "x": 366, "y": 77, "h": 50},
            {"name": "BUS_DROP1", "x": 809, "y": 131, "h": 30},
            {"name": "BUS_DROP2", "x": 669, "y": 133, "h": 30},
            {"name": "INV3_DROP", "x": 720, "y": 78, "h": 50},
            {"name": "INV4_DROP", "x": 861, "y": 78, "h": 50},
            {"name": "INV5_DROP", "x": 137, "y": 156, "h": 50},
            {"name": "INV6_DROP", "x": 983, "y": 126, "h": 50},
            {"name": "ARROW_DROP1", "x": 809, "y": 154, "h": 10, "arrow": True},
            {"name": "ARROW_DROP2", "x": 669, "y": 156, "h": 10, "arrow": True},
            {"name": "ARROW_DROP3", "x": 366, "y": 121, "h": 10, "arrow": True},
        ]

        self.horizontalLines = [
            {"name": "INV1_OUT", "x": 138, "y": 156, "w": 150},
            {"name": "INV2_OUT", "x": 368, "y": 106, "w": 50},
            {"name": "INV3_OUT", "x": 669, "y": 130, "w": 50},
            {"name": "INV4_OUT", "x": 809, "y": 128, "w": 50},
            {"name": "INV5_OUT", "x": 984, "y": 126, "w": 50},
        ]

        self.dragging = False
        self.selectedHorizontal = False
        self.selectedVertical = None
        self.selectedGreen = False
        self.selectedIcon = None
        self.selectedHLine = None
        self.selectedSquare = None
        self.selectedRedDrop = False

        self.offsetX = 0
        self.offsetY = 0

        self.greenLine = {
            "name": "GRID_FLOW",
            "x": 125,
            "y": 77,
            "length": 50,
        }

        self.setStyleSheet("""
        QWidget{
            background:white;
            border:none;
        }
        """)

        self.grid = GridIcon()
        self.grid.setParent(self)
        self.grid.move(3, 15)
        self.grid.setObjectName("GRID_ICON")
        self.grid.show()

        self.breaker = BreakerIcon()
        self.breaker.setParent(self)
        self.breaker.move(177, 62)
        self.breaker.setObjectName("BREAKER_ICON")
        self.breaker.show()

        self.factory = FactoryIcon()
        self.factory.setParent(self)
        self.factory.move(1031, 27)
        self.factory.setObjectName("FACTORY_ICON")
        self.factory.show()

        self.inv1 = InverterIcon1()
        self.inv1.setParent(self)
        self.inv1.move(789, 171)
        self.inv1.setObjectName("INV1_ICON")
        self.inv1.show()

        self.inv2 = InverterIcon2()
        self.inv2.setParent(self)
        self.inv2.move(348, 143)
        self.inv2.setObjectName("INV2_ICON")
        self.inv2.show()

        self.inv3 = InverterIcon3()
        self.inv3.setParent(self)
        self.inv3.move(649, 173)
        self.inv3.setObjectName("INV3_ICON")
        self.inv3.show()

        self.inv4 = InverterIcon4()
        self.inv4.setParent(self)
        self.inv4.move(964, 178)
        self.inv4.setObjectName("INV4_ICON")
        self.inv4.show()

        self.inv5 = InverterIcon5()
        self.inv5.setParent(self)
        self.inv5.move(164, 272)
        self.inv5.setObjectName("INV5_ICON")
        self.inv5.show()

        self.greenDoubleArrow = GreenDoubleArrow()
        self.greenDoubleArrow.setParent(self)
        self.greenDoubleArrow.move(259, 163)
        self.greenDoubleArrow.setObjectName("GREEN_DOUBLE_ARROW")
        self.greenDoubleArrow.show()

        self.greenHLine = GreenHorizontalLine()
        self.greenHLine.setParent(self)
        self.greenHLine.move(237, 347)
        self.greenHLine.setObjectName("GREEN_HLINE")
        self.greenHLine.show()

        self.cbSolar = CBSolarIcon()
        self.cbSolar.setParent(self)
        self.cbSolar.move(125, 208)
        self.cbSolar.setObjectName("CB_SOLAR")
        self.cbSolar.show()

        self.solar = SolarPlantWidget()
        self.solar.setParent(self)
        self.solar.move(71, 233)
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

        self.busDrop1 = BusDropIcon()
        self.busDrop2 = BusDropIcon()
        self.busDrop3 = BusDropIcon()

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
            {"name": "SQ1", "widget": self.square1, "x": 359, "y": 66},
            {"name": "SQ2", "widget": self.square2, "x": 662, "y": 123},
            {"name": "SQ3", "widget": self.square3, "x": 712, "y": 122},
            {"name": "SQ4", "widget": self.square4, "x": 801, "y": 121},
            {"name": "SQ5", "widget": self.square5, "x": 854, "y": 119},
            {"name": "SQ6", "widget": self.square6, "x": 359, "y": 99},
            {"name": "SQ7", "widget": self.square7, "x": 1260, "y": 74},
            {"name": "SQ8", "widget": self.square8, "x": 1430, "y": 74},
        ]

        for sq in self.squarePos:
            sq["widget"].move(sq["x"], sq["y"])

        for w in [self.busDrop1, self.busDrop2, self.busDrop3]:
            w.setParent(self)
            w.show()

        self.busDrop1.move(361,183)
        self.busDrop2.move(803,209)
        self.busDrop3.move(662, 209)

        self.busDrop1.setObjectName("BUS_DROP_ICON1")
        self.busDrop2.setObjectName("BUS_DROP_ICON2")
        self.busDrop3.setObjectName("BUS_DROP_ICON3")

        self.greenDrop1 = GreenBusDropIcon()
        self.greenDrop1.setParent(self)
        self.greenDrop1.move(804,245)
        self.greenDrop1.setObjectName("GREEN_DROP1")
        self.greenDrop1.show()

        self.greenDrop2 = GreenBusDropIcon()
        self.greenDrop2.setParent(self)
        self.greenDrop2.move(662, 246)
        self.greenDrop2.setObjectName("GREEN_DROP2")
        self.greenDrop2.show()

        self.greenDrop3 = GreenBusDropIcon()
        self.greenDrop3.setParent(self)
        self.greenDrop3.move(977,254)
        self.greenDrop3.setObjectName("GREEN_DROP3")
        self.greenDrop3.show()

        self.greenDrop4 = GreenBusDropIcon()
        self.greenDrop4.setParent(self)
        self.greenDrop4.move(760, 170)
        self.greenDrop4.setObjectName("GREEN_DROP4")
        self.greenDrop4.show()

        self.greenDrop5 = GreenBusDropIcon()
        self.greenDrop5.setParent(self)
        self.greenDrop5.move(361, 220)
        self.greenDrop5.setObjectName("GREEN_DROP5")
        self.greenDrop5.show()

        self.greenDrop6 = GreenBusDropIcon()
        self.greenDrop6.setParent(self)
        self.greenDrop6.move(1120, 240)
        self.greenDrop6.setObjectName("GREEN_DROP6")
        self.greenDrop6.show()

        self.redDrop = RedBusDropIcon()
        self.redDrop.setParent(self)
        self.redDrop.move(977,217)
        self.redDrop.setObjectName("RED_DROP")
        self.redDrop.show()

        self.bank1 = BatteryBoxIcon("BESS BANK-1")
        self.bank1.setParent(self)
        self.bank1.move(335,252)
        self.bank1.setObjectName("BATTERY1")
        self.bank1.show()

        self.bank2 = BatteryBoxIcon("BESS BANK-2")
        self.bank2.setParent(self)
        self.bank2.move(626,273)
        self.bank2.setObjectName("BATTERY2")
        self.bank2.show()

        self.bank3 = BatteryBoxIcon("BESS BANK-3")
        self.bank3.setParent(self)
        self.bank3.move(787,273)
        self.bank3.setObjectName("BATTERY3")
        self.bank3.show()

        self.bank4 = BatteryBoxIcon("BESS BANK-4")
        self.bank4.setParent(self)
        self.bank4.move(950,277)
        self.bank4.setObjectName("BATTERY4")
        self.bank4.show()

        self.pcs1 = PCSWidget("PCS-1")
        self.pcs1.setParent(self)
        self.pcs1.move(395,144)
        self.pcs1.setObjectName("PCS1")
        self.pcs1.show()

        self.pcs2 = PCSWidget("PCS-2")
        self.pcs2.setParent(self)
        self.pcs2.move(700, 170)
        self.pcs2.setObjectName("PCS2")
        self.pcs2.show()

        self.pcs3 = PCSWidget("PCS-3")
        self.pcs3.setParent(self)
        self.pcs3.move(836, 174)
        self.pcs3.setObjectName("PCS3")
        self.pcs3.show()

        self.pcs4 = PCSWidget("PCS-4")
        self.pcs4.setParent(self)
        self.pcs4.move(1014,169)
        self.pcs4.setObjectName("PCS4")
        self.pcs4.show()

        # PCS POWER DELTA

        self.pcs1Arrow = PCSPowerDelta()
        self.pcs1Arrow.setParent(self)
        self.pcs1Arrow.move(400, 100)
        self.pcs1Arrow.show()

        self.pcs2Arrow = PCSPowerDelta()
        self.pcs2Arrow.setParent(self)
        self.pcs2Arrow.move(705, 126)
        self.pcs2Arrow.show()

        self.pcs3Arrow = PCSPowerDelta()
        self.pcs3Arrow.setParent(self)
        self.pcs3Arrow.move(841, 130)
        self.pcs3Arrow.show()

        self.pcs4Arrow = PCSPowerDelta()
        self.pcs4Arrow.setParent(self)
        self.pcs4Arrow.move(1019, 125)
        self.pcs4Arrow.show()

    def set_main_bus_power(self, power):
        try:
            if power is None:
                # Modbus/Grid data unavailable
                self.main_bus_color = QColor("#D8A100")  # YELLOW
            else:
                power = float(power)
                if power == 0:
                    self.main_bus_color = QColor("#E23C3C")  # RED
                elif power > 0:
                    self.main_bus_color = QColor("#42C84B")  # GREEN
                else:
                    self.main_bus_color = QColor("#D8A100")  # YELLOW
            self.update()
        except (TypeError, ValueError):
            self.main_bus_color = QColor("#D8A100")  # YELLOW
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

        for line in self.verticalLines:
            if line["name"] == "INV2_DROP":
                # PCS-1
                p.setPen(QPen(self.pcs1_bus_color, 3))
            elif line["name"] in ["INV3_DROP", "BUS_DROP2"]:
                # PCS-2
                p.setPen(QPen(self.pcs2_bus_color, 3))
            elif line["name"] in ["INV4_DROP", "BUS_DROP1"]:
                # PCS-3
                p.setPen(QPen(self.pcs3_bus_color, 3))
            elif line["name"] == "INV6_DROP":
                # PCS-4
                p.setPen(QPen(self.pcs4_bus_color, 3))
            else:
                p.setPen(QPen(QColor("#D3A000"), 3))
            p.drawLine(
                line["x"],
                line["y"],
                line["x"],
                line["y"] + line["h"],
            )

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
            if hline["name"] == "INV3_OUT":
                # PCS-2
                p.setPen(QPen(self.pcs2_bus_color, 3))
            elif hline["name"] == "INV4_OUT":
                # PCS-3
                p.setPen(QPen(self.pcs3_bus_color, 3))
            elif hline["name"] == "INV5_OUT":
                # PCS-4
                p.setPen(QPen(self.pcs4_bus_color, 3))
            else:
                p.setPen(QPen(QColor("#D3A000"), 3))
            p.drawLine(
                hline["x"],
                hline["y"],
                hline["x"] + hline["w"],
                hline["y"],
            )

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

        # ================= GREEN POWER FLOW LINE =================

        greenPen = QPen(QColor("#42C84B"), 2)
        p.setPen(greenPen)

        p.drawLine(
            self.greenLine["x"],
            self.greenLine["y"],
            self.greenLine["x"] + self.greenLine["length"],
            self.greenLine["y"],
        )

        arrow = QPolygon([
            QPoint(self.greenLine["x"] + self.greenLine["length"], self.greenLine["y"]),
            QPoint(self.greenLine["x"] + self.greenLine["length"] - 8, self.greenLine["y"] - 4),
            QPoint(self.greenLine["x"] + self.greenLine["length"] - 8, self.greenLine["y"] + 4),
        ])

        p.setBrush(QColor("#42C84B"))
        p.setPen(Qt.NoPen)
        p.drawPolygon(arrow)

    def mousePressEvent(self, e):
        # Disabled mouse press handling to keep layout positions fixed
        pass

    def mouseMoveEvent(self, e):
        # Disabled mouse move handling to keep layout positions fixed
        pass

    def mouseReleaseEvent(self, e):
        # Disabled mouse release handling to keep layout positions fixed
        pass


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

        self.live_timer = QTimer(self)

        self.previous_pcs_power = {
            1: None,
            2: None,
            3: None,
            4: None,
        }

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
        }

        bank_widgets = {
            1: self.canvas.bank1,
            2: self.canvas.bank2,
            3: self.canvas.bank3,
            4: self.canvas.bank4,
        }

        # ==================================================
        # PCS + BESS LIVE DATA
        # ==================================================

        for unit_id, widget in pcs_widgets.items():

            try:

                pcs_id = f"PCS{unit_id}"
                db = plant_db.device(pcs_id)
                data = {
                    "soc": db.value(Tags.Battery.SOC),
                    "stored_energy": db.value(
                        Tags.Battery.STORED_ENERGY
                    ),
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
                    "ac_voltage": db.value(
                        Tags.PCS.AC_VOLTAGE
                    ),
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
                    fault_code=data["fault_code"]
                )

                
                # PCS ACTIVE POWER

                current_power_kw = float(
                    data["active_power"]
                )

                previous_power_kw = self.previous_pcs_power[
                    unit_id
                ]

                # First reading
                if previous_power_kw is None:

                    delta_power_mw = 0.0

                else:

                    delta_power_mw = (
                        current_power_kw
                        - previous_power_kw
                    ) / 1000.0

                # Save current value
                self.previous_pcs_power[
                    unit_id
                ] = current_power_kw

                
                # UPDATE CORRESPONDING PCS ARROW
                

                arrow_widgets = {

                    1: self.canvas.pcs1Arrow,

                    2: self.canvas.pcs2Arrow,

                    3: self.canvas.pcs3Arrow,

                    4: self.canvas.pcs4Arrow,
                }

                arrow_widgets[unit_id].set_value(
                    delta_power_mw
                )

                # BESS BANK
                try:

                    bank_widgets[unit_id].update_data(
                        soc=data["soc"],
                        stored_energy_kwh=data["stored_energy"],
                        battery_voltage=data.get("battery_voltage"),
                        temperature=data.get("temperature"),
                        power_kw=data.get("power"),
                    )

                except Exception:
                    pass

            except Exception as e:

                print(
                    f"PCS{unit_id} ERROR:",
                    e
                )

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
                "load_power": grid_db.value(
                    Tags.Network.LOAD_POWER
                ),
            }

            print(
                "GRID LIVE:",
                grid_data
            )

            self.canvas.grid.update_data(
                grid_voltage=grid_data["grid_voltage"],
                import_power=grid_data["import_power"],
                export_power=grid_data["export_power"],
                frequency=grid_data["frequency"],
            )

            self.canvas.factory.update_data(
                load_power=grid_data["load_power"]
            )

            # ================= MAIN BUS STATUS =================
            self.canvas.set_main_bus_power(
                grid_data.get("load_power")
            )

        except Exception as e:

            print(
                "GRID ERROR:",
                e
            )
            self.canvas.set_main_bus_power(None)
