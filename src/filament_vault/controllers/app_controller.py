"""Application Controller.

Coordinates Application lifecycle, models, repositories, and window initialization.
"""

from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from ..core.logger import setup_logger, get_logger
from ..core.config import get_user_data_dir, get_bambu_default_spools_path
from ..models.inventory_repo import InventoryRepository
from ..models.metadata_store import MetadataStore
from ..views.main_window import MainWindow

logger = get_logger("app_controller")


class AppController:
    """MVC Controller orchestrating application run."""

    def __init__(self) -> None:
        self.user_data_dir = get_user_data_dir()
        setup_logger(log_dir=self.user_data_dir)
        logger.info("Initializing Filament Vault Controller...")

        # Models & Repositories
        self.metadata_store = MetadataStore(self.user_data_dir)

        # Check if custom path was configured in user settings
        saved_path_str = self.metadata_store.get_setting("bambu_spools_path")
        spools_path = Path(saved_path_str) if saved_path_str else get_bambu_default_spools_path()

        self.inventory_repo = InventoryRepository(spools_path)

        # View
        self.window = MainWindow(self.inventory_repo, self.metadata_store)

    def run(self) -> int:
        """Show window and run application loop."""
        self.window.show()
        return 0
