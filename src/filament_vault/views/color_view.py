"""Color Explorer & Smart Color Engine View.

Implements the Color Explorer mockup from stitch_filament_vault_desktop/filament_vault_color_explorer:
- Top Action & Filter Console:
  - Hex/Color code search
  - Quick Delta-E matcher trigger (ΔE < 2.0 / < 10.0)
  - Color Gamut & CIE Lab spark info
- Spectral Tabs / 13 Color Family Filters:
  - All Spectral, Monochrome & Neutrals, Reds, Greens, Blues, Purples, etc.
- Active Comparator Ribbon:
  - Target anchor swatch preview
  - Color space breakdown (HEX, CIE Lab [L, a, b], RGB)
- The Color Wall (Visual Spool Matrix):
  - Live ranking of spools by chromatic similarity
"""

from __future__ import annotations
from typing import List, Optional, Tuple
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
    QButtonGroup,
)

from ..models.spool import Spool
from ..core.color_engine import (
    COLOR_FAMILIES,
    FAMILY_PREVIEW_COLORS,
    parse_hex_color,
    rgb_to_lab,
    delta_e_ciede2000,
    find_similar_spools,
)
from .widgets import SwatchWidget
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
    TEXT_PRIMARY,
    TEXT_MUTED,
)


class ColorExplorerView(QWidget):
    """Visual Color Engine & Discovery Wall for browsing filament inventories."""

    spool_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.all_spools: List[Spool] = []
        self.active_anchor_hex: str = "#00AE42"  # Bambu Green default
        self.active_family: str = "all"
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Top Action Console
        console = QFrame()
        console.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_LOW};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        console_lay = QVBoxLayout(console)
        console_lay.setContentsMargins(10, 10, 10, 10)
        console_lay.setSpacing(10)

        # Upper row: Search, Delta-E Scope, Gamut
        upper_row = QHBoxLayout()
        upper_row.setSpacing(12)

        self.color_search = QLineEdit()
        self.color_search.setText(self.active_anchor_hex)
        self.color_search.setPlaceholderText("Enter HEX (#00AE42), RGB, or color name...")
        self.color_search.returnPressed.connect(self._on_search_entered)
        upper_row.addWidget(self.color_search, stretch=3)

        btn_match = QPushButton("Match ΔE")
        btn_match.setProperty("id", "primaryBtn")
        btn_match.clicked.connect(self._on_search_entered)
        upper_row.addWidget(btn_match)

        # Center info
        info_badge = QLabel("D65 / 10° CIE Standard • CIEDE2000 Gamut")
        info_badge.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 11px;")
        upper_row.addWidget(info_badge)
        upper_row.addStretch()

        console_lay.addLayout(upper_row)

        # Lower row: Color family spectral tabs
        family_scroll = QScrollArea()
        family_scroll.setWidgetResizable(True)
        family_scroll.setFixedHeight(38)
        family_scroll.setFrameShape(QFrame.Shape.NoFrame)

        family_bar = QWidget()
        self.family_lay = QHBoxLayout(family_bar)
        self.family_lay.setContentsMargins(0, 0, 0, 0)
        self.family_lay.setSpacing(6)

        self.family_group = QButtonGroup(self)
        self.family_group.setExclusive(True)

        # All button
        btn_all = QPushButton("All Spectral")
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        self.family_group.addButton(btn_all, 0)
        self.family_lay.addWidget(btn_all)

        for idx, fam in enumerate(COLOR_FAMILIES, start=1):
            btn = QPushButton(fam.capitalize())
            btn.setCheckable(True)
            self.family_group.addButton(btn, idx)
            self.family_lay.addWidget(btn)

        self.family_lay.addStretch()
        self.family_group.idClicked.connect(self._on_family_tab_clicked)
        family_scroll.setWidget(family_bar)
        console_lay.addWidget(family_scroll)

        main_layout.addWidget(console)

        # 2. Active Comparator Ribbon
        self.ribbon = QFrame()
        self.ribbon.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        ribbon_lay = QHBoxLayout(self.ribbon)
        ribbon_lay.setContentsMargins(12, 8, 12, 8)
        ribbon_lay.setSpacing(12)

        self.anchor_swatch = QFrame()
        self.anchor_swatch.setFixedSize(32, 32)
        self.anchor_swatch.setStyleSheet(f"""
            background-color: {self.active_anchor_hex};
            border-radius: 6px;
            border: 1px solid {BORDER_HAIRLINE};
        """)
        ribbon_lay.addWidget(self.anchor_swatch)

        self.anchor_title = QLabel("Selected Target Anchor: #00AE42")
        self.anchor_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        ribbon_lay.addWidget(self.anchor_title)

        self.anchor_details = QLabel("CIE Lab: [59.4, -62.1, 41.8]")
        self.anchor_details.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 11px;")
        ribbon_lay.addWidget(self.anchor_details)

        ribbon_lay.addStretch()

        self.match_count_lbl = QLabel("Matching Spools: 0")
        self.match_count_lbl.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-family: 'JetBrains Mono'; font-weight: bold; font-size: 11px;")
        ribbon_lay.addWidget(self.match_count_lbl)

        main_layout.addWidget(self.ribbon)

        # 3. The Color Wall Matrix
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.wall_container = QWidget()
        self.wall_layout = QGridLayout(self.wall_container)
        self.wall_layout.setSpacing(12)
        scroll.setWidget(self.wall_container)

        main_layout.addWidget(scroll, stretch=1)

    def set_spools(self, spools: List[Spool]) -> None:
        self.all_spools = spools
        self.render_wall()

    def set_anchor_hex(self, hex_code: str) -> None:
        self.active_anchor_hex = hex_code
        self.color_search.setText(hex_code)
        self.anchor_swatch.setStyleSheet(f"""
            background-color: {hex_code};
            border-radius: 6px;
            border: 1px solid {BORDER_HAIRLINE};
        """)
        r, g, b, _ = parse_hex_color(hex_code)
        l, a, b_val = rgb_to_lab(r, g, b)
        self.anchor_title.setText(f"Selected Target Anchor: {hex_code}")
        self.anchor_details.setText(f"RGB: ({r}, {g}, {b}) • CIE Lab: [{l}, {a}, {b_val}]")
        self.render_wall()

    def render_wall(self) -> None:
        while self.wall_layout.count():
            item = self.wall_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filter by family if requested
        candidates = self.all_spools
        if self.active_family != "all":
            candidates = [s for s in candidates if s.color_family.lower() == self.active_family.lower()]

        # Compute Delta-E against active anchor
        tr, tg, tb, _ = parse_hex_color(self.active_anchor_hex)
        t_lab = rgb_to_lab(tr, tg, tb)

        scored_spools: List[Tuple[Spool, float]] = []
        for s in candidates:
            sr, sg, sb, _ = parse_hex_color(s.color_code)
            s_lab = rgb_to_lab(sr, sg, sb)
            de = delta_e_ciede2000(t_lab, s_lab)
            scored_spools.append((s, de))

        # Rank by closest color difference
        scored_spools.sort(key=lambda x: x[1])
        self.match_count_lbl.setText(f"Matching Spools: {len(scored_spools)}")

        cols = 6
        for idx, (spool, de) in enumerate(scored_spools):
            r = idx // cols
            c = idx % cols
            swatch = SwatchWidget(spool, delta_e=de)
            swatch.clicked.connect(self.spool_selected.emit)
            self.wall_layout.addWidget(swatch, r, c)

    def _on_search_entered(self) -> None:
        val = self.color_search.text().strip()
        if not val.startswith("#"):
            val = "#" + val
        self.set_anchor_hex(val)

    def _on_family_tab_clicked(self, tab_id: int) -> None:
        if tab_id == 0:
            self.active_family = "all"
        else:
            self.active_family = COLOR_FAMILIES[tab_id - 1]
        self.render_wall()
