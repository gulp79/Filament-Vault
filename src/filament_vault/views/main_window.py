"""Main Application Window.

Implements the unified desktop layout defined in the Stitch mockups:
- Fixed Top Navigation Header (Traffic lights, Brand icon, Version badge, Global Search Ctrl+K, AMS Hub telemetry pill)
- Left Workspace Explorer Sidebar (Dashboard, Inventory Explorer, Color Explorer, Spool Details, Analytics, Settings, and Bottom AMS Mini-Matrix)
- Central Fluid Multi-View Stage (QStackedWidget)
- Bottom Technical Status Bar
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QStackedWidget,
    QFrame,
    QStatusBar,
    QButtonGroup,
)

from ..core.logger import get_logger
from ..models.spool import Spool
from ..models.inventory_repo import InventoryRepository
from ..models.metadata_store import MetadataStore
from .dashboard_view import DashboardView
from .inventory_view import InventoryExplorerView
from .color_view import ColorExplorerView
from .spool_details_view import SpoolDetailsView
from .analytics_view import AnalyticsView
from .settings_view import SettingsView
from ..resources.theme import (
    APP_STYLESHEET,
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

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """Filament Vault Desktop Application Window."""

    def __init__(
        self,
        inventory_repo: InventoryRepository,
        metadata_store: MetadataStore,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.inventory_repo = inventory_repo
        self.metadata_store = metadata_store

        self.setWindowTitle("Filament Vault - Advanced Bambu Studio Inventory Explorer")
        self.resize(1340, 840)
        self.setMinimumSize(1024, 680)

        self.setStyleSheet(APP_STYLESHEET)
        self._init_ui()
        self._connect_signals()

        # Initial load
        self.inventory_repo.reload()

    def _init_ui(self) -> None:
        # Central Root Widget
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Fixed Top Application Header
        self.header_bar = self._create_header_bar()
        root_layout.addWidget(self.header_bar)

        # 2. Main Horizontal Workspace Split (Sidebar + Central Stack)
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # Left Sidebar
        self.sidebar = self._create_sidebar()
        workspace_layout.addWidget(self.sidebar)

        # Central Stacked Views
        self.stack = QStackedWidget()

        # View 0: Dashboard
        self.dashboard_view = DashboardView()
        self.stack.addWidget(self.dashboard_view)

        # View 1: Inventory Explorer
        self.inventory_view = InventoryExplorerView(self.metadata_store)
        self.stack.addWidget(self.inventory_view)

        # View 2: Color Explorer
        self.color_view = ColorExplorerView()
        self.stack.addWidget(self.color_view)

        # View 3: Spool Details
        self.spool_details_view = SpoolDetailsView(self.metadata_store)
        self.stack.addWidget(self.spool_details_view)

        # View 4: Analytics
        self.analytics_view = AnalyticsView()
        self.stack.addWidget(self.analytics_view)

        # View 5: Settings
        self.settings_view = SettingsView(self.metadata_store, self.inventory_repo)
        self.stack.addWidget(self.settings_view)

        workspace_layout.addWidget(self.stack, stretch=1)
        root_layout.addLayout(workspace_layout)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar_lbl = QLabel("Ready • Read-Only Bambu Studio Synced")
        self.status_bar.addWidget(self.status_bar_lbl)

    def _create_header_bar(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(42)
        hdr.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_BASE};
                border-bottom: 1px solid {BORDER_HAIRLINE};
                padding: 0 12px;
            }}
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(16)

        # Traffic lights (decorative CAD aesthetic)
        dots = QHBoxLayout()
        dots.setSpacing(6)
        for c in [ERROR, PRIMARY_BRIGHT, SECONDARY]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background-color: {c}; border-radius: 5px;")
            dots.addWidget(dot)
        lay.addLayout(dots)

        # Title & Version Badge
        title_box = QHBoxLayout()
        title_box.setSpacing(8)

        app_icon = QLabel("◆")
        app_icon.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-size: 14px;")
        title_box.addWidget(app_icon)

        title_lbl = QLabel("FILAMENT VAULT")
        title_lbl.setStyleSheet("font-weight: bold; font-family: 'JetBrains Mono'; font-size: 13px; letter-spacing: 1px;")
        title_box.addWidget(title_lbl)

        ver_badge = QLabel("v2.4.0")
        ver_badge.setStyleSheet(f"background-color: {SURFACE_HIGH}; color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 10px; padding: 1px 4px; border-radius: 2px;")
        title_box.addWidget(ver_badge)
        lay.addLayout(title_box)

        # Global Search Ctrl+K
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search spools, NFC tags, materials... (Ctrl+K)")
        self.global_search.setFixedWidth(320)
        self.global_search.returnPressed.connect(self._on_global_search)
        lay.addWidget(self.global_search)

        lay.addStretch()

        # AMS Hub Status Pill
        self.ams_pill = QLabel("● AMS Hub #1: Connected • 4 Slots Ready")
        self.ams_pill.setStyleSheet(f"""
            background-color: {SURFACE_CONTAINER};
            color: {PRIMARY_BRIGHT};
            border: 1px solid {BORDER_HAIRLINE};
            border-radius: 4px;
            padding: 4px 8px;
            font-family: 'JetBrains Mono';
            font-size: 11px;
        """)
        lay.addWidget(self.ams_pill)

        # Refresh button
        btn_refresh = QPushButton("Sync ↺")
        btn_refresh.setToolTip("Refresh Bambu Studio inventory")
        btn_refresh.clicked.connect(self.inventory_repo.reload)
        lay.addWidget(btn_refresh)

        # Ctrl+K Shortcut Action
        shortcut = QAction(self)
        shortcut.setShortcut(QKeySequence("Ctrl+K"))
        shortcut.triggered.connect(self.global_search.setFocus)
        self.addAction(shortcut)

        return hdr

    def _create_sidebar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedWidth(220)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_BASE};
                border-right: 1px solid {BORDER_HAIRLINE};
            }}
        """)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(8, 12, 8, 12)
        lay.setSpacing(6)

        header_lbl = QLabel("WORKSPACE EXPLORER")
        header_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono'; padding-left: 6px;")
        lay.addWidget(header_lbl)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        items = [
            ("Dashboard", 0),
            ("Inventory Explorer", 1),
            ("Color Explorer", 2),
            ("Spool Details", 3),
            ("Analytics", 4),
            ("Settings", 5),
        ]

        for text, idx in items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 8px 12px;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    color: {TEXT_MUTED};
                    background-color: transparent;
                }}
                QPushButton:hover {{
                    background-color: {SURFACE_CONTAINER};
                    color: {TEXT_PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: {SURFACE_HIGH};
                    color: {PRIMARY_BRIGHT};
                    border-left: 2px solid {PRIMARY};
                    font-weight: 600;
                }}
            """)
            self.nav_group.addButton(btn, idx)
            lay.addWidget(btn)
            if idx == 0:
                btn.setChecked(True)

        self.nav_group.idClicked.connect(self._on_nav_clicked)

        lay.addStretch()

        # Bottom AMS Unit mini-telemetry widget
        ams_box = QFrame()
        ams_box.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 4px; padding: 8px;")
        ams_lay = QVBoxLayout(ams_box)
        ams_lay.setContentsMargins(6, 6, 6, 6)
        ams_lay.setSpacing(4)

        ams_hdr = QHBoxLayout()
        ams_hdr.addWidget(QLabel("AMS UNIT 01"))
        opt_lbl = QLabel("Optimal")
        opt_lbl.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-size: 10px; font-family: 'JetBrains Mono';")
        ams_hdr.addWidget(opt_lbl, alignment=Qt.AlignmentFlag.AlignRight)
        ams_lay.addLayout(ams_hdr)

        # 4 slots indicator
        slots_row = QHBoxLayout()
        slots_row.setSpacing(4)
        for s_num in ["A1", "A2", "A3", "A4"]:
            s_box = QLabel(s_num)
            s_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s_box.setStyleSheet(f"background-color: {SURFACE_HIGH}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 2px; font-size: 10px; font-family: 'JetBrains Mono'; padding: 2px;")
            slots_row.addWidget(s_box)
        ams_lay.addLayout(slots_row)

        lay.addWidget(ams_box)
        return bar

    def _connect_signals(self) -> None:
        self.inventory_repo.inventory_updated.connect(self._on_inventory_updated)
        self.inventory_repo.sync_error.connect(self._on_sync_error)

        self.inventory_view.spool_selected.connect(self._show_spool_details)
        self.color_view.spool_selected.connect(self._show_spool_details)
        self.dashboard_view.spool_selected.connect(self._show_spool_details)
        self.analytics_view.spool_selected.connect(self._show_spool_details)

        self.settings_view.request_reload.connect(self.inventory_repo.reload)
        self.spool_details_view.metadata_saved.connect(self._on_metadata_saved)

    def _on_nav_clicked(self, view_id: int) -> None:
        self.stack.setCurrentIndex(view_id)

    def _on_inventory_updated(self, spools: List[Spool]) -> None:
        self.status_bar_lbl.setText(f"Synchronized • {len(spools)} Spools loaded from Bambu Studio (Read-Only)")
        self.dashboard_view.update_data(spools)
        self.inventory_view.set_spools(spools)
        self.color_view.set_spools(spools)
        self.analytics_view.set_spools(spools)

    def _on_sync_error(self, err_msg: str) -> None:
        self.status_bar_lbl.setText(f"Sync Notice: {err_msg}")
        self.status_bar_lbl.setStyleSheet(f"color: {ERROR};")

    def _show_spool_details(self, spool_id: str) -> None:
        # Find spool
        spool = next((s for s in self.inventory_repo.get_spools() if s.spool_id == spool_id), None)
        if spool:
            self.spool_details_view.set_spool(spool)
            # Switch to Spool Details tab (Index 3)
            btn = self.nav_group.button(3)
            if btn:
                btn.setChecked(True)
            self.stack.setCurrentIndex(3)

    def _on_metadata_saved(self, spool_id: str) -> None:
        # Re-apply filters and updates without touching Bambu Studio files
        self.inventory_view.apply_filter()
        self.status_bar_lbl.setText(f"User metadata saved for Spool {spool_id} (stored in user_data/)")

    def _on_global_search(self) -> None:
        query = self.global_search.text().strip()
        if query:
            # Switch to inventory explorer
            btn = self.nav_group.button(1)
            if btn:
                btn.setChecked(True)
            self.stack.setCurrentIndex(1)
            self.inventory_view.search_input.setText(query)
