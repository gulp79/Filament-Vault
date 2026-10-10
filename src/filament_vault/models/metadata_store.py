"""User metadata storage manager.

Stores custom user-generated tags, notes, collections, settings, and favorites
strictly separated from Bambu Studio's spools.json file.

Storage directory: user_data/
  - tags.json
  - notes.json
  - collections.json
  - settings.json
  - metadata.json (consolidated spool metadata mapping spool_id -> SpoolMetadata)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..core.logger import get_logger
from .spool import SpoolMetadata

logger = get_logger("metadata_store")


class MetadataStore:
    """Manages reading and writing user metadata safely and atomically."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._metadata_file = self.data_dir / "metadata.json"
        self._settings_file = self.data_dir / "settings.json"
        self._tags_file = self.data_dir / "tags.json"
        self._notes_file = self.data_dir / "notes.json"
        self._collections_file = self.data_dir / "collections.json"

        self._spool_meta: Dict[str, SpoolMetadata] = {}
        self._settings: Dict[str, Any] = {}
        self.load_all()

    def load_all(self) -> None:
        """Load user data from disk safely."""
        self._spool_meta = {}
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for sid, mdata in raw.items():
                        self._spool_meta[sid] = SpoolMetadata.from_dict(mdata)
            except Exception as e:
                logger.error(f"Failed to read metadata file: {e}")

        # Load settings
        self._settings = {
            "bambu_spools_path": "",
            "auto_sync": True,
            "sync_interval_seconds": 15,
            "currency_symbol": "$",
            "default_cost_per_kg": 20.0,
            "low_stock_threshold_percent": 20,
            "low_stock_threshold_grams": 200.0,
            "shelf_view_rows": 3,
            "shelf_view_spools_per_row": 8,
        }
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    self._settings.update(json.load(f))
            except Exception as e:
                logger.error(f"Failed to read settings file: {e}")

    def save_all(self) -> None:
        """Atomic write of metadata and user files."""
        # 1. metadata.json
        meta_dict = {sid: meta.to_dict() for sid, meta in self._spool_meta.items()}
        self._atomic_json_write(self._metadata_file, meta_dict)

        # 2. settings.json
        self._atomic_json_write(self._settings_file, self._settings)

        # 3. Export modular files for full backward compatibility & inspection:
        # tags.json -> dictionary of tag -> list of spool_ids
        tags_map: Dict[str, List[str]] = {}
        notes_map: Dict[str, str] = {}
        collections_map: Dict[str, List[str]] = {}

        for sid, meta in self._spool_meta.items():
            for t in meta.tags:
                tags_map.setdefault(t, []).append(sid)
            if meta.notes:
                notes_map[sid] = meta.notes
            for c in meta.collections:
                collections_map.setdefault(c, []).append(sid)

        self._atomic_json_write(self._tags_file, tags_map)
        self._atomic_json_write(self._notes_file, notes_map)
        self._atomic_json_write(self._collections_file, collections_map)

    def _atomic_json_write(self, target_path: Path, data: Any) -> None:
        """Write JSON using a temporary file and atomic replace to prevent corruption."""
        temp_path = target_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(target_path)
        except Exception as e:
            logger.error(f"Error saving {target_path.name}: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

    def get_metadata(self, spool_id: str) -> SpoolMetadata:
        """Get or create user metadata for a given spool_id."""
        if spool_id not in self._spool_meta:
            self._spool_meta[spool_id] = SpoolMetadata(spool_id=spool_id)
        return self._spool_meta[spool_id]

    def update_metadata(self, meta: SpoolMetadata) -> None:
        """Update metadata entry and save."""
        self._spool_meta[meta.spool_id] = meta
        self.save_all()

    def get_all_tags(self) -> List[str]:
        """Return sorted unique list of all tags used across spools."""
        tags = set()
        for meta in self._spool_meta.values():
            tags.update(meta.tags)
        return sorted(tags)

    def get_all_collections(self) -> List[str]:
        """Return sorted unique list of all collections defined."""
        colls = set()
        for meta in self._spool_meta.values():
            colls.update(meta.collections)
        return sorted(colls)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self.save_all()
