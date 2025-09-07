# Daylio Sync for Exist.io

This repository contains a Python script for importing and syncing data from [Daylio](https://daylio.net/) journal entries to [Exist.io](https://exist.io/). It allows you to process Daylio CSV exports, filter activities, and sync moods and activities to your Exist.io account.

Daylio does not store entries entries in the cloud (except for iCloud backups which are stored in an opaque format), and has no API. Therefore, you must manually export your Daylio entries to CSV and use the script to process them.

The name of the repository, `exist-util`, is generic because I might add more utilities in the future, but currently I have no specific plans.

## Features

- Import Daylio journal entries from exported CSV files
- Configurable mood rating mapping (can override default values in config)
- Filter activities based on a configurable list
- Organize activities into custom groups for better categorization in Exist.io
- Incremental sync: only process entries since the last successful sync
- Dry-run mode for previewing changes before syncing

## Requirements

- Python 3.10 or later
- Dependencies listed in [`requirements.txt`](requirements.txt)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/exist-util.git
   cd exist-util
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create and configure the `secrets.json` and `config.json` files:
   - Copy the sample files:
     ```bash
     cp secrets.sample.json secrets.json
     cp config.sample.json config.json
     ```
   - Edit secrets.json with your Exist.io API credentials.
   - Edit config.json to specify activities to filter.

## Usage

Run the script with the following options:

```bash
python daylio.py <file_path> [options]
```

### Positional Arguments

- `file_path`: Path to the Daylio CSV file to import.

### Optional Arguments

- `--dry-run`, `-d`: Preview the changes without syncing.
- `--since SINCE_DATE`, `--since-date SINCE_DATE`: Only sync entries on or after this date (YYYY-MM-DD). Overrides stored last sync date if provided.

### Example Commands

1. **Full sync** (recommended - does everything automatically):
   ```bash
   python daylio.py daylio_export.csv
   ```

2. **Dry run** to see what would be synced:
   ```bash
   python daylio.py daylio_export.csv --dry-run
   ```

3. **Sync only recent entries** since a specific date:
   ```bash
   python daylio.py daylio_export.csv --since 2024-01-01
   ```

The script automatically tracks the last successful sync date in `.last_sync_date`. On subsequent runs, only entries from that date forward will be processed. Use `--since` to override this behavior.

## Configuration

- **`secrets.json`** contains client secrets necessary to use the Exist API.
- **`config.json`** contains configuration for filtering hidden activities and specifying which groups activities belong to.

See the corresponding `secrets.sample.json` and `config.sample.json` files for examples.

### Configuration Options

- **`filter_activities`**: List of activity names to exclude from sync
- **`mood_rating_map`**: Override default Daylio mood name to numeric rating mapping. If omitted, defaults are used. Unmapped moods are skipped with warnings.
- **`activity_groups`**: Map activity names to Exist.io attribute groups for better organization. Activities not listed default to the "custom" group.