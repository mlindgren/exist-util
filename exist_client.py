#!/usr/bin/python
"""
Very basic client for Exist.io. Code mostly stolen from https://developer.exist.io/guide/write_client/
"""

from enum import IntEnum
import json
from pprint import PrettyPrinter
import requests

SECRETS = json.load(open('secrets.json'))

# Constants to represent Exist's value types
class ValueType(IntEnum):
    QUANTITY = 0
    DECIMAL = 1
    STRING = 2
    DURATION = 3
    TIMEOFDAY = 4
    PERCENTAGE = 5
    BOOLEAN = 7
    SCALE = 8

def acquire_attribute(token : str, attribute : str):
    # make the json string to send to Exist
    body = json.dumps([{'template': attribute, 'manual': False}])

    # make the POST request, sending the json as the POST body
    # we need a content-type header so Exist knows it's json
    response = requests.post("https://exist.io/api/2/attributes/acquire/", 
        data=body,
        headers={'Authorization':f'Bearer {token}',
                 'Content-type':'application/json'})

    if response.status_code == 200:
        # a 200 status code indicates a successful outcome
        print("Acquired successfully.")
    else:
        # print the error if something went wrong
        data = response.json()
        print("Error:", data)

def make_update(attribute : str, date : str, value):
    return {'name': attribute, 'date': date, 'value': value}

def update_attributes(updates):
    # make the json string to send to Exist
    while len(updates) > 36:
        # Exist only allows 36 updates per request
        # so we need to split the updates into chunks
        chunk = updates[:36]
        updates = updates[36:]
        body = json.dumps(chunk)

        # make the POST request, sending the json as the POST body
        # we need a content-type header so Exist knows it's json
        response = requests.post("https://exist.io/api/2/attributes/update/", 
            data = body,
            headers = {
                "Authorization" : f"Bearer {SECRETS['developerAccessToken']}",
                "Content-type" : "application/json"
            })

        if response.status_code == 200:
            # a 200 status code indicates a successful outcome
            print("Updated successfully.")
        else:
            # print the error if something went wrong
            data = response.json()
            print("Error:", data)

def create_attribute(label, value_type, group, manual):
    # make the json string to send to Exist
    body = json.dumps([
        {'label': label,
         'value_type': value_type,
         'group': group,
         'manual': manual
        }])

    # make the POST request, sending the json as the POST body
    # we need a content-type header so Exist knows it's json
    response = requests.post("https://exist.io/api/2/attributes/create/", 
        data = body,
        headers = {
            "Authorization" : f"Bearer {SECRETS['developerAccessToken']}",
            "Content-type" : "application/json"
        })

    if response.status_code == 200:
        # a 200 status code indicates a successful outcome
        # let's get out the full version of our attribute
        data = response.json()
        obj = data['success'][0]
        print("Created successfully:")
        # and let's print it (nicely) so we can see its fields
        pp = PrettyPrinter()
        pp.pprint(obj)
    else:
        # print the error if something went wrong
        data = response.json()
        print("Error:", data)