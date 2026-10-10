"""Unit tests for Color Engine, Spool Models, and Metadata Storage."""

import os
import tempfile
from pathlib import Path
import pytest

from filament_vault.core.color_engine import (
    parse_hex_color,
    rgba_to_hex,
    rgb_to_lab,
    delta_e_ciede2000,
    classify_color_family,
    COLOR_FAMILIES,
)
from filament_vault.models.spool import Spool, SpoolMetadata
from filament_vault.models.filter_criteria import FilterCriteria
from filament_vault.models.metadata_store import MetadataStore
from filament_vault.models.analytics_engine import AnalyticsEngine


def test_color_hex_parsing():
    r, g, b, a = parse_hex_color("#00AE42FF")
    assert (r, g, b, a) == (0, 174, 66, 255)

    r, g, b, a = parse_hex_color("#FEC600")
    assert (r, g, b, a) == (254, 198, 0, 255)

    r, g, b, a = parse_hex_color("invalid")
    assert (r, g, b, a) == (128, 128, 128, 255)


def test_color_family_classification():
    # Green Bambu Lab
    assert classify_color_family("#00AE42FF") == "green"
    # Pure Yellow
    assert classify_color_family("#FEC600FF") == "yellow"
    # Deep Black
    assert classify_color_family("#000000FF") == "black"
    # Pure White
    assert classify_color_family("#FFFFFFFF") == "white"
    # Neutral Gray
    assert classify_color_family("#9B9EA0FF") == "gray"
    # Cyan
    assert classify_color_family("#A3D8E1FF") == "cyan"
    # Translucent
    assert classify_color_family("#A3D8E1AA", series_or_name="PLA Translucent") == "transparent"


def test_delta_e_ciede2000():
    # Identical colors must have delta-E 0
    lab1 = rgb_to_lab(0, 174, 66)
    lab2 = rgb_to_lab(0, 174, 66)
    assert delta_e_ciede2000(lab1, lab2) == 0.0

    # Slight variation should have small delta-E (< 5.0)
    lab3 = rgb_to_lab(0, 170, 68)
    de = delta_e_ciede2000(lab1, lab3)
    assert 0.0 < de < 5.0


def test_spool_model_parsing():
    raw = {
        "spool_id": "12345",
        "material_type": "PLA",
        "series": "PLA Basic",
        "brand": "Bambu Lab",
        "color_code": "#FEC600FF",
        "net_weight": 903.0,
        "initial_weight": 1000.0,
        "remain_percent": 90,
        "diameter": 1.75,
    }
    spool = Spool.from_dict(raw)
    assert spool.spool_id == "12345"
    assert spool.remaining_weight_g == 903.0
    assert spool.remaining_kg == 0.903
    assert spool.color_family == "yellow"
    assert spool.estimated_length_m > 200.0


def test_metadata_store_isolation():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        store = MetadataStore(tmp_path)

        meta = store.get_metadata("12345")
        assert meta.spool_id == "12345"
        meta.tags = ["Prototype", "Farm-A"]
        meta.notes = "Calibrated at 220C"
        meta.favorite = True
        store.update_metadata(meta)

        # Reload store and verify persistence
        new_store = MetadataStore(tmp_path)
        loaded_meta = new_store.get_metadata("12345")
        assert loaded_meta.favorite is True
        assert "Prototype" in loaded_meta.tags
        assert loaded_meta.notes == "Calibrated at 220C"
        assert "Prototype" in new_store.get_all_tags()


def test_filter_criteria():
    spool = Spool.from_dict({
        "spool_id": "100",
        "material_type": "PETG",
        "series": "PETG Basic",
        "brand": "Bambu Lab",
        "color_code": "#000000FF",
        "net_weight": 150.0,
        "remain_percent": 15,
    })
    meta = SpoolMetadata(spool_id="100", tags=["LowTemp"])

    # Matches PETG
    f1 = FilterCriteria(material="PETG")
    assert f1.matches(spool, meta) is True

    # Fails PLA
    f2 = FilterCriteria(material="PLA")
    assert f2.matches(spool, meta) is False

    # Low stock
    f3 = FilterCriteria(only_low_stock=True)
    assert f3.matches(spool, meta) is True

    # Free text search across tag
    f4 = FilterCriteria(query="LowTemp")
    assert f4.matches(spool, meta) is True


def test_analytics_engine():
    spools = [
        Spool.from_dict({
            "spool_id": "1",
            "material_type": "PLA",
            "series": "PLA Basic",
            "brand": "Bambu Lab",
            "color_code": "#00AE42FF",
            "net_weight": 800.0,
            "initial_weight": 1000.0,
            "remain_percent": 80,
        }),
        Spool.from_dict({
            "spool_id": "2",
            "material_type": "PLA",
            "series": "PLA Basic",
            "brand": "Bambu Lab",
            "color_code": "#00AE42FF",
            "net_weight": 100.0,
            "initial_weight": 1000.0,
            "remain_percent": 10,
        }),
    ]
    summary = AnalyticsEngine.compute_summary(spools)
    assert summary["total_spools"] == 2
    assert summary["total_weight_g"] == 900.0
    assert summary["low_stock_count"] == 1

    # Conflict detector should flag duplicate PLA Basic #00AE42FF
    conflicts = AnalyticsEngine.detect_fragmentation_conflicts(spools)
    assert len(conflicts) == 1
    assert conflicts[0]["count"] == 2
