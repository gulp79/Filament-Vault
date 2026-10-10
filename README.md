# Filament Vault

**Filament Vault** is an advanced desktop inventory explorer for Bambu Studio 3D printer filament inventories.

Engineered with dark-mode first technical aesthetics inspired by Grafana, VS Code, and modern CAD software, it provides deep search, smart color classification, physical shelf visualization, duplicate remnant analysis, and real-time telemetry while keeping 100% full compatibility with Bambu Studio.

---

## 🔒 Source of Truth & Zero-Modification Guarantee

Bambu Studio remains the authoritative source of inventory data at:
`%APPDATA%/BambuStudio/filament_inventory/spools.json`

- **Read-Only Access**: Filament Vault opens this file strictly in read-only mode.
- **Never Modifies**: It will **never** overwrite, alter, reformat, or inject tags into Bambu Studio files.
- **Independent User Metadata**: Custom user tags, notes, collections, custom physical rack locations, and favorites are stored independently in `user_data/`:
  - `user_data/tags.json`
  - `user_data/notes.json`
  - `user_data/collections.json`
  - `user_data/settings.json`
  - `user_data/metadata.json`
- **Live File-Change Detection**: Automatically monitors `spools.json` via `QFileSystemWatcher` and reloads immediately when Bambu Studio writes updates.

---

## ✨ Features

1. **Engineering KPI Dashboard**
   - Active, sealed, and depleted headcount tracking
   - Net material mass available (kg & percentage)
   - AMS slot occupancy and telemetry status
   - Print runway hours and continuous feed distance estimation
   - Low stock warnings (<20% or <200g remaining)

2. **Inventory Explorer (4 Viewing Modes)**
   - **Table View**: High-density telemetric tabular layout with sorting and instant search.
   - **Grid View**: Spool cards featuring simulated 2D radial filament winding graphics with gloss sheen.
   - **Shelf View**: Physical vertical spool profiles on storage rack levels.
   - **Gallery View**: High-contrast chromatic cards.

3. **Smart Color Engine & Discovery Wall**
   - 13 Color Family Classification: *red, orange, yellow, green, cyan, blue, purple, pink, brown, gray, white, black, transparent*.
   - CIEDE2000 ($\Delta E$) Color Difference Calculator (D65 standard illuminant).
   - Chromatic Similarity Wall: Ranks your entire inventory against any selected target color.

4. **Telemetry & Cost Intelligence**
   - Material and manufacturer breakdown tables.
   - Spool Fragmentation & Redundancy Alert Engine (flags open split spools of identical material).
   - One-click CSV export of entire inventory.

5. **Spool Details & User Metadata Editor**
   - Comprehensive factory parameter inspection (NFC RFID Tag UID, Setting ID, Tray ID, Tare weight).
   - Rich user metadata editor with tag management, notes, and collections.

---

## 🛠️ Technology Stack

- **Language**: Python 3.12 / 3.13
- **GUI Framework**: PySide6 (Qt for Python)
- **Architecture**: Model-View-Controller (MVC)
- **Typing & Quality**: Type hints across all modules, structured logging, pytest test suite.
- **Offline**: Zero external cloud or internet dependencies.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+ (or Python 3.13)
- Windows 10/11

### Installation

1. Clone or extract the repository:
   ```powershell
   cd "Filament Vault"
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Launch the application:
   ```powershell
   $env:PYTHONPATH="src"
   python -m filament_vault
   ```

---

## 🧪 Running Automated Tests

Run the test suite with `pytest`:
```powershell
$env:PYTHONPATH="src"
pytest tests/
```

---

## 📦 Building Single Windows Executable

### Option A: Using Nuitka (Recommended & Configured in CI)

```powershell
pip install nuitka zstandard ordered-set
python -m nuitka --standalone --onefile --enable-plugin=pyside6 --windows-console-mode=disable --include-package=filament_vault --output-filename=FilamentVault.exe --output-dir=dist src/filament_vault/__main__.py
```

### Option B: Using PyInstaller

```powershell
pip install pyinstaller
pyinstaller FilamentVault.spec
```
The compiled single executable will be located in `dist/FilamentVault.exe`.

---

## 🤖 GitHub Actions Automated Releases

A GitHub Actions workflow is included at `.github/workflows/build_release.yml`. When you push a new tag (e.g. `v2.4.0`), GitHub Actions will:
1. Check out code and set up Python 3.13.
2. Run the test suite.
3. Compile the standalone executable using Nuitka.
4. Publish the single `.exe` binary to the GitHub Release.

---

## 📄 License

MIT License. Designed and built for Bambu Lab users and 3D printing enthusiasts.
