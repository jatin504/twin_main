from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

from common.enums import PCSState


class PCSWidget(QWidget):

    def __init__(
        self,
        title,
        mw="0.00 MW",
        mvar="0.00 MVAr",
        pf="PF 1.00",
    ):
        super().__init__()

        self.setFixedSize(90, 70)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        self.titleLbl = QLabel(title)

        self.titleLbl.setStyleSheet("""
        QLabel{
            font-size:9px;
            font-weight:700;
            color:#30343B;
        }
        """)

        # --------------------------------------------------
        # Active Power
        # --------------------------------------------------

        self.mwLbl = QLabel(mw)

        self.mwLbl.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        # --------------------------------------------------
        # Reactive Power
        # --------------------------------------------------

        self.mvarLbl = QLabel(mvar)

        self.mvarLbl.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        # --------------------------------------------------
        # Power Factor
        # --------------------------------------------------

        self.pfLbl = QLabel(pf)

        self.pfLbl.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        self.lbl_voltage = QLabel("0.00V")
        
        self.lbl_voltage.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        self.fault_code = QLabel("—")  # Existing label now displays the live PCS state.

        self.fault_code.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        self.previous_power_kw = None

        power_row = QWidget(self)
        power_row.setAttribute(Qt.WA_TranslucentBackground)
        power_layout = QHBoxLayout(power_row)
        power_layout.setContentsMargins(0, 0, 0, 0)
        power_layout.setSpacing(4)

        self.delta_arrow = QLabel("•")
        self.delta_arrow.setStyleSheet("""
        QLabel{
            font-size:10px;
            font-weight:700;
            color:#6B7280;
        }
        """)

        self.delta_value = QLabel("0.00 kW")
        self.delta_value.setStyleSheet("""
        QLabel{
            font-size:8px;
            font-weight:700;
            color:#6B7280;
        }
        """)

        power_layout.addWidget(self.mwLbl)
        power_layout.addWidget(self.delta_arrow)
        power_layout.addWidget(self.delta_value)
        power_layout.addStretch()

        layout.addWidget(self.titleLbl)
        layout.addWidget(power_row)
        # layout.addWidget(self.mvarLbl)
        # layout.addWidget(self.pfLbl)
        layout.addWidget(self.lbl_voltage)
        layout.addWidget(self.fault_code)

    
    # LIVE DATA UPDATE
    

    def update_data(
        self,
        power_kw,
        mvar=None,
        pf=None,
        ac_voltage=None,
        fault_code=None,
        pcs_state=None,
    ):

        # --------------------------------------------------
        # Backend Active Power is currently read as kW
        # Convert kW -> MW for UI
        # --------------------------------------------------

        try:
            power_value = float(power_kw)
        except (TypeError, ValueError):
            power_value = 0.0

        if self.previous_power_kw is not None:
            delta_kw = power_value - self.previous_power_kw
            if delta_kw > 0:
                self.delta_arrow.setText("▲")
                self.delta_arrow.setStyleSheet("""
                QLabel{
                    font-size:10px;
                    font-weight:700;
                    color:#22C55E;
                }
                """)
                self.delta_value.setText(f"+{delta_kw:.2f} kW")
                self.delta_value.setStyleSheet("""
                QLabel{
                    font-size:8px;
                    font-weight:700;
                    color:#22C55E;
                }
                """)
            elif delta_kw < 0:
                self.delta_arrow.setText("▼")
                self.delta_arrow.setStyleSheet("""
                QLabel{
                    font-size:10px;
                    font-weight:700;
                    color:#EF4444;
                }
                """)
                self.delta_value.setText(f"{delta_kw:.2f} kW")
                self.delta_value.setStyleSheet("""
                QLabel{
                    font-size:8px;
                    font-weight:700;
                    color:#EF4444;
                }
                """)
            else:
                self.delta_arrow.setText("•")
                self.delta_arrow.setStyleSheet("""
                QLabel{
                    font-size:10px;
                    font-weight:700;
                    color:#6B7280;
                }
                """)
                self.delta_value.setText("0.00 kW")
                self.delta_value.setStyleSheet("""
                QLabel{
                    font-size:8px;
                    font-weight:700;
                    color:#6B7280;
                }
                """)
        else:
            self.delta_arrow.setText("•")
            self.delta_arrow.setStyleSheet("""
            QLabel{
                font-size:10px;
                font-weight:700;
                color:#6B7280;
            }
            """)
            self.delta_value.setText("0.00 kW")
            self.delta_value.setStyleSheet("""
            QLabel{
                font-size:8px;
                font-weight:700;
                color:#6B7280;
            }
            """)

        self.previous_power_kw = power_value

        self.mwLbl.setText(
            f"{power_value:.2f} kW"
        )

        # --------------------------------------------------
        # MVAr
        #
        # Currently not available in Modbus mapping.
        # Therefore keep existing UI value unless supplied.
        # --------------------------------------------------

        if mvar is not None:

            self.mvarLbl.setText(
                f"{mvar:.2f} MVAr"
            )

        # --------------------------------------------------
        # Power Factor
        #
        # Currently not available in Modbus mapping.
        # Therefore keep existing UI value unless supplied.
        # --------------------------------------------------

        if pf is not None:

            self.pfLbl.setText(
                f"PF {pf:.2f}"
            )

        # AC Voltage
        if ac_voltage is not None:
        
            self.lbl_voltage.setText(
                f"{ac_voltage:.2f}V"
            )

        # Display the PCS operating state in the existing bottom label.
        if pcs_state is not None:
            try:
                state_name = PCSState(pcs_state).name
            except (TypeError, ValueError):
                state_name = "UNKNOWN"
            self.fault_code.setText(state_name)
            self.fault_code.setToolTip(state_name)