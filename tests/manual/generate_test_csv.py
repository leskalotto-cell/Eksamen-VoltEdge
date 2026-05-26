#!/usr/bin/env python3
from datetime import datetime, timedelta
from uuid import uuid4
import csv
from random import choice, randint, random, seed

seed(42)
rows = []
base = datetime.utcnow()
for i in range(2000):
    session_id = str(uuid4())
    charger_id = f'CHG-{(i % 50) + 1:03d}'
    connector_id = f'CON-{(i % 6) + 1}'
    user_id = f'USR-{1000 + (i % 200):04d}'
    status = choice(['INITIATED'] * 10 + ['ACTIVE'] * 8 + ['COMPLETED'] * 15 + ['FAULTED'] * 2)
    created_at = base - timedelta(days=randint(0, 30), hours=randint(0,23), minutes=randint(0,59), seconds=randint(0,59))
    started_at = ''
    ended_at = ''
    energy_kwh = ''
    tariff_rate = ''
    cost_dkk = ''
    if status in ['ACTIVE', 'COMPLETED', 'FAULTED']:
        started_at_dt = created_at + timedelta(minutes=randint(1, 120))
        if started_at_dt > base:
            started_at_dt = created_at
        started_at = started_at_dt.isoformat() + 'Z'
        if status == 'COMPLETED':
            kwh = round(1.0 + random() * 45.0, 2)
            tariff = round(1.5 + random() * 3.5, 2)
            ended_at_dt = started_at_dt + timedelta(minutes=randint(15, 180))
            ended_at = ended_at_dt.isoformat() + 'Z'
            energy_kwh = f'{kwh:.2f}'
            tariff_rate = f'{tariff:.2f}'
            cost_dkk = f'{round(kwh * tariff, 2):.2f}'
        elif status == 'FAULTED':
            ended_at_dt = started_at_dt + timedelta(minutes=randint(1, 60))
            ended_at = ended_at_dt.isoformat() + 'Z'
            energy_kwh = f'{round(random() * 5.0, 2):.2f}'
            tariff_rate = f'{round(1.5 + random() * 3.5, 2):.2f}'
            cost_dkk = ''
    rows.append({
        'session_id': session_id,
        'charger_id': charger_id,
        'connector_id': connector_id,
        'user_id': user_id,
        'status': status,
        'started_at': started_at,
        'ended_at': ended_at,
        'energy_kwh': energy_kwh,
        'cost_dkk': cost_dkk,
        'tariff_rate': tariff_rate,
        'created_at': created_at.isoformat() + 'Z'
    })

path = 'tests/manual/session_test_data.csv'
with open(path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['session_id','charger_id','connector_id','user_id','status','started_at','ended_at','energy_kwh','cost_dkk','tariff_rate','created_at'])
    writer.writeheader()
    writer.writerows(rows)

print(f'Wrote {len(rows)} rows to {path}')
