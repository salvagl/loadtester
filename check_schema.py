#!/usr/bin/env python3
"""Check if schema is properly saved in database"""

import sqlite3
import json

conn = sqlite3.connect('G:/Mi unidad/PSU-IA/Q2/TF1/src/shared/database/loadtester.db')
cursor = conn.cursor()

# Get the endpoint for API 14 (the one from the recent test)
cursor.execute('SELECT endpoint_id, endpoint_name, http_method, endpoint_path, schema FROM endpoints WHERE api_id=14')
rows = cursor.fetchall()

print('Endpoints for API 14 (recent test):')
print('='*60)

for row in rows:
    ep_id, name, method, path, schema_str = row
    print(f'\nEndpoint ID: {ep_id}')
    print(f'Name: {name}')
    print(f'Method: {method} {path}')

    if schema_str:
        print(f'✓ Has schema: Yes ({len(schema_str)} chars)')

        try:
            schema = json.loads(schema_str)

            # Check requestBody
            if 'requestBody' in schema:
                rb = schema['requestBody']
                print(f'  - Has requestBody: Yes')

                if 'content' in rb and 'application/json' in rb['content']:
                    json_schema = rb['content']['application/json'].get('schema', {})

                    if 'required' in json_schema:
                        print(f'  - Required fields: {json_schema["required"]}')
                    else:
                        print(f'  ✗ NO required fields in schema!')

                    if 'properties' in json_schema:
                        props = list(json_schema['properties'].keys())
                        print(f'  - Properties: {props[:5]}...')
                    else:
                        print(f'  ✗ NO properties in schema!')
            else:
                print(f'  ✗ NO requestBody in schema!')

        except Exception as e:
            print(f'  ✗ Error parsing schema: {e}')
    else:
        print(f'✗ Has schema: NO - THIS IS THE PROBLEM!')

conn.close()
