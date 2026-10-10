"""Analytics and Cost Intelligence View.

Implements the layout shown in stitch_filament_vault_desktop/filament_vault_analytics:
- Top Telemetry Header & Metric Ribbon (30-Day Material Flow, Turnover, Valuation, Purge Loss)
- Duplicate Spool & Fragmentation Analysis Engine (alerts on open split spools of identical material)
- Material and Manufacturer Breakdown Tables
- Export to CSV action
"""

from __future__ import annotations
import csv
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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


class AnalyticsView(QWidget):
    """Deep analytics, telemetry, and duplicate spool detector."""

    spool_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.all_spools: List[Spool] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Header & Actions
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        hdr_title = QLabel("Telemetry & Cost Intelligence")
        hdr_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_row.addWidget(hdr_title)

        tag = QLabel("Bambu Studio JSON-RPC Live Feed")
        tag.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-family: 'JetBrains Mono'; font-size: 11px;")
        header_row.addWidget(tag)
        header_row.addStretch()

        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        header_row.addWidget(self.btn_export_csv)

        main_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_lay = QVBoxLayout(content)
        self.content_lay.setSpacing(16)

        # 2. Metric Ribbon (4 cards)
        self.metric_ribbon_grid = QGridLayout()
        self.metric_ribbon_grid.setSpacing(12)
        self.content_lay.addLayout(self.metric_ribbon_grid)

        # 3. Intelligent Fragmentation & Redundancy Detection
        self.fragmentation_card = QFrame()
        self.fragmentation_card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        self.frag_layout = QVBoxLayout(self.fragmentation_card)
        self.frag_layout.setSpacing(10)
        self.content_lay.addWidget(self.fragmentation_card)

        # 4. Material Breakdown Table
        mat_header = QLabel("MATERIAL INVENTORY BREAKDOWN")
        mat_header.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.content_lay.addWidget(mat_header)

        self.mat_table = QTableWidget()
        self.mat_table.setColumnCount(4)
        self.mat_table.setHorizontalHeaderLabels(["Material Type", "Spool Count", "Total Mass (kg)", "Share (%)"])
        self.mat_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mat_table.verticalHeader().setVisible(False)
        self.mat_table.setFixedHeight(160)
        self.content_lay.addWidget(self.mat_table)

        self.content_lay.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def set_spools(self, spools: List[Spool]) -> None:
        self.all_spools = spools
        summary = AnalyticsEngine.compute_summary(spools)
        materials = AnalyticsEngine.get_material_distribution(spools)
        conflicts = AnalyticsEngine.detect_fragmentation_conflicts(spools)

        # Update metric ribbon
        while self.metric_ribbon_grid.count():
            item = self.metric_ribbon_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Ribbon 1: Available Mass
        r1 = self._build_card("AVAILABLE NET MASS", f"{summary['total_weight_kg']} kg", f"{summary['total_spools']} Spools total", PRIMARY_BRIGHT)
        self.metric_ribbon_grid.addWidget(r1, 0, 0)

        # Ribbon 2: Inventory Valuation
        r2 = self._build_card("ESTIMATED VALUATION", f"${summary['estimated_valuation']:.2f}", "Avg $20.00 / kg standard", SECONDARY)
        self.metric_ribbon_grid.addWidget(r2, 0, 1)

        # Ribbon 3: Print Runway
        r3 = self._build_card("ESTIMATED RUNWAY", f"~{int(summary['print_runway_hours'])} hrs", f"{int(summary['total_length_m'])}m continuous feed", TERTIARY)
        self.metric_ribbon_grid.addWidget(r3, 0, 2)

        # Ribbon 4: Low Stock Alert
        r4 = self._build_card("DEPLETION QUEUE", f"{summary['low_stock_count']}", "Spools with <20% mass", ERROR if summary['low_stock_count'] > 0 else TEXT_MUTED)
        self.metric_ribbon_grid.addWidget(r4, 0, 3)

        # Render Fragmentation & Redundancy
        while self.frag_layout.count():
            item = self.frag_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        f_hdr = QLabel("SPOOL FRAGMENTATION & REDUNDANCY ANALYSIS")
        f_hdr.setStyleSheet(f"color: {SECONDARY}; font-size: 12px; font-weight: bold; font-family: 'JetBrains Mono';")
        self.frag_layout.addWidget(f_hdr)

        f_desc = QLabel("Identifies split remnants and identical opened spools eligible for merger to optimize drybox space.")
        f_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.frag_layout.addWidget(f_desc)

        if not conflicts:
            none_lbl = QLabel("✓ Zero duplicate opened spools detected.")
            none_lbl.setStyleSheet(f"color: {SECONDARY}; font-size: 12px; padding: 6px 0;")
            self.frag_layout.addWidget(none_lbl)
        else:
            for conf in conflicts[:4]:
                box = QFrame()
                box.setStyleSheet(f"background-color: {SURFACE_LOW}; border-radius: 4px; padding: 6px;")
                b_lay = QHBoxLayout(box)
                b_lay.setContentsMargins(8, 6, 8, 6)

                swatch = QFrame()
                swatch.setFixedSize(14, 14)
                swatch.setStyleSheet(f"background-color: {conf['color_code']}; border-radius: 3px;")
                b_lay.addWidget(swatch)

                title_lbl = QLabel(conf["title"])
                title_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
                b_lay.addWidget(title_lbl, stretch=2)

                stat_lbl = QLabel(f"{conf['count']} Spools • {conf['total_weight_g']}g total")
                stat_lbl.setStyleSheet(f"color: {PRIMARY_BRIGHT}; font-family: 'JetBrains Mono'; font-size: 11px;")
                b_lay.addWidget(stat_lbl)

                rec_lbl = QLabel(conf["recommendation"])
                rec_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
                b_lay.addWidget(rec_lbl, stretch=3)

                self.frag_layout.addWidget(box)

        # Render Material Table
        self.mat_table.setRowCount(len(materials))
        for row, mat in enumerate(materials):
            self.mat_table.setItem(row, 0, QTableWidgetItem(mat["material"]))
            self.mat_table.setItem(row, 1, QTableWidgetItem(str(mat["count"])))
            self.mat_table.setItem(row, 2, QTableWidgetItem(f"{mat['weight_kg']:.2f} kg"))
            self.mat_table.setItem(row, 3, QTableWidgetItem(f"{mat['percentage']}%"))

    def _build_card(self, title: str, val: str, sub: str, val_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"background-color: {SURFACE_CONTAINER}; border: 1px solid {BORDER_HAIRLINE}; border-radius: 6px; padding: 10px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; font-family: 'JetBrains Mono';")
        lay.addWidget(t_lbl)

        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: bold; font-family: 'JetBrains Mono';")
        lay.addWidget(v_lbl)

        s_lbl = QLabel(sub)
        s_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        lay.addWidget(s_lbl)
        return card

    def _export_csv(self) -> None:
        if not self.all_spools:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Spool Inventory CSV", "spools_inventory.csv", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Spool ID", "Brand", "Material", "Series", "Color Code", "Color Family",
                    "Net Weight (g)", "Initial Weight (g)", "Remain %", "Est Length (m)", "AMS Tray ID", "RFID Tag"
                ])
                for s in self.all_spools:
                    writer.writerow([
                        s.spool_id, s.brand, s.material_type, s.series, s.color_code, s.color_family,
                        s.remaining_weight_g, s.initial_weight, s.remain_percent, s.estimated_length_m,
                        s.tray_id_name, s.tag_uid
                    ])
        except Exception:
            pass
