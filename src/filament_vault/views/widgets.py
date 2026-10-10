"""Custom UI widgets for Filament Vault:
- SpoolVisualWidget: 2D radial filament winding spool graphic with gloss sheen and mass core
- SpoolCardWidget: Grid/Gallery card displaying color swatch, remaining percentage bar, RFID status
- ShelfSpoolWidget: Technical side-elevation spool profile for the Shelf View
- SwatchWidget: Crisp rounded swatch for the Color Wall
"""

from __future__ import annotations
import math
from typing import Optional
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QLinearGradient,
    QRadialGradient,
    QFont,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
)

from ..models.spool import Spool
from ..core.color_engine import parse_hex_color, get_contrast_text_color
from ..resources.theme import (
    SURFACE_CONTAINER,
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


class SpoolVisualWidget(QWidget):
    """Accurately renders the radial winding filament spool graphic from the Stitch mockups.
    Features:
    - Outer spool polycarbonate flange rim
    - Scaled winding circle corresponding to remaining weight percentage
    - Specular highlights / gloss gradient reflection
    - Central polycarbonate core hub displaying net remaining grams
    """

    def __init__(self, spool: Optional[Spool] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spool = spool
        self.setMinimumSize(180, 180)

    def set_spool(self, spool: Optional[Spool]) -> None:
        self.spool = spool
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 16
        center_x = w / 2.0
        center_y = h / 2.0
        radius = size / 2.0

        if not self.spool:
            # Placeholder empty ring
            pen = QPen(QColor(BORDER_HAIRLINE), 2)
            painter.setPen(pen)
            painter.setBrush(QColor(SURFACE_CONTAINER))
            painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
            return

        r, g, b, _ = parse_hex_color(self.spool.color_code)
        filament_color = QColor(r, g, b)

        # 1. Outer rim / flange
        outer_pen = QPen(QColor(SURFACE_HIGHEST), 3)
        painter.setPen(outer_pen)
        painter.setBrush(QColor(SURFACE_BASE))
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # 2. Filament Winding Track
        # The winding thickness depends on remaining percent (0% -> core radius, 100% -> rim radius)
        core_radius = radius * 0.42
        max_winding_width = radius - core_radius - 6.0
        pct = max(0.0, min(100.0, float(self.spool.remain_percent))) / 100.0
        current_winding_width = max(4.0, max_winding_width * pct)

        # Draw empty track background
        empty_pen = QPen(QColor(SURFACE_CONTAINER), max_winding_width)
        empty_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(empty_pen)
        empty_radius = core_radius + (max_winding_width / 2.0)
        painter.drawEllipse(QPointF(center_x, center_y), empty_radius, empty_radius)

        # Draw filament material ring
        filament_radius = core_radius + (current_winding_width / 2.0)
        filament_pen = QPen(filament_color, current_winding_width)
        filament_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(filament_pen)
        painter.drawEllipse(QPointF(center_x, center_y), filament_radius, filament_radius)

        # 3. Specular Highlight arc across the winding
        specular_grad = QLinearGradient(
            center_x - radius, center_y - radius, center_x + radius, center_y + radius
        )
        specular_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
        specular_grad.setColorAt(0.45, QColor(255, 255, 255, 50))
        specular_grad.setColorAt(0.55, QColor(255, 255, 255, 0))
        specular_pen = QPen(QBrush(specular_grad), current_winding_width)
        painter.setPen(specular_pen)
        painter.drawEllipse(QPointF(center_x, center_y), filament_radius, filament_radius)

        # 4. Central Hub Core
        core_pen = QPen(QColor(SURFACE_HIGH), 2)
        painter.setPen(core_pen)
        hub_grad = QRadialGradient(center_x, center_y, core_radius)
        hub_grad.setColorAt(0.0, QColor(SURFACE_CONTAINER))
        hub_grad.setColorAt(1.0, QColor(SURFACE_BASE))
        painter.setBrush(hub_grad)
        painter.drawEllipse(QPointF(center_x, center_y), core_radius, core_radius)

        # 5. Core Text Readout: Mass Net in grams
        painter.setPen(QColor(TEXT_MUTED))
        font_label = QFont("JetBrains Mono", 8)
        painter.setFont(font_label)
        painter.drawText(
            QRectF(center_x - core_radius, center_y - 20, core_radius * 2, 14),
            Qt.AlignmentFlag.AlignCenter,
            "NET MASS",
        )

        painter.setPen(QColor(PRIMARY_BRIGHT))
        font_value = QFont("JetBrains Mono", 12, QFont.Weight.Bold)
        painter.setFont(font_value)
        mass_text = f"{int(self.spool.remaining_weight_g)}g"
        painter.drawText(
            QRectF(center_x - core_radius, center_y - 4, core_radius * 2, 18),
            Qt.AlignmentFlag.AlignCenter,
            mass_text,
        )

        painter.setPen(QColor(TEXT_MUTED))
        font_sub = QFont("JetBrains Mono", 7)
        painter.setFont(font_sub)
        init_text = f"/{int(self.spool.initial_weight)}g"
        painter.drawText(
            QRectF(center_x - core_radius, center_y + 14, core_radius * 2, 12),
            Qt.AlignmentFlag.AlignCenter,
            init_text,
        )


class SpoolCardWidget(QFrame):
    """Grid card for inventory explorer with color swatch, progress bar, and metrics."""

    clicked = Signal(str)  # Emits spool_id

    def __init__(self, spool: Spool, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spool = spool
        self.setObjectName("spoolCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Style card
        self.setStyleSheet(f"""
            QFrame#spoolCard {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 4px;
            }}
            QFrame#spoolCard:hover {{
                background-color: {SURFACE_HIGH};
                border: 1px solid {PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header: Material Chip & AMS/RFID Badge
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        mat_lbl = QLabel(f" {spool.material_type} ")
        mat_lbl.setStyleSheet(f"""
            background-color: {SURFACE_BASE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_HAIRLINE};
            border-radius: 3px;
            font-family: 'JetBrains Mono';
            font-size: 10px;
            font-weight: bold;
        """)
        header_row.addWidget(mat_lbl)
        header_row.addStretch()

        if spool.is_ams_loaded:
            ams_lbl = QLabel(f"AMS: {spool.tray_id_name or 'LOADED'}")
            ams_lbl.setStyleSheet(f"""
                color: {PRIMARY_BRIGHT};
                font-family: 'JetBrains Mono';
                font-size: 10px;
                font-weight: bold;
            """)
            header_row.addWidget(ams_lbl)
        elif spool.tag_uid:
            nfc_lbl = QLabel("RFID")
            nfc_lbl.setStyleSheet(f"""
                color: {SECONDARY};
                font-family: 'JetBrains Mono';
                font-size: 10px;
            """)
            header_row.addWidget(nfc_lbl)

        layout.addLayout(header_row)

        # Center Graphic: Radial spool miniature
        self.visual = SpoolVisualWidget(spool, self)
        self.visual.setMinimumSize(120, 120)
        self.visual.setMaximumHeight(130)
        layout.addWidget(self.visual, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title & Series
        brand_lbl = QLabel(spool.brand)
        brand_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(brand_lbl)

        series_lbl = QLabel(spool.series or spool.material_type)
        series_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 13px;")
        series_lbl.setWordWrap(True)
        layout.addWidget(series_lbl)

        # Color strip & Hex
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        swatch = QFrame()
        swatch.setFixedSize(14, 14)
        swatch.setStyleSheet(f"""
            background-color: {spool.color_code};
            border: 1px solid {BORDER_HAIRLINE};
            border-radius: 3px;
        """)
        color_row.addWidget(swatch)

        hex_lbl = QLabel(spool.color_code[:7])
        hex_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 11px;")
        color_row.addWidget(hex_lbl)

        color_row.addStretch()
        pct_lbl = QLabel(f"{spool.remain_percent}%")
        pct_color = PRIMARY_BRIGHT if spool.remain_percent >= 20 else ERROR
        pct_lbl.setStyleSheet(f"color: {pct_color}; font-family: 'JetBrains Mono'; font-weight: bold; font-size: 12px;")
        color_row.addWidget(pct_lbl)
        layout.addLayout(color_row)

        # Progress bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(spool.remain_percent)
        bar.setTextVisible(False)
        bar.setFixedHeight(4)
        bar_color = PRIMARY if spool.remain_percent >= 20 else ERROR
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {SURFACE_BASE};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(bar)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.spool.spool_id)
        super().mousePressEvent(event)


class ShelfSpoolWidget(QWidget):
    """Side profile vertical view of a spool standing on a storage shelf.
    Mimics physical spools on an organized filament rack.
    Width: 38px, Height: 120px.
    """

    clicked = Signal(str)

    def __init__(self, spool: Spool, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spool = spool
        self.setFixedSize(48, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{spool.brand} {spool.series}\nColor: {spool.color_code}\nRemaining: {spool.remaining_weight_g}g ({spool.remain_percent}%)")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r, g, b, _ = parse_hex_color(self.spool.color_code)
        filament_color = QColor(r, g, b)

        # Outer spool rim flanges (left and right edges)
        painter.setPen(QPen(QColor(BORDER_HAIRLINE), 1))
        painter.setBrush(QColor(SURFACE_HIGHEST))
        # Left flange
        painter.drawRoundedRect(QRectF(4, 4, 6, h - 8), 2, 2)
        # Right flange
        painter.drawRoundedRect(QRectF(w - 10, 4, 6, h - 8), 2, 2)

        # Center filament barrel
        # Fill height depends on remaining percent
        pct = max(0.05, min(1.0, self.spool.remain_percent / 100.0))
        filament_h = (h - 24) * pct
        filament_y = 12 + ((h - 24) - filament_h)

        # Empty core void
        painter.setBrush(QColor(SURFACE_BASE))
        painter.drawRect(QRectF(10, 12, w - 20, h - 24))

        # Filament wound material
        painter.setBrush(filament_color)
        painter.drawRect(QRectF(10, filament_y, w - 20, filament_h))

        # Highlight gradient
        grad = QLinearGradient(10, 0, w - 10, 0)
        grad.setColorAt(0.0, QColor(0, 0, 0, 70))
        grad.setColorAt(0.5, QColor(255, 255, 255, 40))
        grad.setColorAt(1.0, QColor(0, 0, 0, 70))
        painter.setBrush(grad)
        painter.drawRect(QRectF(10, filament_y, w - 20, filament_h))

        # Bottom label: Remaining grams
        painter.setPen(QColor(TEXT_PRIMARY))
        font = QFont("JetBrains Mono", 7)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, h - 14, w, 12),
            Qt.AlignmentFlag.AlignCenter,
            f"{int(self.spool.remaining_weight_g)}g",
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.spool.spool_id)
        super().mousePressEvent(event)


class SwatchWidget(QFrame):
    """Rounded industrial swatch widget for the Color Explorer."""

    clicked = Signal(str)  # Emits color hex or spool_id

    def __init__(
        self,
        spool: Spool,
        delta_e: Optional[float] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.spool = spool
        self.delta_e = delta_e
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE_CONTAINER};
                border: 1px solid {BORDER_HAIRLINE};
                border-radius: 6px;
                padding: 6px;
            }}
            QFrame:hover {{
                border: 1px solid {PRIMARY_BRIGHT};
                background-color: {SURFACE_HIGH};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Delta-E badge if comparing
        if self.delta_e is not None:
            de_lbl = QLabel(f"ΔE {self.delta_e:.1f}")
            de_color = PRIMARY_BRIGHT if self.delta_e < 2.0 else SECONDARY if self.delta_e < 10.0 else TEXT_MUTED
            de_lbl.setStyleSheet(f"color: {de_color}; font-family: 'JetBrains Mono'; font-size: 10px; font-weight: bold;")
            layout.addWidget(de_lbl, alignment=Qt.AlignmentFlag.AlignRight)

        # Color preview square
        swatch_box = QFrame()
        swatch_box.setMinimumHeight(60)
        swatch_box.setStyleSheet(f"""
            background-color: {spool.color_code};
            border-radius: 4px;
            border: 1px solid {BORDER_HAIRLINE};
        """)
        layout.addWidget(swatch_box)

        # Labels
        name_lbl = QLabel(spool.series)
        name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 11px;")
        layout.addWidget(name_lbl)

        code_lbl = QLabel(spool.color_code[:7])
        code_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono'; font-size: 10px;")
        layout.addWidget(code_lbl)

        fam_lbl = QLabel(spool.color_family.upper())
        fam_lbl.setStyleSheet(f"color: {TERTIARY}; font-family: 'JetBrains Mono'; font-size: 9px;")
        layout.addWidget(fam_lbl)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.spool.spool_id)
        super().mousePressEvent(event)
