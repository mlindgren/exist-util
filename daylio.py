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
from typing import List

import exist_client

CONFIG = json.load(open('config.json'))

MOOD_RATING_MAP = {
    "awful" : 1,
    "bad" : 2,
    "meh" : 3,
    "good" : 4,
    "rad" : 5
}

@dataclass
class DaylioEntry:
    """
    Represents a single Daylio journal entry.
    """
    date: datetime.date
    mood_name: str
    mood_rating: int
    activities: List[str]
    note: str

GLOBAL_ACTIVITY_LIST = set()

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
            mood_rating = MOOD_RATING_MAP.get(row['mood'], -1)
            activities = row['activities'].split(' | ')

            # Removed activities that are filtered in the config
            activities = [activity for activity in activities if activity not in CONFIG['filter_activities']]
            GLOBAL_ACTIVITY_LIST.update(set(activities))

            note = row['note']
            entry = DaylioEntry(date, mood_name, mood_rating, activities, note)
            entries.append(entry)
    return entries

def daylio_mood_to_exist(daylio_mood_rating : int):
    return (daylio_mood_rating * 2) - 1

def create_activity_tags():
    for activity in GLOBAL_ACTIVITY_LIST:
        exist_client.create_attribute(activity, exist_client.ValueType.BOOLEAN, 'custom', False)

parser = argparse.ArgumentParser(description =
    "Import Daylio journal entries from an exported CSV file, and optionally sync them to Exist.io.")

parser.add_argument('file_path', type=str, help='Path to the Daylio CSV file to import.')
parser.add_argument('--sync-moods', action='store_true', help='Sync moods Exist.io.')
parser.add_argument('--sync-activities', action='store_true', help='Sync activities to Exist.io.')
parser.add_argument('--create-activity-tags', action='store_true', help='Create custom attributes for each activity.')
parser.add_argument('--dry-run', '-d', action='store_true', help='Instead of syncing, print a preview of what would be synced.')

def main():
    args = parser.parse_args()
    entries = import_daylio_csv(args.file_path)

    if args.sync_moods:
        updates = [exist_client.make_update('mood', entry.date.isoformat(), daylio_mood_to_exist(entry.mood_rating)) for entry in entries]
        if args.dry_run:
            print(f"{len(updates)} updates to sync, showing first 5:")
            for i in range(5):
                print(updates[i])
        else:
            exist_client.update_attributes(updates)
    elif args.create_activity_tags:
        if args.dry_run:
            print("Activites to create: ", GLOBAL_ACTIVITY_LIST)
        else:
            create_activity_tags()
    elif args.sync_activities:
        updates = []
        for entry in entries:
            for activity in entry.activities:
                if activity == '':
                    continue
                activity = activity.replace(' ', '_')
                activity = activity.replace('/', '')
                activity = activity.replace('&', '')
                activity = activity.replace('(', '')
                activity = activity.replace(')', '')
                updates.append(exist_client.make_update(activity, entry.date.isoformat(), True))

        if args.dry_run:
            print(f"{len(updates)} updates to sync, showing first 5:")
            for i in range(5):
                print(updates[i])
        else:
            exist_client.update_attributes(updates)


if __name__ == '__main__':
    main()