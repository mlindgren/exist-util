#!/usr/bin/python
"""
Module for importing Daylio journal entries from an exported CSV file.
"""

import argparse
import csv
from dataclasses import dataclass
import datetime
import json
import sys
from typing import List, Optional
from pathlib import Path

import exist_client

CONFIG = json.load(open('config.json'))

# Default Daylio mood name to rating mapping. Can be overridden in config.json
# by providing a key "mood_rating_map" with the same structure.
DEFAULT_MOOD_RATING_MAP = {
    "awful": 1,
    "bad": 3,
    "meh": 5,
    "good": 7,
    "rad": 9,
}

MOOD_RATING_MAP = CONFIG.get('mood_rating_map', DEFAULT_MOOD_RATING_MAP)

# Activity groups mapping (group -> list of activity names) loaded from config.
GROUP_CONFIG = CONFIG.get('activity_groups', {})

# Inverted mapping: activity name -> group name, used when creating attributes.
ACTIVITY_TO_GROUP = {}
for _group, _activities in GROUP_CONFIG.items():
    for _activity in _activities:
        if _activity in ACTIVITY_TO_GROUP and ACTIVITY_TO_GROUP[_activity] != _group:
            print(f"Warning: Activity '{_activity}' appears in multiple groups ('{ACTIVITY_TO_GROUP[_activity]}' and '{_group}'). Using first.", file=sys.stderr)
            continue
        ACTIVITY_TO_GROUP[_activity] = _group

GLOBAL_ACTIVITY_LIST = set()

LAST_SYNC_FILE = '.last_sync_date'

def read_last_sync_date() -> Optional[datetime.date]:
    """Reads the last sync date from disk if present."""
    p = Path(LAST_SYNC_FILE)
    if not p.exists():
        return None
    try:
        content = p.read_text().strip()
        if not content:
            return None
        return datetime.date.fromisoformat(content)
    except Exception as e:
        print(f"Warning: Couldn't read last sync date ('{e}'), ignoring.", file=sys.stderr)
        return None

def write_last_sync_date(d: datetime.date):
    try:
        Path(LAST_SYNC_FILE).write_text(d.isoformat())
    except Exception as e:
        print(f"Warning: Failed to write last sync date ('{e}').", file=sys.stderr)

def normalize_activity_name(activity: str) -> str:
    """Normalize activity name for Exist.io attribute creation/updates"""
    return (activity.replace(' ', '_')
                    .replace('/', '')
                    .replace('&', '')
                    .replace('(', '')
                    .replace(')', '')
                    .lower())

@dataclass
class DaylioEntry:
    """
    Represents a single Daylio journal entry.
    """
    date: datetime.date
    mood_name: str
    mood_rating: Optional[int]
    activities: List[str]
    note: str

def import_daylio_csv(file_path: str) -> List[DaylioEntry]:
    """
    Imports Daylio journal entries from a CSV file.
    """
    entries = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date = datetime.date.fromisoformat(row['full_date'])
            mood_name = row['mood']
            if mood_name in MOOD_RATING_MAP:
                mood_rating = MOOD_RATING_MAP[mood_name]
            else:
                print(f"Warning: Unmapped mood '{mood_name}' on {date}, skipping mood for that day.", file=sys.stderr)
                mood_rating = None

            activities = row['activities'].split(' | ')

            # Removed activities that are filtered in the config
            activities = [activity for activity in activities if activity not in CONFIG['filter_activities']]
            GLOBAL_ACTIVITY_LIST.update(set(activities))
            GLOBAL_ACTIVITY_LIST.discard('') # Remove spurious empty activities

            note = row['note']
            entry = DaylioEntry(date, mood_name, mood_rating, activities, note)
            entries.append(entry)
    return entries

def create_activity_tags():
    for activity in GLOBAL_ACTIVITY_LIST:
        group = ACTIVITY_TO_GROUP.get(activity, '')
        exist_client.create_attribute(activity, exist_client.ValueType.BOOLEAN, 'custom', group, False)

def get_missing_activity_attributes(activities):
    """Check which activity attributes don't exist yet in Exist.io"""
    # Normalize activity names same way as in sync
    normalized_activities = []
    for activity in activities:
        if activity == '':
            continue
        activity_norm = normalize_activity_name(activity)
        normalized_activities.append(activity_norm)
    
    # If no activities, skip the API call
    if not normalized_activities:
        return []
    
    # Get existing attributes with limit set to double the number of unique activity names.
    # This is to handle the case where there are more activity tags in the user's Exist account
    # than there are Daylio activities, which could happen if the user deleted or renamed activities
    # in Daylio.
    limit = len(normalized_activities) * 2
    existing_attrs = exist_client.list_attributes(limit=limit)
    existing_names = {attr['name'] for attr in existing_attrs}
    
    missing = [activity for activity in normalized_activities if activity not in existing_names]
    return missing

def sync_all(entries, dry_run=False):
    """Perform complete sync: create missing attributes, sync moods, sync activities"""
    print("Starting comprehensive sync...")
    
    # Step 1: Check and create missing activity attributes
    print("\n1. Checking activity attributes...")
    all_activities = set()
    for entry in entries:
        all_activities.update(entry.activities)
    
    missing_attrs = get_missing_activity_attributes(all_activities)
    if missing_attrs:
        print(f"   Found {len(missing_attrs)} missing activity attributes: {missing_attrs}")
        if dry_run:
            print("   [DRY RUN] Would create missing attributes: {}".format(missing_attrs))
        else:
            print("   Creating missing attributes...")
            for activity in missing_attrs:
                group = ACTIVITY_TO_GROUP.get(activity, 'custom')
                exist_client.create_attribute(activity, exist_client.ValueType.BOOLEAN, group, '', False)
    else:
        print("   All activity attributes already exist")
    
    # Step 2: Sync moods
    print("\n2. Syncing moods...")
    mood_entries = [entry for entry in entries if entry.mood_rating is not None]
    mood_updates = [
        exist_client.make_update('mood', entry.date.isoformat(), entry.mood_rating)
        for entry in mood_entries
    ]
    
    if mood_updates:
        print(f"   Found {len(mood_updates)} mood entries to sync")
        if dry_run:
            print("   [DRY RUN] Would sync moods, showing first 5:")
            for i in range(min(5, len(mood_updates))):
                print(f"     {mood_updates[i]}")
        else:
            print("   Syncing moods...")
            exist_client.update_attributes(mood_updates)
    else:
        print("   No mood entries to sync")
    
    # Step 3: Sync activities
    print("\n3. Syncing activities...")
    activity_updates = []
    for entry in entries:
        for activity in entry.activities:
            if activity == '':
                continue
            activity_norm = normalize_activity_name(activity)
            activity_updates.append(exist_client.make_update(activity_norm, entry.date.isoformat(), True))
    
    if activity_updates:
        print(f"   Found {len(activity_updates)} activity entries to sync")
        if dry_run:
            print("   [DRY RUN] Would sync activities, showing first 5:")
            for i in range(min(5, len(activity_updates))):
                print(f"     {activity_updates[i]}")
        else:
            print("   Syncing activities...")
            exist_client.update_attributes(activity_updates)
    else:
        print("   No activity entries to sync")
    
    # Step 4: Update last sync date
    if not dry_run and (mood_updates or activity_updates):
        latest_date = max(e.date for e in entries)
        print(f"\n4. Updating last sync date to {latest_date}")
        write_last_sync_date(latest_date)
    
    print("\nSync complete!")

parser = argparse.ArgumentParser(description =
    "Import Daylio journal entries from an exported CSV file, and optionally sync them to Exist.io.")

parser.add_argument('file_path', type=str, help='Path to the Daylio CSV file to import.')
parser.add_argument('--dry-run', '-d', action='store_true', help='Instead of syncing, print a preview of what would be synced.')
parser.add_argument('--since', '--since-date', dest='since_date', type=str,
    help='Only sync entries on or after this date (YYYY-MM-DD). Overrides stored last sync date if provided.')

def main():
    args = parser.parse_args()
    entries = import_daylio_csv(args.file_path)

    # Determine effective since date (CLI override > stored last sync)
    since_date: Optional[datetime.date] = None
    if args.since_date:
        try:
            since_date = datetime.date.fromisoformat(args.since_date)
        except ValueError:
            print(f"Error: --since date '{args.since_date}' is not valid ISO format YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        since_date = read_last_sync_date()

    if since_date:
        entries = [e for e in entries if e.date >= since_date]
        if not entries:
            print("No entries to process after since date.")
            return
    
    # Run comprehensive sync by default
    sync_all(entries, dry_run = args.dry_run)

if __name__ == '__main__':
    main()