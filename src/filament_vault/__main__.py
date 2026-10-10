"""Filament Vault Entry Point."""

from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from filament_vault.controllers.app_controller import AppController


def main() -> int:
    """Launch Filament Vault desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Filament Vault")
    app.setOrganizationName("FilamentVault")

    controller = AppController()
    controller.run()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
