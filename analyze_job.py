import sqlite3
import json

conn = sqlite3.connect('./shared/database/loadtester.db')
cursor = conn.cursor()

job_id = '21c983ed-1c2a-4dc4-bc48-d97b76d3d92a'

print("=" * 80)
print("JOB ANALYSIS FOR:", job_id)
print("=" * 80)

# 1. Job info
cursor.execute('SELECT * FROM jobs WHERE job_id LIKE ?', (f'{job_id[:8]}%',))
job = cursor.fetchone()
if job:
    print("\n[1] JOB INFO:")
    print(f"  Job ID: {job[0]}")
    print(f"  Type: {job[1]}")
    print(f"  Status: {job[2]}")
    print(f"  Progress: {job[3]}%")
    print(f"  Result Data: {job[4]}")
    print(f"  Error: {job[5]}")
    print(f"  Created: {job[8]}")
    print(f"  Started: {job[9]}")
    print(f"  Finished: {job[10]}")

# 2. Test executions
cursor.execute('SELECT * FROM test_executions ORDER BY start_time DESC LIMIT 1')
execution = cursor.fetchone()
if execution:
    print("\n[2] TEST EXECUTION:")
    print(f"  Execution ID: {execution[0]}")
    print(f"  Scenario ID: {execution[1]}")
    print(f"  Name: {execution[2]}")
    print(f"  Start: {execution[3]}")
    print(f"  End: {execution[4]}")
    print(f"  Status: {execution[5]}")
    print(f"  Duration: {execution[6]} seconds")

    execution_id = execution[0]

    # 3. Test results
    cursor.execute('SELECT * FROM test_results WHERE execution_id = ?', (execution_id,))
    result = cursor.fetchone()
    print("\n[3] TEST RESULTS:")
    if result:
        print(f"  Result ID: {result[0]}")
        print(f"  Execution ID: {result[1]}")
        print(f"  Avg Response Time: {result[2]} ms")
        print(f"  P95: {result[3]} ms")
        print(f"  P99: {result[4]} ms")
        print(f"  Min: {result[5]} ms")
        print(f"  Max: {result[6]} ms")
        print(f"  Total Requests: {result[7]}")
        print(f"  Successful: {result[8]}")
        print(f"  Failed: {result[9]}")
        print(f"  Success Rate: {result[10]}%")
        print(f"  RPS: {result[11]}")
        print(f"  Concurrent Users: {result[12]}")
        print(f"  HTTP 4xx errors: {result[16]}")
        print(f"  HTTP 5xx errors: {result[17]}")
        print(f"  Timeout errors: {result[18]}")
        print(f"  Connection errors: {result[19]}")
        print(f"  Error Summary: {result[20]}")
    else:
        print("  [X] NO TEST RESULTS FOUND!")

    # 4. Performance metrics
    cursor.execute('PRAGMA table_info(performance_metrics)')
    metrics_cols = cursor.fetchall()
    print("\n[4] PERFORMANCE METRICS TABLE STRUCTURE:")
    for col in metrics_cols:
        print(f"  - {col[1]} ({col[2]})")

    cursor.execute('SELECT COUNT(*) FROM performance_metrics')
    metrics_count = cursor.fetchone()[0]
    print(f"\n  Total metrics records: {metrics_count}")

    if metrics_count > 0:
        cursor.execute('SELECT * FROM performance_metrics LIMIT 3')
        metrics = cursor.fetchall()
        print("\n  Sample metrics:")
        for m in metrics:
            print(f"    {m}")

print("\n" + "=" * 80)
conn.close()
