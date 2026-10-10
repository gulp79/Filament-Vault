"""Filter and query criteria model for inventory search and presets."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from .spool import Spool, SpoolMetadata


@dataclass
class FilterCriteria:
    """Filter specifications for search and faceted browsing."""
    query: str = ""  # free-text search across brand, material, series, color name, tag UID, notes, tags
    material: Optional[str] = None
    brand: Optional[str] = None
    finish: Optional[str] = None
    color_family: Optional[str] = None
    collection: Optional[str] = None
    tag: Optional[str] = None
    only_favorites: bool = False
    only_ams_loaded: bool = False
    only_low_stock: bool = False  # e.g., remain_percent < 20 or net_weight < 200g
    max_mass_g: Optional[float] = None  # slider threshold
    target_hex_delta_e: Optional[str] = None  # target hex code for delta-E filtering
    max_delta_e: float = 15.0

    def matches(self, spool: Spool, meta: Optional[SpoolMetadata] = None) -> bool:
        """Check if a spool (and its metadata) matches all filter conditions."""
        # 1. Free-text search
        if self.query:
            q = self.query.strip().lower()
            text_match = (
                q in spool.brand.lower()
                or q in spool.material_type.lower()
                or q in spool.series.lower()
                or q in spool.color_name.lower()
                or q in spool.color_code.lower()
                or q in spool.tray_id_name.lower()
                or q in spool.tag_uid.lower()
                or q in spool.spool_id.lower()
                or (meta and any(q in t.lower() for t in meta.tags))
                or (meta and q in meta.notes.lower())
                or (meta and q in meta.custom_location.lower())
            )
            if not text_match:
                return False

        # 2. Material
        if self.material and self.material != "All":
            if self.material.upper() not in spool.material_type.upper():
                return False

        # 3. Brand
        if self.brand and self.brand != "All":
            if self.brand.lower() not in spool.brand.lower():
                return False

        # 4. Finish
        if self.finish and self.finish != "All":
            finish_lower = self.finish.lower()
            if finish_lower not in spool.series.lower():
                return False

        # 5. Color Family
        if self.color_family and self.color_family != "all":
            if spool.color_family.lower() != self.color_family.lower():
                return False

        # 6. Mass limit
        if self.max_mass_g is not None:
            if spool.remaining_weight_g > self.max_mass_g:
                return False

        # 7. Low stock
        if self.only_low_stock:
            if spool.remain_percent >= 20 and spool.remaining_weight_g >= 200:
                return False

        # 8. AMS loaded
        if self.only_ams_loaded:
            if not spool.is_ams_loaded:
                return False

        # 9. Favorites
        if self.only_favorites:
            fav = spool.favorite or (meta.favorite if meta else False)
            if not fav:
                return False

        # 10. Tag filter
        if self.tag:
            if not meta or self.tag not in meta.tags:
                return False

        # 11. Collection filter
        if self.collection:
            if not meta or self.collection not in meta.collections:
                return False

        return True
