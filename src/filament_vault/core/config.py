"""Path configuration and default directory resolution for Filament Vault."""

from __future__ import annotations
import os
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Return application directory where executable or script resides."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent.parent


def get_bambu_default_spools_path() -> Path:
    """Return default Bambu Studio spools.json location on Windows:
    %APPDATA%/BambuStudio/filament_inventory/spools.json
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "BambuStudio" / "filament_inventory" / "spools.json"
    return Path.home() / "AppData" / "Roaming" / "BambuStudio" / "filament_inventory" / "spools.json"


def get_user_data_dir() -> Path:
    """Return local user_data directory for storing metadata, tags, notes, and collections.
    
    Defaults to <app_dir>/user_data or %LOCALAPPDATA%/FilamentVault/user_data.
    Uses <app_dir>/user_data if writable (portable mode), else falls back to LocalAppData.
    """
    app_user_data = get_app_dir() / "user_data"
    try:
        app_user_data.mkdir(parents=True, exist_ok=True)
        # Test write
        test_file = app_user_data / ".write_test"
        test_file.touch()
        test_file.unlink()
        return app_user_data
    except Exception:
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            fallback = Path(local_appdata) / "FilamentVault" / "user_data"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        fallback = Path.home() / ".filament_vault" / "user_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
