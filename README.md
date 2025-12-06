# Spotify Extended Streaming History Analyzer

A tool to analyze Spotify Extended Streaming History data and generate visual reports.

## Setup

### Requirements

- Python 3.8 or higher
- uv (Python package manager)

### Installation

```bash
# Install dependencies
uv sync
```

## Usage

1. Download Extended Streaming History data from Spotify
2. Place JSON files in the `Spotify Extended Streaming History/` directory
3. Generate the report:

```bash
uv run python main.py
```

4. Open `output/report.html` in your browser
