#!/usr/bin/env python3
"""Fix database schema by adding missing schema column"""

import subprocess
import time

print(">> Deteniendo backend...")
subprocess.run(["docker-compose", "stop", "backend"], cwd="G:/Mi unidad/PSU-IA/Q2/TF1/src", check=True)
time.sleep(2)

print(">> Ejecutando ALTER TABLE dentro del contenedor...")
result = subprocess.run([
    "docker-compose", "run", "--rm", "backend",
    "python", "-c",
    """
import sqlite3
db_path = '/app/data/loadtester.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='endpoints'")
if not cursor.fetchone():
    print('ERROR: Table endpoints does not exist!')
else:
    # Check if column exists
    cursor.execute("PRAGMA table_info(endpoints)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'schema' not in columns:
        print('Adding schema column...')
        cursor.execute("ALTER TABLE endpoints ADD COLUMN schema TEXT")
        conn.commit()
        print('SUCCESS: Column schema added!')
    else:
        print('Column schema already exists')

# Verify
cursor.execute("PRAGMA table_info(endpoints)")
print('\\nCurrent columns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

conn.close()
"""
], cwd="G:/Mi unidad/PSU-IA/Q2/TF1/src")

if result.returncode == 0:
    print("\n>> Iniciando backend...")
    subprocess.run(["docker-compose", "start", "backend"], cwd="G:/Mi unidad/PSU-IA/Q2/TF1/src", check=True)
    print(">> Backend iniciado!")
else:
    print(f"\n>> ERROR: Failed with code {result.returncode}")
