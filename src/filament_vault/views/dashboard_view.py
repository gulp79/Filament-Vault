"""Engineering Telemetry Dashboard View.

Implements the layout shown in stitch_filament_vault_desktop/filament_vault_dashboard:
- Top Engineering KPI Strip (Inventory Headcount, Net Material Mass, AMS Occupancy, Print Runway, Low Stock)
- Material Distribution Matrix with Grafana-style proportional bars
- AMS Unit Status overview
- Depletion / Low Stock Alert Queue
- Recent inventory activity
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QScrollArea,
    QPushButton,
)

from ..models.spool import Spool
from ..models.analytics_engine import AnalyticsEngine
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
    WARNING,
    TEXT_PRIMARY,
    TEXT_MUTED,
)


class DashboardView(QWidget):
    """Main Dashboard View displaying real-time telemetry metrics and engineering KPIs."""

    spool_selected = Signal(str)
    navigate_requested = Signal(str)  # Tab path like 'inventory-explorer'

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # 1. Top KPI Strip (5 cards)
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(12)
        self.content_layout.addLayout(self.kpi_grid)

        # 2. Middle Section: Material Matrix & AMS Hubs
        middle_row = QHBoxLayout()
        middle_row.setSpacing(16)

        # Material Matrix Card
        self.matrix_card = QFrame()
        self.matrix_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        self.matrix_layout = QVBoxLayout(self.matrix_card)
        self.matrix_layout.setContentsMargins(12, 12, 12, 12)
        self.matrix_layout.setSpacing(10)
        middle_row.addWidget(self.matrix_card, stretch=3)

        # Low Stock & Alert Queue Card
        self.alerts_card = QFrame()
        self.alerts_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        self.alerts_layout = QVBoxLayout(self.alerts_card)
        self.alerts_layout.setContentsMargins(12, 12, 12, 12)
        self.alerts_layout.setSpacing(10)
        middle_row.addWidget(self.alerts_card, stretch=2)

        self.content_layout.addLayout(middle_row)

        # 3. Bottom Section: Manufacturer Distribution & Quick Actions
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        self.brands_card = QFrame()
        self.brands_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        self.brands_layout = QVBoxLayout(self.brands_card)
        self.brands_layout.setContentsMargins(12, 12, 12, 12)
        bottom_row.addWidget(self.brands_card, stretch=1)

        self.color_summary_card = QFrame()
        self.color_summary_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        self.color_summary_layout = QVBoxLayout(self.color_summary_card)
        self.color_summary_layout.setContentsMargins(12, 12, 12, 12)
        bottom_row.addWidget(self.color_summary_card, stretch=1)

        self.content_layout.addLayout(bottom_row)
        self.content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def update_data(self, spools: List[Spool]) -> None:
        """Refresh all telemetry components from spool inventory."""
        summary = AnalyticsEngine.compute_summary(spools)
        materials = AnalyticsEngine.get_material_distribution(spools)
        brands = AnalyticsEngine.get_brand_distribution(spools)
        colors = AnalyticsEngine.get_color_family_distribution(spools)

        # Clear existing KPI grid widgets
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Render KPI Cards
        # 1. Headcount
        c1 = self._build_kpi_card(
            title="INVENTORY HEADCOUNT",
            value=f"{summary['total_spools']}",
            unit="Spools",
            subtext=f"<span style='color:{PRIMARY_BRIGHT}'>{summary['active_spools']} Act</span> • <span style='color:{TERTIARY}'>{summary['sealed_spools']} Seal</span> • <span style='color:{ERROR}'>{summary['depleted_spools']} Depl</span>",
            val_color=TEXT_PRIMARY,
        )
        self.kpi_grid.addWidget(c1, 0, 0)

        # 2. Net Material Mass
        c2 = self._build_kpi_card(
            title="NET MATERIAL MASS",
            value=f"{summary['total_weight_kg']}",
            unit=f"kg ({summary['capacity_percent']}%)",
            progress_pct=summary["capacity_percent"],
            progress_color=PRIMARY,
            val_color=PRIMARY_BRIGHT,
        )
        self.kpi_grid.addWidget(c2, 0, 1)

        # 3. AMS Slots
        ams_loaded = summary["ams_loaded_count"]
        c3 = self._build_kpi_card(
            title="AMS FEEDER SLOTS",
            value=f"{ams_loaded}",
            unit="Loaded in Hub",
            subtext=f"<span style='color:{SECONDARY}'>{ams_loaded} Synced Trays</span>",
            val_color=SECONDARY,
        )
        self.kpi_grid.addWidget(c3, 0, 2)

        # 4. Print Runway
        c4 = self._build_kpi_card(
            title="PRINT RUNWAY",
            value=f"~{int(summary['print_runway_hours'])}",
            unit="Hours",
            subtext=f"{int(summary['total_length_m'])}m est. total",
            val_color=TERTIARY,
        )
        self.kpi_grid.addWidget(c4, 0, 3)

        # 5. Low Stock
        c5 = self._build_kpi_card(
            title="LOW STOCK WARNINGS",
            value=f"{summary['low_stock_count']}",
            unit="< 200g remaining",
            subtext=f"<span style='color:{ERROR}'>Reorder queue active</span>",
            val_color=ERROR if summary['low_stock_count'] > 0 else TEXT_MUTED,
        )
        self.kpi_grid.addWidget(c5, 0, 4)

        # Render Material Matrix
        self._render_material_matrix(materials)

        # Render Alerts
        self._render_alerts(spools)

        # Render Brand & Color distributions
        self._render_brands(brands)
        self._render_color_families(colors)

    def _build_kpi_card(
        self,
        title: str,
        value: str,
        unit: str,
        subtext: str = "",
        progress_pct: Optional[float] = None,
        progress_color: str = PRIMARY,
        val_color: str = TEXT_PRIMARY,
    ) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: {SURFACE_HIGH};
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        lay.addWidget(title_lbl)

        val_row = QHBoxLayout()
        val_row.setSpacing(6)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {val_color}; font-size: 22px; font-weight: bold; font-family: 'JetBrains Mono';")
        val_row.addWidget(val_lbl)

        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-family: 'JetBrains Mono';")
        val_row.addWidget(unit_lbl)
        val_row.addStretch()
        lay.addLayout(val_row)

        if progress_pct is not None:
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(progress_pct))
            bar.setTextVisible(False)
            bar.setFixedHeight(4)
            bar.setStyleSheet(f"""
                QProgressBar {{ background-color: {SURFACE_BASE}; border: none; border-radius: 2px; }}
                QProgressBar::chunk {{ background-color: {progress_color}; border-radius: 2px; }}
            """)
            lay.addWidget(bar)

        if subtext:
            sub_lbl = QLabel(subtext)
            sub_lbl.setStyleSheet("font-size: 11px; font-family: 'JetBrains Mono';")
            lay.addWidget(sub_lbl)

        return card

    def _render_material_matrix(self, materials: List[Dict[str, Any]]) -> None:
        # Clear layout
        while self.matrix_layout.count():
            item = self.matrix_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hdr = QLabel("MATERIAL MATRIX TELEMETRY")
        hdr.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.matrix_layout.addWidget(hdr)

        for mat in materials[:6]:
            row = QHBoxLayout()
            name_lbl = QLabel(mat["material"])
            name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")
            row.addWidget(name_lbl, stretch=2)

            count_lbl = QLabel(f"{mat['count']} Spools")
            count_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 11px;")
            row.addWidget(count_lbl, stretch=1)

            wt_lbl = QLabel(f"{mat['weight_kg']} kg ({mat['percentage']}%)")
            wt_lbl.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-family: 'JetBrains Mono'; font-size: 11px; font-weight: bold;")
            row.addWidget(wt_lbl, stretch=1, alignment=Qt.AlignmentFlag.AlignRight)

            self.matrix_layout.addLayout(row)

            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(int(mat["percentage"]))
            pbar.setTextVisible(False)
            pbar.setFixedHeight(4)
            pbar.setStyleSheet(f"""
                QProgressBar {{ background-color: {SURFACE_BASE}; border: none; border-radius: 2px; }}
                QProgressBar::chunk {{ background-color: {PRIMARY}; border-radius: 2px; }}
            """)
            self.matrix_layout.addWidget(pbar)

        self.matrix_layout.addStretch()

    def _render_alerts(self, spools: List[Spool]) -> None:
        while self.alerts_layout.count():
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hdr = QLabel("LOW STOCK & DEPLETION QUEUE")
        hdr.setStyleSheet(f"color: {ERROR}; font-size: 12px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.alerts_layout.addWidget(hdr)

        low_stock = [s for s in spools if s.remain_percent < 20 or s.remaining_weight_g < 200.0]
        if not low_stock:
            ok_lbl = QLabel("✓ All filament reserves above threshold (>20%)")
            ok_lbl.setStyleSheet(f"color: {SECONDARY}; font-size: 12px; padding: 10px 0;")
            self.alerts_layout.addWidget(ok_lbl)
        else:
            for s in low_stock[:5]:
                row = QHBoxLayout()
                swatch = QFrame()
                swatch.setFixedSize(12, 12)
                swatch.setStyleSheet(f"background-color: {s.color_code}; border-radius: 2px;")
                row.addWidget(swatch)

                name_lbl = QLabel(f"{s.brand} {s.series}")
                name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px;")
                row.addWidget(name_lbl, stretch=2)

                rem_lbl = QLabel(f"{int(s.remaining_weight_g)}g ({s.remain_percent}%)")
                rem_lbl.setStyleSheet(f"color: {ERROR}; font-family: 'JetBrains Mono'; font-weight: bold; font-size: 11px;")
                row.addWidget(rem_lbl)

                self.alerts_layout.addLayout(row)

        self.alerts_layout.addStretch()

    def _render_brands(self, brands: List[Dict[str, Any]]) -> None:
        while self.brands_layout.count():
            item = self.brands_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hdr = QLabel("MANUFACTURER DISTRIBUTION")
        hdr.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.brands_layout.addWidget(hdr)

        for b in brands[:5]:
            row = QHBoxLayout()
            name_lbl = QLabel(b["brand"])
            name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
            row.addWidget(name_lbl, stretch=2)

            cnt_lbl = QLabel(f"{b['count']} ({b['percentage']}%)")
            cnt_lbl.setStyleSheet(f"color: {TERTIARY}; font-family: 'JetBrains Mono'; font-size: 11px;")
            row.addWidget(cnt_lbl, alignment=Qt.AlignmentFlag.AlignRight)
            self.brands_layout.addLayout(row)

        self.brands_layout.addStretch()

    def _render_color_families(self, colors: List[Dict[str, Any]]) -> None:
        while self.color_summary_layout.count():
            item = self.color_summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hdr = QLabel("TOP COLOR FAMILIES")
        hdr.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.color_summary_layout.addWidget(hdr)

        for c in colors[:5]:
            row = QHBoxLayout()
            fam_lbl = QLabel(c["family"].capitalize())
            fam_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
            row.addWidget(fam_lbl, stretch=2)

            cnt_lbl = QLabel(f"{c['count']} Spools")
            cnt_lbl.setStyleSheet(f"color: {SECONDARY}; font-family: 'JetBrains Mono'; font-size: 11px;")
            row.addWidget(cnt_lbl, alignment=Qt.AlignmentFlag.AlignRight)
            self.color_summary_layout.addLayout(row)

        self.color_summary_layout.addStretch()
