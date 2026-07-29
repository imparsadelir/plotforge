# PlotForge

Desktop application for creating publication-quality academic charts.

## Status

Under active development. Phase 0 complete: project structure and embedded Matplotlib canvas working.

## Tech Stack

- PySide6 (GUI)
- Matplotlib (rendering)
- Pandas / NumPy (data handling)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Linux note

If Qt fails to start with an `xcb` platform plugin error:

```bash
sudo apt install libxcb-cursor0
```

## Project Structure

```
plotforge/
├── core/          # Business logic (no GUI dependencies)
│   ├── io/        # File readers (Excel, CSV)
│   ├── models/    # Data models and plot configuration
│   ├── plotting/  # Chart renderers
│   ├── analysis/  # Curve fitting and regression
│   └── export/    # Output to PDF, PNG, SVG
├── gui/           # PySide6 interface
│   ├── panels/    # Side panels
│   └── dialogs/   # Popup windows
├── resources/     # Icons and styles
└── tests/         # Unit tests
```