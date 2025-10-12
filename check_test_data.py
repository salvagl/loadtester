#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('/app/data/loadtester.db')
cursor = conn.cursor()

cursor.execute('SELECT scenario_id, scenario_name, test_data FROM test_scenarios WHERE endpoint_id=12 LIMIT 1')
row = cursor.fetchone()

if row:
    scenario_id, name, test_data_str = row
    print(f'Scenario: {name}')

    if test_data_str:
        test_data = json.loads(test_data_str)
        print(f'Test data count: {len(test_data)}')

        if test_data:
            first = test_data[0]
            print('First sample:')
            print(json.dumps(first, indent=2)[:600])

            if 'photoUrls' in first:
                print('photoUrls: PRESENT')
            else:
                print('photoUrls: MISSING!')
else:
    print('No scenarios')

conn.close()
