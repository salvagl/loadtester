#!/usr/bin/env python3
"""Add schema column to endpoints table"""

import sqlite3

db_path = 'G:/Mi unidad/PSU-IA/Q2/TF1/src/shared/database/loadtester.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(endpoints)")
columns = [row[1] for row in cursor.fetchall()]

if 'schema' not in columns:
    print("Adding 'schema' column to endpoints table...")
    cursor.execute("ALTER TABLE endpoints ADD COLUMN schema TEXT")
    conn.commit()
    print("Column 'schema' added successfully!")
else:
    print("Column 'schema' already exists.")

# Verify
cursor.execute("PRAGMA table_info(endpoints)")
print("\nEndpoints table columns:")
for row in cursor.fetchall():
    print(f"  - {row[1]} ({row[2]})")

conn.close()
