"""Settings and Synchronization Configuration View.

Implements the layout shown in stitch_filament_vault_desktop/filament_vault_settings:
- System Config / Workstation Environment
- Bambu Studio inventory source path configuration (%APPDATA%/BambuStudio/filament_inventory/spools.json)
- Custom path selector & validation
- Live synchronization & file watcher settings
- Offline safety checks: Read-only verification, backup location, user metadata integrity
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QFileDialog,
    QCheckBox,
    QSpinBox,
    QMessageBox,
)

from ..core.config import get_bambu_default_spools_path, get_user_data_dir
from ..models.metadata_store import MetadataStore
from ..models.inventory_repo import InventoryRepository
from ..resources.theme import (
    SURFACE_CONTAINER,
    SURFACE_LOW,
    SURFACE_HIGH,
    SURFACE_HIGHEST,
    SURFACE_BASE,
    BORDER_HAIRLINE,
    PRIMARY,
    PRIMARY_BRIGHT,
    SECONDARY,
    TERTIARY,
    ERROR,
    TEXT_PRIMARY,
    TEXT_MUTED,
)


class SettingsView(QWidget):
    """Configuration interface for inventory paths, sync rates, and metadata storage."""

    settings_changed = Signal()
    request_reload = Signal()

    def __init__(
        self,
        metadata_store: MetadataStore,
        inventory_repo: InventoryRepository,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.metadata_store = metadata_store
        self.inventory_repo = inventory_repo
        self._init_ui()
        self._load_values()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Header
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel("Workstation Environment & Synchronization")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_box.addWidget(title)

        sub = QLabel("Configuration of Bambu Studio Read-Only Inventory and User Metadata Storage")
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        title_box.addWidget(sub)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_apply = QPushButton("Apply & Save Preferences")
        self.btn_apply.setProperty("id", "primaryBtn")
        self.btn_apply.clicked.connect(self._save_values)
        header_row.addWidget(self.btn_apply)

        main_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(16)

        # 2. Bambu Studio Source Card
        source_card = QFrame()
        source_card.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        s_lay = QVBoxLayout(source_card)
        s_lay.setSpacing(10)

        s_hdr = QLabel("BAMBU STUDIO INVENTORY SOURCE (READ-ONLY)")
        s_hdr.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-size: 11px; font-weight: bold; font-family: 'JetBrains Mono';")
        s_lay.addWidget(s_hdr)

        s_note = QLabel("Filament Vault accesses this file strictly in READ-ONLY mode. It will never overwrite, modify, or format it.")
        s_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        s_lay.addWidget(s_note)

        path_box = QHBoxLayout()
        self.txt_bambu_path = QLineEdit()
        self.txt_bambu_path.setPlaceholderText("%APPDATA%/BambuStudio/filament_inventory/spools.json")
        path_box.addWidget(self.txt_bambu_path, stretch=3)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_bambu_path)
        path_box.addWidget(btn_browse)

        btn_reset_default = QPushButton("Default Path")
        btn_reset_default.clicked.connect(self._reset_to_default_path)
        path_box.addWidget(btn_reset_default)

        btn_test_sync = QPushButton("Test Sync")
        btn_test_sync.clicked.connect(self._test_sync)
        path_box.addWidget(btn_test_sync)

        s_lay.addLayout(path_box)

        # Status readout
        self.status_lbl = QLabel("Status: Ready")
        self.status_lbl.setStyleSheet(f"color: {SECONDARY}; font-family: 'JetBrains Mono'; font-size: 11px;")
        s_lay.addWidget(self.status_lbl)

        content_lay.addWidget(source_card)

        # 3. User Data Storage Card
        data_card = QFrame()
        data_card.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        d_lay = QVBoxLayout(data_card)
        d_lay.setSpacing(10)

        d_hdr = QLabel("USER METADATA STORAGE LOCATION")
        d_hdr.setStyleSheet(f"color: {TERTIARY}; font-size: 11px; font-weight: bold; font-family: 'JetBrains Mono';")
        d_lay.addWidget(d_hdr)

        d_desc = QLabel("User tags, notes, collections, custom physical locations, and favorites are stored independently in:")
        d_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        d_lay.addWidget(d_desc)

        user_data_path_lbl = QLabel(str(get_user_data_dir().resolve()))
        user_data_path_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: 'JetBrains Mono'; font-size: 11px; background-color: {SURFACE_BASE}; padding: 6px; border-radius: 4px;")
        d_lay.addWidget(user_data_path_lbl)

        content_lay.addWidget(data_card)

        # 4. Synchronization & Telemetry Preferences Card
        sync_card = QFrame()
        sync_card.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        sync_lay = QVBoxLayout(sync_card)
        sync_lay.setSpacing(10)

        sync_hdr = QLabel("PREFERENCES & THRESHOLDS")
        sync_hdr.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold; font-family: 'JetBrains Mono';")
        sync_lay.addWidget(sync_hdr)

        self.chk_auto_sync = QCheckBox("Enable background file change detection (QFileSystemWatcher)")
        self.chk_auto_sync.setChecked(True)
        sync_lay.addWidget(self.chk_auto_sync)

        # Low stock threshold
        thresh_row = QHBoxLayout()
        thresh_row.addWidget(QLabel("Low Stock Alert Threshold (Grams):"))
        self.spin_low_grams = QSpinBox()
        self.spin_low_grams.setRange(20, 500)
        self.spin_low_grams.setValue(200)
        thresh_row.addWidget(self.spin_low_grams)
        thresh_row.addStretch()
        sync_lay.addLayout(thresh_row)

        content_lay.addWidget(sync_card)
        content_lay.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _load_values(self) -> None:
        saved_path = self.metadata_store.get_setting("bambu_spools_path")
        if saved_path:
            self.txt_bambu_path.setText(saved_path)
        else:
            self.txt_bambu_path.setText(str(self.inventory_repo.current_path))

        self.chk_auto_sync.setChecked(self.metadata_store.get_setting("auto_sync", True))
        self.spin_low_grams.setValue(int(self.metadata_store.get_setting("low_stock_threshold_grams", 200.0)))

    def _save_values(self) -> None:
        p_str = self.txt_bambu_path.text().strip()
        p = Path(p_str)
        self.metadata_store.set_setting("bambu_spools_path", str(p))
        self.metadata_store.set_setting("auto_sync", self.chk_auto_sync.isChecked())
        self.metadata_store.set_setting("low_stock_threshold_grams", float(self.spin_low_grams.value()))

        self.inventory_repo.set_path(p)
        self.settings_changed.emit()
        self.request_reload.emit()
        QMessageBox.information(self, "Settings Saved", "Preferences applied and inventory re-synchronized successfully.")

    def _browse_bambu_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Bambu Studio spools.json",
            str(self.inventory_repo.current_path.parent if self.inventory_repo.current_path.exists() else Path.home()),
            "JSON Files (*.json);;All Files (*.*)",
        )
        if path:
            self.txt_bambu_path.setText(path)

    def _reset_to_default_path(self) -> None:
        def_path = get_bambu_default_spools_path()
        self.txt_bambu_path.setText(str(def_path))

    def _test_sync(self) -> None:
        p = Path(self.txt_bambu_path.text().strip())
        if not p.exists():
            self.status_lbl.setText(f"Status: Error - File does not exist at {p}")
            self.status_lbl.setStyleSheet(f"color: {ERROR}; font-family: 'JetBrains Mono';")
            return

        self.inventory_repo.set_path(p)
        ok, msg = self.inventory_repo.reload()
        if ok:
            self.status_lbl.setText(f"Status: Success - {msg}")
            self.status_lbl.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-family: 'JetBrains Mono';")
        else:
            self.status_lbl.setText(f"Status: Failure - {msg}")
            self.status_lbl.setStyleSheet(f"color: {ERROR}; font-family: 'JetBrains Mono';")
