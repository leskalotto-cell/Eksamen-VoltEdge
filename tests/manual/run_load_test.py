#!/usr/bin/env python3
"""
Simple load/test helper to create multiple sessions against the local API.
Usage:
  python run_load_test.py --count 10 --start --end
"""
import os
import sys
import argparse
import json
from time import sleep

try:
    import requests
except Exception:
    print("Please install requests: pip install requests")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

API = os.getenv('API_URL', 'http://localhost:8000')
KEY = os.getenv('API_KEY', 'skift-dette')
HEADERS = {'X-API-Key': KEY, 'Content-Type': 'application/json'}

parser = argparse.ArgumentParser(description='Create multiple test sessions')
parser.add_argument('--count', type=int, default=10, help='Number of sessions to create')
parser.add_argument('--start', action='store_true', help='Also call /start for each created session')
parser.add_argument('--end', action='store_true', help='Also call /end for each created session (requires --start)')
parser.add_argument('--delay', type=float, default=0.1, help='Delay (s) between requests')
args = parser.parse_args()

if args.end and not args.start:
    print('Warning: --end requested without --start; end will likely fail unless sessions are active')

created = []
for i in range(args.count):
    payload = {
        'charger_id': f'CHG-{i:03d}',
        'connector_id': f'CON-{(i%4)+1}',
        'user_id': f'USR-{1000+i}'
    }
    try:
        r = requests.post(f"{API}/sessions/", headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        obj = r.json()
        sid = obj.get('session_id')
        created.append(sid)
        print(f'Created: {sid}')
    except Exception as e:
        print('Create failed:', e, getattr(e, 'response', None) and e.response.text)
    sleep(args.delay)

if args.start:
    for sid in created:
        if not sid:
            continue
        try:
            r = requests.post(f"{API}/sessions/{sid}/start", headers=HEADERS, timeout=10)
            r.raise_for_status()
            print(f'Started: {sid}')
        except Exception as e:
            print('Start failed:', e, getattr(e, 'response', None) and e.response.text)
        sleep(args.delay)

if args.end:
    for sid in created:
        if not sid:
            continue
        payload = {'energy_kwh': 5.0 + (hash(sid) % 10), 'tariff_rate': 2.5}
        try:
            r = requests.post(f"{API}/sessions/{sid}/end", headers=HEADERS, json=payload, timeout=10)
            r.raise_for_status()
            print(f'Ended: {sid}')
        except Exception as e:
            print('End failed:', e, getattr(e, 'response', None) and e.response.text)
        sleep(args.delay)

print('\nDone. Created sessions:', len(created))
print('You can list sessions: GET', f'{API}/sessions')
