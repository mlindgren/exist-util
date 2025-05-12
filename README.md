# Daylio Sync for Exist.io

This repository contains a Python script for importing and syncing data from [Daylio](https://daylio.net/) journal entries to [Exist.io](https://exist.io/). It allows you to process Daylio CSV exports, filter activities, and sync moods and activities to your Exist.io account.

Daylio does not store entries entries in the cloud (except for iCloud backups which are stored in an opaque format), and has no API. Therefore, you must manually export your Daylio entries to CSV and use the script to process them.

The name of the repository, `exist-util`, is generic because I might add more utilities in the future, but currently I have no specific plans.

## Features

- Import Daylio journal entries from exported CSV files.
- Filter activities based on a configurable list.
- Sync moods and activities to Exist.io.
- Create custom attributes for activities in Exist.io.
- Dry-run mode for previewing changes before syncing.

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

- `--sync-moods`: Sync moods to Exist.io.
- `--sync-activities`: Sync activities to Exist.io.
- `--create-activity-tags`: Create custom attributes for each activity in Exist.io. (You must do this before syncing activities for the first time.)
- `--dry-run`, `-d`: Preview the changes without syncing.

### Example Commands

1. Import a Daylio CSV file and sync moods:
   ```bash
   python daylio.py daylio_export.csv --sync-moods
   ```

2. Create custom attributes for activities:
   ```bash
   python daylio.py daylio_export.csv --create-activity-tags
   ```

3. Sync activities with a dry run:
   ```bash
   python daylio.py daylio_export.csv --sync-activities --dry-run
   ```

## Configuration

### secrets.json

This file contains your Exist.io API credentials. Example:

```json
{
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "developerAccessToken": "your-access-token",
    "developerRefreshToken": "your-refresh-token"
}
```

### config.json

This specifies activities to filter out during import. Example:

```json
{
    "filter_activities": ["secret_activity"]
}
```