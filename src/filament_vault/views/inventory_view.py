"""Inventory Explorer View.

Implements:
- Quick View Presets Toolbar (All Spools, Loaded in AMS, Drybox, Low Stock, RFID Synced)
- Parameter Filter Matrix & Omnisearch Strip (Material, Brand, Finish, Mass range slider)
- 4 Multi-view Modes:
    1. Grid View (cards with radial spool graphics)
    2. Table View (high-density telemetric tabular layout)
    3. Shelf View (visually mimics physical filament shelf racks)
    4. Gallery View (large color swatch focus)
- Instant filtering and sorting
"""

from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSlider,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QFrame,
    QButtonGroup,
    QStackedWidget,
)

from ..models.spool import Spool
from ..models.filter_criteria import FilterCriteria
from ..models.metadata_store import MetadataStore
from .widgets import SpoolCardWidget, ShelfSpoolWidget
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


class InventoryExplorerView(QWidget):
    """Multi-view Inventory Explorer featuring Table, Grid, Shelf, and Gallery displays."""

    spool_selected = Signal(str)  # Emits spool_id

    def __init__(self, metadata_store: MetadataStore, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.metadata_store = metadata_store
        self.all_spools: List[Spool] = []
        self.filtered_spools: List[Spool] = []
        self.current_filter = FilterCriteria()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header Toolbar: Summary Counter + View Mode Switchers
        header_bar = QHBoxLayout()
        header_bar.setSpacing(12)

        self.summary_badge = QLabel("64 SPOOLS REGISTERED • 51.24 kg ON-SITE")
        self.summary_badge.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-family: 'JetBrains Mono';
            font-size: 11px;
            font-weight: 600;
        """)
        header_bar.addWidget(self.summary_badge)
        header_bar.addStretch()

        # View Switcher Buttons
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.setExclusive(True)

        self.btn_grid_view = QPushButton("Grid")
        self.btn_table_view = QPushButton("Table")
        self.btn_shelf_view = QPushButton("Shelf")
        self.btn_gallery_view = QPushButton("Gallery")

        for i, btn in enumerate([self.btn_table_view, self.btn_grid_view, self.btn_shelf_view, self.btn_gallery_view]):
            btn.setCheckable(True)
            self.view_btn_group.addButton(btn, i)
            header_bar.addWidget(btn)

        self.btn_table_view.setChecked(True)
        self.view_btn_group.idClicked.connect(self._on_view_mode_changed)

        main_layout.addLayout(header_bar)

        # 2. Quick View Presets Toolbar
        preset_bar = QHBoxLayout()
        preset_bar.setSpacing(8)

        self.preset_btn_group = QButtonGroup(self)
        self.preset_btn_group.setExclusive(True)

        self.preset_all = QPushButton("All Spools")
        self.preset_ams = QPushButton("Loaded in AMS")
        self.preset_low = QPushButton("Low Stock (<20%)")
        self.preset_rfid = QPushButton("Bambu RFID")
        self.preset_fav = QPushButton("Favorites")

        presets = [self.preset_all, self.preset_ams, self.preset_low, self.preset_rfid, self.preset_fav]
        for idx, p in enumerate(presets):
            p.setProperty("class", "presetBtn")
            p.setCheckable(True)
            self.preset_btn_group.addButton(p, idx)
            preset_bar.addWidget(p)

        self.preset_all.setChecked(True)
        self.preset_btn_group.idClicked.connect(self._on_preset_clicked)
        preset_bar.addStretch()
        main_layout.addLayout(preset_bar)

        # 3. Parametric Filter Strip & Omnisearch
        filter_panel = QFrame()
        filter_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_LOW};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(8, 6, 8, 6)
        filter_layout.setSpacing(10)

        # Omnisearch input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter material, hex, brand, RFID, tags... (Ctrl+F)")
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_input, stretch=3)

        # Material Select
        self.material_combo = QComboBox()
        self.material_combo.addItem("Material: All")
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        filter_layout.addWidget(self.material_combo, stretch=1)

        # Brand Select
        self.brand_combo = QComboBox()
        self.brand_combo.addItem("Brand: All")
        self.brand_combo.currentTextChanged.connect(self._on_brand_changed)
        filter_layout.addWidget(self.brand_combo, stretch=1)

        # Mass Slider
        mass_box = QHBoxLayout()
        mass_box.setSpacing(6)
        mass_lbl = QLabel("Mass:")
        mass_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-family: 'JetBrains Mono';")
        mass_box.addWidget(mass_lbl)

        self.mass_slider = QSlider(Qt.Orientation.Horizontal)
        self.mass_slider.setRange(50, 1000)
        self.mass_slider.setValue(1000)
        self.mass_slider.setFixedWidth(80)
        self.mass_slider.valueChanged.connect(self._on_mass_slider_changed)
        mass_box.addWidget(self.mass_slider)

        self.mass_val_lbl = QLabel("≤1000g")
        self.mass_val_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: 'JetBrains Mono'; font-size: 11px;")
        mass_box.addWidget(self.mass_val_lbl)
        filter_layout.addLayout(mass_box)

        # Reset button
        reset_btn = QPushButton("↺")
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip("Reset All Filters")
        reset_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(reset_btn)

        main_layout.addWidget(filter_panel)

        # 4. View Modes Stack (0: Table, 1: Grid, 2: Shelf, 3: Gallery)
        self.view_stack = QStackedWidget()

        # View 0: Table View
        self.table_view = self._create_table_widget()
        self.view_stack.addWidget(self.table_view)

        # View 1: Grid View
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_scroll.setWidget(self.grid_container)
        self.view_stack.addWidget(self.grid_scroll)

        # View 2: Shelf View
        self.shelf_scroll = QScrollArea()
        self.shelf_scroll.setWidgetResizable(True)
        self.shelf_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.shelf_container = QWidget()
        self.shelf_layout = QVBoxLayout(self.shelf_container)
        self.shelf_layout.setSpacing(16)
        self.shelf_scroll.setWidget(self.shelf_container)
        self.view_stack.addWidget(self.shelf_scroll)

        # View 3: Gallery View
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.gallery_container = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_container)
        self.gallery_layout.setSpacing(16)
        self.gallery_scroll.setWidget(self.gallery_container)
        self.view_stack.addWidget(self.gallery_scroll)

        main_layout.addWidget(self.view_stack, stretch=1)

    def _create_table_widget(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Color & Code",
            "Material",
            "Series / Brand",
            "Location / AMS",
            "Net Weight",
            "Remaining %",
            "Length Est.",
            "Tags & Notes",
        ])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        return table

    def set_spools(self, spools: List[Spool]) -> None:
        """Update source spools list and refresh populate options."""
        self.all_spools = spools
        # Populate material and brand dropdowns
        materials = sorted(list({s.material_type for s in spools if s.material_type}))
        brands = sorted(list({s.brand for s in spools if s.brand}))

        curr_mat = self.material_combo.currentText()
        self.material_combo.blockSignals(True)
        self.material_combo.clear()
        self.material_combo.addItem("Material: All")
        for m in materials:
            self.material_combo.addItem(m)
        idx_m = self.material_combo.findText(curr_mat)
        if idx_m >= 0:
            self.material_combo.setCurrentIndex(idx_m)
        self.material_combo.blockSignals(False)

        curr_brand = self.brand_combo.currentText()
        self.brand_combo.blockSignals(True)
        self.brand_combo.clear()
        self.brand_combo.addItem("Brand: All")
        for b in brands:
            self.brand_combo.addItem(b)
        idx_b = self.brand_combo.findText(curr_brand)
        if idx_b >= 0:
            self.brand_combo.setCurrentIndex(idx_b)
        self.brand_combo.blockSignals(False)

        self.apply_filter()

    def apply_filter(self) -> None:
        """Filter self.all_spools through self.current_filter."""
        results = []
        for s in self.all_spools:
            meta = self.metadata_store.get_metadata(s.spool_id)
            if self.current_filter.matches(s, meta):
                results.append(s)
        self.filtered_spools = results

        total_weight_kg = sum(s.remaining_weight_g for s in self.filtered_spools) / 1000.0
        self.summary_badge.setText(
            f"{len(self.filtered_spools)} OF {len(self.all_spools)} SPOOLS • {total_weight_kg:.2f} kg MATCHED"
        )

        self._render_current_view()

    def _render_current_view(self) -> None:
        idx = self.view_stack.currentIndex()
        if idx == 0:
            self._render_table()
        elif idx == 1:
            self._render_grid()
        elif idx == 2:
            self._render_shelf()
        elif idx == 3:
            self._render_gallery()

    def _render_table(self) -> None:
        self.table_view.setRowCount(len(self.filtered_spools))
        for row, s in enumerate(self.filtered_spools):
            meta = self.metadata_store.get_metadata(s.spool_id)

            # Col 0: Color swatch + Hex
            col_item = QTableWidgetItem(f" ■ {s.color_code[:7]}")
            col_item.setForeground(QColor(s.color_code[:7]))
            col_item.setData(Qt.ItemDataRole.UserRole, s.spool_id)
            self.table_view.setItem(row, 0, col_item)

            # Col 1: Material
            self.table_view.setItem(row, 1, QTableWidgetItem(s.material_type))

            # Col 2: Series / Brand
            self.table_view.setItem(row, 2, QTableWidgetItem(f"{s.brand} - {s.series}"))

            # Col 3: Location / AMS
            loc_str = s.tray_id_name or ("AMS" if s.is_ams_loaded else meta.custom_location or "Storage")
            self.table_view.setItem(row, 3, QTableWidgetItem(loc_str))

            # Col 4: Net Weight
            self.table_view.setItem(row, 4, QTableWidgetItem(f"{int(s.remaining_weight_g)}g"))

            # Col 5: Remaining %
            pct_item = QTableWidgetItem(f"{s.remain_percent}%")
            if s.remain_percent < 20:
                pct_item.setForeground(QColor(ERROR))
            self.table_view.setItem(row, 5, pct_item)

            # Col 6: Length Est
            self.table_view.setItem(row, 6, QTableWidgetItem(f"{int(s.estimated_length_m)}m"))

            # Col 7: Tags & Notes
            tags_str = ", ".join(meta.tags) if meta and meta.tags else (meta.notes if meta else "")
            self.table_view.setItem(row, 7, QTableWidgetItem(tags_str))

    def _render_grid(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 4
        for idx, s in enumerate(self.filtered_spools):
            r = idx // cols
            c = idx % cols
            card = SpoolCardWidget(s)
            card.clicked.connect(self.spool_selected.emit)
            self.grid_layout.addWidget(card, r, c)

    def _render_shelf(self) -> None:
        """Renders filament storage shelves with physical vertical spool profiles."""
        while self.shelf_layout.count():
            item = self.shelf_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        spools_per_shelf = 12
        total = len(self.filtered_spools)

        for shelf_idx in range(0, total, spools_per_shelf):
            shelf_spools = self.filtered_spools[shelf_idx : shelf_idx + spools_per_shelf]

            shelf_frame = QFrame()
            shelf_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {SURFACE_CONTAINER};
                    border-bottom: 4px solid {SURFACE_HIGHEST};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """)
            shelf_box = QVBoxLayout(shelf_frame)
            shelf_box.setContentsMargins(8, 4, 8, 4)

            label = QLabel(f"SHELF LEVEL {shelf_idx // spools_per_shelf + 1} ({len(shelf_spools)} Spools)")
            label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
            shelf_box.addWidget(label)

            row = QHBoxLayout()
            row.setSpacing(10)
            for s in shelf_spools:
                w = ShelfSpoolWidget(s)
                w.clicked.connect(self.spool_selected.emit)
                row.addWidget(w)
            row.addStretch()
            shelf_box.addLayout(row)

            self.shelf_layout.addWidget(shelf_frame)

        self.shelf_layout.addStretch()

    def _render_gallery(self) -> None:
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 6
        for idx, s in enumerate(self.filtered_spools):
            r = idx // cols
            c = idx % cols
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {SURFACE_CONTAINER};
                    border: 1px solid {BORDER_HAIRLINE};
                    border-radius: 6px;
                    padding: 8px;
                }}
                QFrame:hover {{
                    border: 1px solid {PRIMARY_BRIGHT};
                }}
            """)
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(8, 8, 8, 8)
            card_lay.setSpacing(6)

            swatch = QFrame()
            swatch.setFixedHeight(80)
            swatch.setStyleSheet(f"background-color: {s.color_code}; border-radius: 4px;")
            card_lay.addWidget(swatch)

            title = QLabel(s.series or s.material_type)
            title.setStyleSheet("font-weight: bold; font-size: 12px;")
            card_lay.addWidget(title)

            sub = QLabel(f"{s.color_code[:7]} • {int(s.remaining_weight_g)}g")
            sub.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 10px;")
            card_lay.addWidget(sub)

            self.gallery_layout.addWidget(card, r, c)

    def _on_table_cell_double_clicked(self, row: int, col: int) -> None:
        item = self.table_view.item(row, 0)
        if item:
            spool_id = item.data(Qt.ItemDataRole.UserRole)
            if spool_id:
                self.spool_selected.emit(spool_id)

    def _on_view_mode_changed(self, view_id: int) -> None:
        self.view_stack.setCurrentIndex(view_id)
        self._render_current_view()

    def _on_preset_clicked(self, preset_id: int) -> None:
        # 0: All, 1: AMS, 2: Low, 3: RFID, 4: Fav
        self.current_filter.only_ams_loaded = (preset_id == 1)
        self.current_filter.only_low_stock = (preset_id == 2)
        self.current_filter.only_favorites = (preset_id == 4)
        if preset_id == 3:
            self.current_filter.query = "RFID"
        elif self.current_filter.query == "RFID":
            self.current_filter.query = ""
        self.apply_filter()

    def _on_search_changed(self, text: str) -> None:
        self.current_filter.query = text
        self.apply_filter()

    def _on_material_changed(self, text: str) -> None:
        self.current_filter.material = None if text == "Material: All" else text
        self.apply_filter()

    def _on_brand_changed(self, text: str) -> None:
        self.current_filter.brand = None if text == "Brand: All" else text
        self.apply_filter()

    def _on_mass_slider_changed(self, val: int) -> None:
        self.mass_val_lbl.setText(f"≤{val}g")
        self.current_filter.max_mass_g = float(val) if val < 1000 else None
        self.apply_filter()

    def reset_filters(self) -> None:
        self.search_input.clear()
        self.material_combo.setCurrentIndex(0)
        self.brand_combo.setCurrentIndex(0)
        self.mass_slider.setValue(1000)
        self.preset_all.setChecked(True)
        self.current_filter = FilterCriteria()
        self.apply_filter()
