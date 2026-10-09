import sys

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
)

from core.simulator import Simulator

from runtime.build_simulation import build_simulation
from runtime.start_modbus_server import start_modbus_server

from ui.configuration_dialog import ConfigurationDialog
from ui.main_window import MainWindow


def start_backend():
    simulator = Simulator()

    topology, net, simulator = build_simulation(
        simulator,
        "plant/plant.yaml",
    )

    start_modbus_server(simulator)

    return net,simulator

def main():
    # ==================================================
    # QT APPLICATION
    # ==================================================
    app = QApplication(sys.argv)

    # ==================================================
    # CONFIGURATION SELECTION
    # ==================================================
    configuration_dialog = ConfigurationDialog()
    if configuration_dialog.exec() != QDialog.Accepted:
        sys.exit(0)

    configuration = configuration_dialog.get_configuration()

    # ==================================================
    # START BACKEND ONLY FOR BUILT-IN
    # ==================================================
    net = None
    if configuration == "builtin":
        net = start_backend()

    # ==================================================
    # MAIN WINDOW
    # ==================================================
    window = MainWindow(
        network_manager=net,
        custom_mode=(configuration == "custom"),
        backend_factory=start_backend,
    )
    window.showMaximized()
    sys.exit(
        app.exec()
    )

if __name__ == "__main__":

    main()