#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor a specific load test job"""

import sys
import requests
import time

if len(sys.argv) < 2:
    print("Usage: python monitor_job.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]
print(f">> Monitoreando job: {job_id}\n")

previous_progress = -1
start_time = time.time()

try:
    while True:
        response = requests.get(f"http://localhost:8000/api/v1/status/{job_id}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            progress = data.get('progress', 0)

            elapsed = int(time.time() - start_time)

            # Solo mostrar si el progreso cambió
            if progress != previous_progress:
                print(f"[{elapsed}s] Status: {status:10} | Progress: {progress:6.1f}%")
                previous_progress = progress

            if status == "FINISHED":
                print(f"\n>> Test COMPLETADO exitosamente!")
                print(f"   Tiempo total: {elapsed}s")
                print(f"   Report URL: {data.get('report_url', 'N/A')}")

                # Mostrar información adicional si está disponible
                if 'finished_at' in data:
                    print(f"   Finalizado: {data['finished_at']}")
                break

            elif status == "FAILED":
                print(f"\n>> Test FALLO!")
                print(f"   Tiempo hasta fallo: {elapsed}s")
                break

        elif response.status_code == 404:
            print(f">> ERROR: Job {job_id} no encontrado")
            break
        else:
            print(f">> ERROR: Status code {response.status_code}")
            break

        time.sleep(3)

except KeyboardInterrupt:
    print(f"\n>> Monitoreo cancelado por usuario")
except Exception as e:
    print(f"\n>> ERROR: {str(e)}")
