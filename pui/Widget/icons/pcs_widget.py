from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from common.enums import FaultCode


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

        self.fault_code = QLabel("0")
        
        self.fault_code.setStyleSheet("""
        QLabel{
            font-size:8px;
            color:#30343B;
        }
        """)

        layout.addWidget(self.titleLbl)
        layout.addWidget(self.mwLbl)
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
    ):

        # --------------------------------------------------
        # Backend Active Power is currently read as kW
        # Convert kW -> MW for UI
        # --------------------------------------------------

        power_mw = power_kw

        self.mwLbl.setText(
            f"{power_mw:.2f} kW"
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

        # AC Voltage
        if fault_code is not None:
        
            self.fault_code.setText(
                f"{FaultCode(fault_code).name}"
            )