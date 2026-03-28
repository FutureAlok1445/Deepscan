import requests
import sqlite3

conn = sqlite3.connect('backend/deepscan.db')
cursor = conn.cursor()
cursor.execute('SELECT id FROM scans ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()
if not row:
    print("No scans in DB.")
else:
    scan_id = row[0]
    print(f"Testing with scan_id: {scan_id}")
    res = requests.get(f'http://localhost:8000/api/v1/report/{scan_id}?score=50&verdict=UNCERTAIN')
    print("Status:", res.status_code)
    print("Response snippet:", res.content[:200])
