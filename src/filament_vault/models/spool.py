"""Data models for Filament Vault.

Represents Spool records (immutable read-only from Bambu Studio) and
SpoolMetadata (user-defined tags, notes, collections, custom favorites).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from ..core.color_engine import classify_color_family, parse_hex_color, rgb_to_lab


@dataclass
class Spool:
    """Read-only spool entity loaded from Bambu Studio spools.json."""
    spool_id: str
    material_type: str
    series: str
    brand: str
    color_code: str
    color_name: str = ""
    net_weight: float = 1000.0  # current remaining weight in grams
    initial_weight: float = 1000.0
    spool_weight: float = 0.0  # empty tare spool mass
    remain_percent: int = 100
    diameter: float = 1.75
    setting_id: str = ""
    tray_id_name: str = ""
    tag_uid: str = ""
    entry_method: str = "manual"  # 'manual', 'ams_sync', etc.
    status: str = "active"
    cloud_synced: bool = False
    favorite: bool = False
    note: str = ""
    bound_ams_id: str = ""
    bound_dev_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    colors: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Derived fields
    color_family: str = field(init=False)
    lab: tuple[float, float, float] = field(init=False)

    def __post_init__(self) -> None:
        # Determine color family
        self.color_family = classify_color_family(self.color_code, self.series)
        r, g, b, _ = parse_hex_color(self.color_code)
        self.lab = rgb_to_lab(r, g, b)

    @property
    def remaining_weight_g(self) -> float:
        """Calculate remaining weight in grams using net_weight or remain_percent."""
        if self.net_weight > 0:
            return round(self.net_weight, 1)
        if self.initial_weight > 0 and self.remain_percent > 0:
            return round((self.initial_weight * self.remain_percent) / 100.0, 1)
        return 0.0

    @property
    def remaining_kg(self) -> float:
        """Calculate remaining weight in kilograms."""
        return round(self.remaining_weight_g / 1000.0, 3)

    @property
    def estimated_length_m(self) -> float:
        """Estimate remaining filament length in meters based on density and diameter.
        Standard density ~1.24 g/cm3 for PLA, ~1.27 g/cm3 for PETG.
        Volume per meter for 1.75mm: pi * (0.175/2)^2 * 100 = 2.405 cm3/m
        Grams per meter ~ 2.405 * 1.25 = ~3.0 g/m
        """
        density = 1.25
        mat = self.material_type.upper()
        if "PETG" in mat:
            density = 1.27
        elif "ABS" in mat or "ASA" in mat:
            density = 1.05
        elif "TPU" in mat:
            density = 1.21
        elif "PC" in mat:
            density = 1.20

        radius_cm = (self.diameter / 10.0) / 2.0
        area_cm2 = 3.14159265 * (radius_cm ** 2)
        weight_per_m = area_cm2 * 100.0 * density  # grams per meter
        if weight_per_m <= 0:
            return 0.0
        return round(self.remaining_weight_g / weight_per_m, 1)

    @property
    def display_name(self) -> str:
        """Formatted descriptive spool title."""
        title_parts = [self.brand, self.series or self.material_type]
        if self.color_name:
            title_parts.append(self.color_name)
        return " ".join(p for p in title_parts if p).strip()

    @property
    def is_ams_loaded(self) -> bool:
        """True if spool is presently bound to an AMS slot."""
        return bool(self.bound_ams_id or self.tray_id_name.startswith(("A", "B", "C", "D")))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Spool:
        """Factory constructor from Bambu Studio JSON dictionary entry."""
        # Clean numeric fields
        spool_id = str(data.get("spool_id") or data.get("id") or "")
        try:
            net_weight = float(data.get("net_weight", 1000.0) or 0.0)
        except (ValueError, TypeError):
            net_weight = 1000.0

        try:
            initial_weight = float(data.get("initial_weight", 1000.0) or 1000.0)
        except (ValueError, TypeError):
            initial_weight = 1000.0

        try:
            spool_weight = float(data.get("spool_weight", 0.0) or 0.0)
        except (ValueError, TypeError):
            spool_weight = 0.0

        try:
            remain_percent = int(data.get("remain_percent", 100) or 0)
        except (ValueError, TypeError):
            remain_percent = 100

        try:
            diameter = float(data.get("diameter", 1.75) or 1.75)
        except (ValueError, TypeError):
            diameter = 1.75

        color_code = str(data.get("color_code", "#CCCCCCFF"))
        colors_raw = data.get("colors") or []
        if isinstance(colors_raw, list):
            colors = [str(c) for c in colors_raw]
        else:
            colors = [color_code]

        return cls(
            spool_id=spool_id,
            material_type=str(data.get("material_type") or "Unknown").strip(),
            series=str(data.get("series") or data.get("material_type") or "Generic").strip(),
            brand=str(data.get("brand") or "Generic").strip(),
            color_code=color_code,
            color_name=str(data.get("color_name") or "").strip(),
            net_weight=net_weight,
            initial_weight=initial_weight,
            spool_weight=spool_weight,
            remain_percent=remain_percent,
            diameter=diameter,
            setting_id=str(data.get("setting_id") or "").strip(),
            tray_id_name=str(data.get("tray_id_name") or "").strip(),
            tag_uid=str(data.get("tag_uid") or "").strip(),
            entry_method=str(data.get("entry_method") or "manual").strip(),
            status=str(data.get("status") or "active").strip(),
            cloud_synced=bool(data.get("cloud_synced", False)),
            favorite=bool(data.get("favorite", False)),
            note=str(data.get("note") or "").strip(),
            bound_ams_id=str(data.get("bound_ams_id") or "").strip(),
            bound_dev_id=str(data.get("bound_dev_id") or "").strip(),
            created_at=str(data.get("created_at") or "").strip(),
            updated_at=str(data.get("updated_at") or "").strip(),
            colors=colors,
            raw_data=data,
        )


@dataclass
class SpoolMetadata:
    """User-generated custom metadata stored separately from Bambu Studio."""
    spool_id: str
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    collections: List[str] = field(default_factory=list)
    favorite: bool = False
    custom_location: str = ""  # e.g., 'Shelf 2', 'Drybox A'
    custom_price: Optional[float] = None
    custom_reorder_level: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spool_id": self.spool_id,
            "tags": self.tags,
            "notes": self.notes,
            "collections": self.collections,
            "favorite": self.favorite,
            "custom_location": self.custom_location,
            "custom_price": self.custom_price,
            "custom_reorder_level": self.custom_reorder_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpoolMetadata:
        return cls(
            spool_id=str(data.get("spool_id", "")),
            tags=list(data.get("tags") or []),
            notes=str(data.get("notes") or ""),
            collections=list(data.get("collections") or []),
            favorite=bool(data.get("favorite", False)),
            custom_location=str(data.get("custom_location") or ""),
            custom_price=data.get("custom_price"),
            custom_reorder_level=data.get("custom_reorder_level"),
        )
