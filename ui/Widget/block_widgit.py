from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class BlockPanel(QWidget):
    """
    Single BLOCK-1 / BLOCK-2 panel.
    """

    GREEN = QColor("#24D94F")
    BLUE = QColor("#0639D8")
    DEVICE_GREEN = QColor("#00C97A")
    DEVICE_BLUE = QColor("#0839D8")
    TEXT_GREEN = QColor("#00B95C")
    TEXT_BLUE = QColor("#0738D5")

    def __init__(self, block_no=1, parent=None):
        super().__init__(parent)
        self.block_no = block_no
        self.setFixedSize(121, 205)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        stack_no = self.block_no

        devices = [
            ("spare", self.DEVICE_BLUE, "SPARE"),
            (
                "series_block_panel",
                self.DEVICE_BLUE,
                "SERVICE BLOCK",
            ),
            (
                "stack_panel",
                self.DEVICE_GREEN,
                f"EV STACK PANEL",
            ),
            (
                "cooling_tower",
                self.DEVICE_BLUE,
                "COOLING TOWER",
            ),
            (
                "chiller",
                self.DEVICE_GREEN,
                "MT-CHILLER PH-1\nC1:2988MW",
            ),
        ]

        p.setPen(QPen(QColor("#111111"), 2))
        box_x = 15
        box_w = self.width() - box_x - 5
        box_h = 18
        first_box_y = 5
        last_box_y = self.height() - 44
        row_spacing = (
            (last_box_y - first_box_y) / (len(devices) - 1)
            if len(devices) > 1
            else 0
        )

        for index, (key, border_color, label) in enumerate(devices):
            box_y = round(first_box_y + index * row_spacing)

            # Arrow points horizontally into each device row.
            arrow_y = box_y + box_h // 2
            p.setPen(QPen(QColor("#111111"), 2))
            p.drawLine(3, arrow_y, box_x - 2, arrow_y)
            p.drawLine(box_x - 2, arrow_y, box_x - 7, arrow_y - 4)
            p.drawLine(box_x - 2, arrow_y, box_x - 7, arrow_y + 4)

            p.setPen(QPen(border_color, 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(box_x, box_y, box_w, box_h, 4, 4)

            text_color = (
                self.TEXT_GREEN
                if border_color == self.DEVICE_GREEN
                else self.TEXT_BLUE
            )

            font = QFont("Arial", 6)
            font.setBold(True)
            p.setFont(font)
            p.setPen(text_color)
            text_rect = QRect(box_x + 3, box_y + 1, box_w - 6, box_h - 2)
            p.drawText(
                text_rect,
                Qt.AlignCenter,
                label,
            )

            value = self.box_values[key]
            try:
                value_text = f"{float(value):.2f} kW"
            except (TypeError, ValueError):
                value_text = f"{value or 'N/A'} kW"
            value_font = QFont("Arial", 5)
            p.setFont(value_font)
            p.setPen(QColor("#526170"))
            p.drawText(
                QRect(
                    box_x,
                    box_y + box_h,
                    box_w,
                    max(1, round(row_spacing) - box_h),
                ),
                Qt.AlignCenter,
                value_text,
            )

        # Requested label text and red styling instead of BLOCK-1 / BLOCK-2
        font = QFont("Arial", 5)
        font.setBold(False)
        p.setFont(font)
        p.setPen(QColor("#E24A32"))
        p.drawText(
            0,
            self.height() - 9,
            self.width(),
            9,
            Qt.AlignCenter,
            "MAIN LT PANEL-1" if self.block_no == 1 else "MAIN LT PANEL-2",
        )

class BlockWidget(BlockPanel):
    def __init__(self, block_no=1, parent=None):
        super().__init__(block_no=block_no, parent=parent)
        self.box_values = {
            "spare": None,
            "series_block_panel": None,
            "stack_panel": None,
            "cooling_tower": None,
            "chiller": None,
        }

    def set_box_values(self, values):
        self.box_values.update(values)
        self.update()
