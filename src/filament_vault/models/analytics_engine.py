"""Analytics and Telemetry Engine.

Computes:
- Headcount and available filament mass (kg, %)
- Material distribution (PLA, PETG, ABS, TPU, etc.)
- Manufacturer distribution
- Color family distribution
- Spool fragmentation & duplicate analysis (e.g., multiple opened spools of identical material/color)
- Low stock analysis (<20% or <200g)
- Estimated print runway / remaining length in meters
- Inventory valuation
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from .spool import Spool, SpoolMetadata


class AnalyticsEngine:
    """Computes comprehensive telemetry metrics on spool collection."""

    @staticmethod
    def compute_summary(spools: List[Spool], default_price_per_kg: float = 20.0) -> Dict[str, Any]:
        """Compute key aggregate metrics for dashboard and telemetry strip."""
        total_spools = len(spools)
        if total_spools == 0:
            return {
                "total_spools": 0,
                "active_spools": 0,
                "sealed_spools": 0,
                "depleted_spools": 0,
                "total_weight_g": 0.0,
                "total_weight_kg": 0.0,
                "capacity_percent": 0.0,
                "ams_loaded_count": 0,
                "print_runway_hours": 0.0,
                "low_stock_count": 0,
                "total_length_m": 0.0,
                "estimated_valuation": 0.0,
            }

        total_weight_g = 0.0
        total_initial_g = 0.0
        total_length_m = 0.0
        active_count = 0
        sealed_count = 0
        depleted_count = 0
        ams_loaded = 0
        low_stock_count = 0

        for s in spools:
            rem_g = s.remaining_weight_g
            total_weight_g += rem_g
            init_g = s.initial_weight if s.initial_weight > 0 else 1000.0
            total_initial_g += init_g
            total_length_m += s.estimated_length_m

            if rem_g <= 50.0 or s.remain_percent <= 5:
                depleted_count += 1
            elif s.remain_percent >= 98 and rem_g >= 950.0:
                sealed_count += 1
            else:
                active_count += 1

            if s.is_ams_loaded:
                ams_loaded += 1

            if s.remain_percent < 20 or rem_g < 200.0:
                low_stock_count += 1

        capacity_pct = round((total_weight_g / total_initial_g) * 100.0, 1) if total_initial_g > 0 else 0.0
        total_weight_kg = round(total_weight_g / 1000.0, 2)
        # Assuming average consumption of 150g per print hour across workshop
        runway_hours = round(total_weight_g / 150.0, 1)
        estimated_val = round(total_weight_kg * default_price_per_kg, 2)

        return {
            "total_spools": total_spools,
            "active_spools": active_count,
            "sealed_spools": sealed_count,
            "depleted_spools": depleted_count,
            "total_weight_g": round(total_weight_g, 1),
            "total_weight_kg": total_weight_kg,
            "capacity_percent": capacity_pct,
            "ams_loaded_count": ams_loaded,
            "print_runway_hours": runway_hours,
            "low_stock_count": low_stock_count,
            "total_length_m": round(total_length_m, 1),
            "estimated_valuation": estimated_val,
        }

    @staticmethod
    def get_material_distribution(spools: List[Spool]) -> List[Dict[str, Any]]:
        """Return breakdown by material type sorted by weight desc."""
        by_mat: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "weight_g": 0.0})
        total_g = 0.0

        for s in spools:
            mat = s.material_type or "Unknown"
            w = s.remaining_weight_g
            by_mat[mat]["count"] += 1
            by_mat[mat]["weight_g"] += w
            total_g += w

        result = []
        for mat, data in by_mat.items():
            pct = round((data["weight_g"] / total_g) * 100.0, 1) if total_g > 0 else 0.0
            result.append({
                "material": mat,
                "count": int(data["count"]),
                "weight_kg": round(data["weight_g"] / 1000.0, 2),
                "weight_g": round(data["weight_g"], 1),
                "percentage": pct,
            })
        result.sort(key=lambda x: x["weight_g"], reverse=True)
        return result

    @staticmethod
    def get_brand_distribution(spools: List[Spool]) -> List[Dict[str, Any]]:
        """Return breakdown by manufacturer sorted by count desc."""
        by_brand: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "weight_g": 0.0})
        total_spools = len(spools)

        for s in spools:
            b = s.brand or "Unknown"
            by_brand[b]["count"] += 1
            by_brand[b]["weight_g"] += s.remaining_weight_g

        result = []
        for brand, data in by_brand.items():
            pct = round((data["count"] / total_spools) * 100.0, 1) if total_spools > 0 else 0.0
            result.append({
                "brand": brand,
                "count": int(data["count"]),
                "weight_kg": round(data["weight_g"] / 1000.0, 2),
                "percentage": pct,
            })
        result.sort(key=lambda x: x["count"], reverse=True)
        return result

    @staticmethod
    def get_color_family_distribution(spools: List[Spool]) -> List[Dict[str, Any]]:
        """Return breakdown by 13 color families."""
        by_fam: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "weight_g": 0.0})
        total_spools = len(spools)

        for s in spools:
            fam = s.color_family
            by_fam[fam]["count"] += 1
            by_fam[fam]["weight_g"] += s.remaining_weight_g

        result = []
        for fam, data in by_fam.items():
            pct = round((data["count"] / total_spools) * 100.0, 1) if total_spools > 0 else 0.0
            result.append({
                "family": fam,
                "count": int(data["count"]),
                "weight_kg": round(data["weight_g"] / 1000.0, 2),
                "percentage": pct,
            })
        result.sort(key=lambda x: x["count"], reverse=True)
        return result

    @staticmethod
    def detect_fragmentation_conflicts(spools: List[Spool]) -> List[Dict[str, Any]]:
        """Detect duplicate opened spools of identical material, series and color code."""
        groups: Dict[Tuple[str, str, str], List[Spool]] = defaultdict(list)
        for s in spools:
            key = (s.brand.lower(), s.series.lower(), s.color_code.lower())
            groups[key].append(s)

        conflicts = []
        for (brand, series, color), spool_list in groups.items():
            if len(spool_list) > 1:
                # Multiple spools of exact match
                open_spools = [sp for sp in spool_list if sp.remain_percent < 98]
                total_open_g = sum(sp.remaining_weight_g for sp in spool_list)
                first = spool_list[0]
                conflicts.append({
                    "title": f"{len(spool_list)} Spools: {first.brand} {first.series}",
                    "brand": first.brand,
                    "series": first.series,
                    "color_code": first.color_code,
                    "count": len(spool_list),
                    "open_count": len(open_spools),
                    "total_weight_g": round(total_open_g, 1),
                    "spool_ids": [sp.spool_id for sp in spool_list],
                    "recommendation": "Spools can be consolidated or prioritized in print queue to free drybox slots."
                })
        conflicts.sort(key=lambda x: x["count"], reverse=True)
        return conflicts
