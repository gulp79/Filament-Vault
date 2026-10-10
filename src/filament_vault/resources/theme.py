"""Design token definitions and PySide6 QSS stylesheet.

Faithfully implements the visual design system defined in stitch_filament_vault_desktop/filament_vault/DESIGN.md:
- Colors: Surface #10141a, Primary #54e16d, Secondary #4edea3, Tertiary #7bd0ff, Error #ffb4ab
- Typography: Inter & JetBrains Mono
- Radii: 4px default, 6px containers
- Borders: #30363d hairline borders
"""

from __future__ import annotations

# Color Constants
SURFACE_BASE = "#0a0e14"
SURFACE = "#10141a"
SURFACE_LOW = "#181c22"
SURFACE_CONTAINER = "#1c2026"
SURFACE_HIGH = "#262a31"
SURFACE_HIGHEST = "#31353c"
SURFACE_BRIGHT = "#353940"

PRIMARY = "#00ae42"  # Bambu signature green
PRIMARY_BRIGHT = "#54e16d"
PRIMARY_CONTAINER = "#00531b"
ON_PRIMARY = "#003910"

SECONDARY = "#10b981"  # Telemetry emerald
TERTIARY = "#38bdf8"   # Cool cyan
ERROR = "#f85149"      # Warning/empty red
WARNING = "#d29922"    # Amber

TEXT_PRIMARY = "#f0f6fc"
TEXT_MUTED = "#8b949e"
TEXT_DIM = "#484f58"

BORDER_HAIRLINE = "#30363d"
BORDER_FOCUS = "#00ae42"

APP_STYLESHEET = f"""
/* Universal Window & Component Theme */
QMainWindow, QWidget {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
}}

/* Toolbars and Headers */
QToolBar {{
    background-color: {SURFACE_BASE};
    border-bottom: 1px solid {BORDER_HAIRLINE};
    spacing: 6px;
    padding: 4px;
}}

/* Scrollbars - Compact technical aesthetic */
QScrollBar:vertical {{
    background: {SURFACE_CONTAINER};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE_HIGHEST};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {SURFACE_CONTAINER};
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {SURFACE_HIGHEST};
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Text Fields and Search Inputs */
QLineEdit {{
    background-color: {SURFACE_BASE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 5px 8px;
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    selection-background-color: {PRIMARY};
    selection-color: #ffffff;
}}
QLineEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
    background-color: {SURFACE_CONTAINER};
}}
QLineEdit:hover {{
    border: 1px solid {TEXT_DIM};
}}

/* Combo Boxes */
QComboBox {{
    background-color: {SURFACE_CONTAINER};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
QComboBox:hover {{
    border: 1px solid {TEXT_MUTED};
    background-color: {SURFACE_HIGH};
}}
QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_CONTAINER};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_HAIRLINE};
    selection-background-color: {PRIMARY};
    selection-color: #ffffff;
    outline: none;
}}

/* Push Buttons */
QPushButton {{
    background-color: {SURFACE_HIGH};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {SURFACE_HIGHEST};
    border: 1px solid {TEXT_MUTED};
}}
QPushButton:pressed {{
    background-color: {SURFACE_CONTAINER};
}}

/* Primary Action Buttons */
QPushButton#primaryBtn {{
    background-color: {PRIMARY};
    color: #ffffff;
    font-weight: 600;
    border: none;
}}
QPushButton#primaryBtn:hover {{
    background-color: {PRIMARY_BRIGHT};
    color: #000000;
}}
QPushButton#primaryBtn:pressed {{
    background-color: #008f36;
}}

/* Preset Filter Buttons */
QPushButton.presetBtn {{
    background-color: {SURFACE_LOW};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
}}
QPushButton.presetBtn:hover {{
    background-color: {SURFACE_HIGH};
    color: {TEXT_PRIMARY};
}}
QPushButton.presetBtn:checked {{
    background-color: {SURFACE_HIGHEST};
    color: {PRIMARY_BRIGHT};
    border: 1px solid {PRIMARY};
    font-weight: 600;
}}

/* Tables */
QTableWidget, QTableView {{
    background-color: {SURFACE_BASE};
    color: {TEXT_PRIMARY};
    gridline-color: {SURFACE_CONTAINER};
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 4px;
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    selection-background-color: {SURFACE_HIGHEST};
    selection-color: {PRIMARY_BRIGHT};
    outline: none;
}}
QTableWidget::item, QTableView::item {{
    padding: 4px 8px;
    border-bottom: 1px solid {SURFACE_CONTAINER};
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {SURFACE_HIGH};
    color: {TEXT_PRIMARY};
}}
QHeaderView::section {{
    background-color: {SURFACE_HIGH};
    color: {TEXT_MUTED};
    padding: 6px;
    border: none;
    border-right: 1px solid {BORDER_HAIRLINE};
    border-bottom: 1px solid {BORDER_HAIRLINE};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 4px;
    background: {SURFACE_HIGHEST};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {PRIMARY};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {TEXT_PRIMARY};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {PRIMARY_BRIGHT};
}}

/* Checkboxes */
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 2px;
    background: {SURFACE_BASE};
}}
QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border: 1px solid {PRIMARY};
}}

/* Group Boxes & Containers */
QGroupBox {{
    border: 1px solid {BORDER_HAIRLINE};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: {PRIMARY_BRIGHT};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {BORDER_HAIRLINE};
    background-color: {SURFACE};
    border-radius: 4px;
}}
QTabBar::tab {{
    background-color: {SURFACE_CONTAINER};
    color: {TEXT_MUTED};
    padding: 6px 14px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid {BORDER_HAIRLINE};
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {SURFACE};
    color: {PRIMARY_BRIGHT};
    border-bottom: 2px solid {PRIMARY};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background-color: {SURFACE_HIGH};
    color: {TEXT_PRIMARY};
}}

/* Status Bar */
QStatusBar {{
    background-color: {SURFACE_BASE};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER_HAIRLINE};
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
}}
"""
