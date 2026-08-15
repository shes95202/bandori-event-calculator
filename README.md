# Bandori Event Calculator

A Windows desktop calculator for tracking BanG Dream! Girls Band Party! event pace using live event data from [Bestdori](https://bestdori.com/).

The application retrieves current event cutoffs and Bestdori predictions, then calculates how much Event Point progress is needed to reach selected ranking and pace targets.

## Features

- Windows desktop GUI built with PySide6
- JP and TW server support
- Automatic current-event detection
- Automatic Bestdori data loading on startup
- Manual Bestdori refresh
- Cached JP/TW data for instant server switching
- Current cutoff display
- Bestdori predicted cutoff display
- Event progress calculation
- Current pace projected final score
- Ranking target calculations
- Pace / interval target calculations
- Required games calculation
- Required boosts calculation
- Required boost refills
- Required stars
- Estimated play time
- Separate JP and TW player progress
- Persistent player settings across application restarts
- Portable `settings.json` suitable for synchronization with Synology Drive or other cloud storage

## Supported Ranking Targets

### JP

- T500
- T1000
- T2000

Pace benchmarks:

- T2000
- Average of T500 and T1000 predictions

### TW

- T100
- T500
- T1000

Pace benchmarks:

- Average of T100 and T500 predictions
- Q1 between T100 and T500

## Screenshots

![Bandori Event Calculator](docs/screenshot.png)

## How It Works

The calculator retrieves event information from Bestdori and combines it with two values entered by the user:

- **Current Score** — your current Event Points
- **Average Score per Game** — the average Event Points earned per game

The application then calculates two types of targets.

### Pace Targets

Pace targets answer:

> How much do I need to play now to catch up with the expected progress at the current point of the event?

The expected score is calculated from:

```text
Predicted Final Score × Current Event Progress
```

The calculator then shows:

- Current cutoff
- Predicted cutoff
- Expected score at the current event progress
- Whether you are ahead or behind
- Remaining Event Points
- Required games
- Required boosts
- Required refills
- Required stars
- Estimated play time

### Ranking Targets

Ranking targets answer:

> How much more do I need to play before the event ends to reach the predicted final cutoff?

These calculations use the predicted final score as the target.

## Player Settings

Player input is saved automatically to:

```text
settings.json
```

The file is stored next to `BandoriEventCalculator.exe`.

Example:

```json
{
    "JP": {
        "current_score": 1243245,
        "average_score": 20235
    },
    "TW": {
        "current_score": 0,
        "average_score": 0
    }
}
```

Because the settings file is portable, the application can be placed inside a synchronized folder such as Synology Drive:

```text
Synology Drive/
└── Bandori Event Calculator/
    ├── BandoriEventCalculator.exe
    └── settings.json
```

This allows player progress to be shared across multiple computers.

> Avoid editing the same `settings.json` from multiple computers at the same time, as this may cause synchronization conflicts.

## Download

Prebuilt Windows releases are available from the GitHub **Releases** page.

Download:

```text
BandoriEventCalculator.exe
```

No Python installation is required for the prebuilt Windows version.

When the application starts, it automatically retrieves the latest JP and TW event information from Bestdori.

## Development

### Requirements

- Python 3
- PySide6
- Playwright
- Chromium
- requests

Clone the repository:

```powershell
git clone https://github.com/shes95202/bandori-event-calculator.git
cd bandori-event-calculator
```

Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
pip install -e .
```

Install Playwright Chromium:

```powershell
playwright install chromium
```

Run the GUI:

```powershell
bandori-event-calculator-gui
```

or:

```powershell
python run_gui.py
```

## Tests

Run the test suite with:

```powershell
pytest
```

## Building the Windows Executable

Install PyInstaller:

```powershell
pip install pyinstaller
```

Bundle Chromium for Playwright:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="0"
playwright install chromium
```

Build the application:

```powershell
pyinstaller --noconfirm --clean --onefile --windowed `
    --name BandoriEventCalculator `
    run_gui.py
```

The executable will be created at:

```text
dist/BandoriEventCalculator.exe
```

## Application Data

The application stores different types of data in different locations.

### Player Progress

Stored next to the executable:

```text
settings.json
```

This file can be synchronized between computers.

### Playwright Browser Profile

The Chromium profile used for Bestdori is stored locally on each Windows computer:

```text
%LOCALAPPDATA%\BandoriEventCalculator\playwright-profile
```

The browser profile is intentionally not stored next to the executable and does not need to be synchronized.

## Known Limitations

- Challenge Live-specific calculations are not implemented yet.
- Bestdori prediction retrieval depends on the current Bestdori Event Tracker website structure.
- The current prebuilt release targets Windows.
- An internet connection is required when retrieving Bestdori data.

## Data Source

Event information, cutoff data, and predictions are retrieved from:

**Bestdori**

This project is an independent tool and is not affiliated with Bestdori, Bushiroad, Craft Egg, or BanG Dream!.

## Version

Current release:

```text
v0.1.0
```