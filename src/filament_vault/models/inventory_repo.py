"""Bambu Studio Inventory Reader and Synchronizer.

Strictly READ-ONLY access to:
  %APPDATA%/BambuStudio/filament_inventory/spools.json

Guarantees:
- Never overwrite
- Never modify
- Never reformat
- Never write metadata into the Bambu Studio file
- Automatic file change monitoring (QFileSystemWatcher)
- Resilient error handling if file is missing, empty, or corrupted
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple, Callable
from PySide6.QtCore import QObject, Signal, QFileSystemWatcher, QTimer

from ..core.logger import get_logger
from ..core.config import get_bambu_default_spools_path
from .spool import Spool

logger = get_logger("inventory_repo")


class InventoryRepository(QObject):
    """Manages read-only synchronization of Bambu Studio filament inventory."""

    inventory_updated = Signal(list)  # Emits List[Spool]
    sync_error = Signal(str)  # Emits error message

    def __init__(self, spools_path: Optional[Path] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._path: Path = spools_path or get_bambu_default_spools_path()
        self._spools: List[Spool] = []
        self._last_mtime: float = 0.0

        # File watcher for auto-refresh
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)

        # Debounce timer for file modification events
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(600)  # 600ms debounce
        self._debounce_timer.timeout.connect(self.reload)

        self._setup_watcher()

    @property
    def current_path(self) -> Path:
        return self._path

    def set_path(self, new_path: Path) -> None:
        """Update inventory file location and reload."""
        if self._watcher.files():
            self._watcher.removePaths(self._watcher.files())
        self._path = new_path
        self._setup_watcher()
        self.reload()

    def _setup_watcher(self) -> None:
        """Add current path to QFileSystemWatcher if file exists."""
        if self._path.exists() and self._path.is_file():
            self._watcher.addPath(str(self._path.resolve()))
            logger.info(f"Watching inventory file for live changes: {self._path}")

    def _on_file_changed(self, path_str: str) -> None:
        """Triggered by QFileSystemWatcher when Bambu Studio saves spools.json."""
        logger.info(f"Detected external modification to {path_str}")
        # Note: In Windows, when Bambu Studio re-writes files, the watcher path might need to be re-added
        if str(self._path.resolve()) not in self._watcher.files() and self._path.exists():
            self._watcher.addPath(str(self._path.resolve()))
        self._debounce_timer.start()

    def get_spools(self) -> List[Spool]:
        """Return current in-memory spool list."""
        return list(self._spools)

    def reload(self) -> Tuple[bool, str]:
        """Read spools.json strictly in read-only mode and parse."""
        if not self._path.exists():
            msg = f"Bambu Studio inventory file not found at: {self._path}"
            logger.warning(msg)
            self.sync_error.emit(msg)
            return False, msg

        try:
            mtime = self._path.stat().st_mtime
            # Read strictly with 'r' mode and utf-8 encoding
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_spools = []
            if isinstance(data, dict):
                # Standard Bambu Studio format: {"spools": [...]}
                if "spools" in data and isinstance(data["spools"], list):
                    raw_spools = data["spools"]
                elif "filament_list" in data and isinstance(data["filament_list"], list):
                    raw_spools = data["filament_list"]
                else:
                    # In case keys are spool_ids
                    for val in data.values():
                        if isinstance(val, dict) and ("material_type" in val or "color_code" in val):
                            raw_spools.append(val)
            elif isinstance(data, list):
                raw_spools = data

            parsed_spools = [Spool.from_dict(item) for item in raw_spools if isinstance(item, dict)]
            self._spools = parsed_spools
            self._last_mtime = mtime
            logger.info(f"Successfully loaded {len(self._spools)} spools from {self._path}")
            self.inventory_updated.emit(self._spools)
            return True, f"Loaded {len(self._spools)} spools successfully."

        except json.JSONDecodeError as jde:
            msg = f"Failed to parse JSON (file may be corrupted or being written): {jde}"
            logger.error(msg)
            self.sync_error.emit(msg)
            return False, msg
        except Exception as e:
            msg = f"Unexpected error reading inventory: {e}"
            logger.error(msg)
            self.sync_error.emit(msg)
            return False, msg
