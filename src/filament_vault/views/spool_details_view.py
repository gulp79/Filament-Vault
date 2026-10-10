"""Spool Details and User Metadata Editor View.

Implements the layout shown in stitch_filament_vault_desktop/filament_vault_spool_details:
- Sub-Header Ribbon: Spool Identity & Quick Status Bar (Material, Brand, RFID status)
- Primary Parametric Cockpit (3-Column Layout):
  - Left: Spool Visual Vector Asset (radial winding graphic), Mass Net readout, AMS RFID Telemetry card
  - Center: Technical Specifications (Material, Diameter, Setting ID, Tare spool weight, Extrusion temp)
  - Right: User-Generated Metadata (Tags, Notes, Collections, Custom Location, Favorites)
- Strictly keeps user data stored in user_data/ while Bambu Studio inventory remains untouched.
"""

from __future__ import annotations
from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QCheckBox,
)

from ..models.spool import Spool, SpoolMetadata
from ..models.metadata_store import MetadataStore
from .widgets import SpoolVisualWidget
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


class SpoolDetailsView(QWidget):
    """Detailed telemetry inspector and metadata editor for a single spool."""

    metadata_saved = Signal(str)  # Emits spool_id

    def __init__(self, metadata_store: MetadataStore, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.metadata_store = metadata_store
        self.current_spool: Optional[Spool] = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Sub-Header Ribbon
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_LOW};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        h_lay = QHBoxLayout(self.header_frame)
        h_lay.setContentsMargins(12, 8, 12, 8)
        h_lay.setSpacing(12)

        self.color_dot = QFrame()
        self.color_dot.setFixedSize(14, 14)
        self.color_dot.setStyleSheet("border-radius: 7px; background-color: #00AE42;")
        h_lay.addWidget(self.color_dot)

        self.title_lbl = QLabel("Bambu Lab PLA Basic - Bambu Green")
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        h_lay.addWidget(self.title_lbl)

        self.rfid_badge = QLabel("RFID: AUTHENTICATED")
        self.rfid_badge.setStyleSheet(f"color: {SECONDARY}; font-family: 'JetBrains Mono'; font-size: 11px; font-weight: bold;")
        h_lay.addWidget(self.rfid_badge)

        h_lay.addStretch()

        self.btn_save = QPushButton("Save User Metadata")
        self.btn_save.setProperty("id", "primaryBtn")
        self.btn_save.clicked.connect(self._save_metadata)
        h_lay.addWidget(self.btn_save)

        main_layout.addWidget(self.header_frame)

        # 2. Main 3-Column Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        cockpit_container = QWidget()
        cols_lay = QHBoxLayout(cockpit_container)
        cols_lay.setSpacing(16)

        # --- Col 1: Spool Radial Visual & RFID Telemetry ---
        col1 = QFrame()
        col1.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        col1_lay = QVBoxLayout(col1)
        col1_lay.setSpacing(12)

        lbl_c1 = QLabel("SPOOL GEOMETRY & CAPACITY")
        lbl_c1.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        col1_lay.addWidget(lbl_c1)

        self.spool_visual = SpoolVisualWidget(None)
        self.spool_visual.setMinimumSize(180, 180)
        col1_lay.addWidget(self.spool_visual, alignment=Qt.AlignmentFlag.AlignCenter)

        # RFID Card
        self.rfid_box = QFrame()
        self.rfid_box.setStyleSheet(f"background-color: {SURFACE_LOW}; border-radius: 4px; padding: 8px;")
        rfid_lay = QVBoxLayout(self.rfid_box)
        rfid_lay.setSpacing(4)

        rfid_title = QLabel("AMS RFID TELEMETRY")
        rfid_title.setStyleSheet(f"color: {SECONDARY}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        rfid_lay.addWidget(rfid_title)

        self.rfid_uid_lbl = QLabel("Tag UID: --")
        self.rfid_uid_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_PRIMARY};")
        rfid_lay.addWidget(self.rfid_uid_lbl)

        self.spool_id_lbl = QLabel("Spool ID: --")
        self.spool_id_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_MUTED};")
        rfid_lay.addWidget(self.spool_id_lbl)

        col1_lay.addWidget(self.rfid_box)
        col1_lay.addStretch()
        cols_lay.addWidget(col1, stretch=1)

        # --- Col 2: Technical Specifications ---
        col2 = QFrame()
        col2.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        col2_lay = QVBoxLayout(col2)
        col2_lay.setSpacing(10)

        lbl_c2 = QLabel("FACTORY PARAMETRIC SPECIFICATIONS")
        lbl_c2.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        col2_lay.addWidget(lbl_c2)

        self.spec_grid = QGridLayout()
        self.spec_grid.setSpacing(8)

        self.fields = {
            "Material Type": QLabel("--"),
            "Series": QLabel("--"),
            "Brand": QLabel("--"),
            "Diameter": QLabel("--"),
            "Initial Weight": QLabel("--"),
            "Current Weight": QLabel("--"),
            "Estimated Length": QLabel("--"),
            "Color Code (HEX)": QLabel("--"),
            "Color Family": QLabel("--"),
            "Setting ID": QLabel("--"),
            "Tray ID": QLabel("--"),
            "Cloud Synced": QLabel("--"),
        }

        row = 0
        for name, lbl in self.fields.items():
            k_lbl = QLabel(name)
            k_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 600;")
            self.spec_grid.addWidget(k_lbl, row, 0)
            self.spec_grid.addWidget(lbl, row, 1)
            row += 1

        col2_lay.addLayout(self.spec_grid)
        col2_lay.addStretch()
        cols_lay.addWidget(col2, stretch=1)

        # --- Col 3: User Metadata Editor ---
        col3 = QFrame()
        col3.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 12px;")
        col3_lay = QVBoxLayout(col3)
        col3_lay.setSpacing(10)

        lbl_c3 = QLabel("USER METADATA (INDEPENDENT STORAGE)")
        lbl_c3.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        col3_lay.addWidget(lbl_c3)

        self.chk_favorite = QCheckBox("Add to Favorites")
        col3_lay.addWidget(self.chk_favorite)

        col3_lay.addWidget(QLabel("Physical Location (Shelf, Drybox):"))
        self.txt_location = QLineEdit()
        self.txt_location.setPlaceholderText("e.g. Drybox 1, Rack B-4")
        col3_lay.addWidget(self.txt_location)

        col3_lay.addWidget(QLabel("Custom Tags (comma separated):"))
        self.txt_tags = QLineEdit()
        self.txt_tags.setPlaceholderText("e.g. Prototype, High-Detail, Waterproof")
        col3_lay.addWidget(self.txt_tags)

        col3_lay.addWidget(QLabel("Collections (comma separated):"))
        self.txt_collections = QLineEdit()
        self.txt_collections.setPlaceholderText("e.g. Architectural Models, Client A")
        col3_lay.addWidget(self.txt_collections)

        col3_lay.addWidget(QLabel("User Notes:"))
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Custom temperature calibration notes, flow rate, purchase date...")
        self.txt_notes.setMaximumHeight(120)
        col3_lay.addWidget(self.txt_notes)

        col3_lay.addStretch()
        cols_lay.addWidget(col3, stretch=1)

        scroll.setWidget(cockpit_container)
        main_layout.addWidget(scroll, stretch=1)

    def set_spool(self, spool: Optional[Spool]) -> None:
        self.current_spool = spool
        if not spool:
            return

        self.spool_visual.set_spool(spool)
        self.title_lbl.setText(f"{spool.brand} {spool.series or spool.material_type} - {spool.color_code[:7]}")
        self.color_dot.setStyleSheet(f"border-radius: 7px; background-color: {spool.color_code};")

        self.rfid_uid_lbl.setText(f"Tag UID: {spool.tag_uid or 'N/A'}")
        self.spool_id_lbl.setText(f"Spool ID: {spool.spool_id}")

        self.fields["Material Type"].setText(spool.material_type)
        self.fields["Series"].setText(spool.series)
        self.fields["Brand"].setText(spool.brand)
        self.fields["Diameter"].setText(f"{spool.diameter} mm")
        self.fields["Initial Weight"].setText(f"{spool.initial_weight} g")
        self.fields["Current Weight"].setText(f"{spool.remaining_weight_g} g ({spool.remain_percent}%)")
        self.fields["Estimated Length"].setText(f"{spool.estimated_length_m} m")
        self.fields["Color Code (HEX)"].setText(spool.color_code)
        self.fields["Color Family"].setText(spool.color_family.upper())
        self.fields["Setting ID"].setText(spool.setting_id or "--")
        self.fields["Tray ID"].setText(spool.tray_id_name or "--")
        self.fields["Cloud Synced"].setText("Yes" if spool.cloud_synced else "No")

        # Load user metadata
        meta = self.metadata_store.get_metadata(spool.spool_id)
        self.chk_favorite.setChecked(meta.favorite)
        self.txt_location.setText(meta.custom_location)
        self.txt_tags.setText(", ".join(meta.tags))
        self.txt_collections.setText(", ".join(meta.collections))
        self.txt_notes.setPlainText(meta.notes)

    def _save_metadata(self) -> None:
        if not self.current_spool:
            return

        sid = self.current_spool.spool_id
        meta = self.metadata_store.get_metadata(sid)

        meta.favorite = self.chk_favorite.isChecked()
        meta.custom_location = self.txt_location.text().strip()

        # Parse comma separated tags
        raw_tags = [t.strip() for t in self.txt_tags.text().split(",") if t.strip()]
        meta.tags = raw_tags

        # Parse collections
        raw_colls = [c.strip() for c in self.txt_collections.text().split(",") if c.strip()]
        meta.collections = raw_colls

        meta.notes = self.txt_notes.toPlainText().strip()

        self.metadata_store.update_metadata(meta)
        self.metadata_saved.emit(sid)
