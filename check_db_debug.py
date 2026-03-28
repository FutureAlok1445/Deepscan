import sqlite3
import json

def check_db():
    try:
        conn = sqlite3.connect('d:/jondle/Deepscan/backend/deepscan.db')
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(scans)")
        columns = cursor.fetchall()
        print("Scans Table Columns:", [c[1] for c in columns])
        
        # Get last result
        cursor.execute("SELECT id, signals FROM scans ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            scan_id, signals_json = row
            print(f"\nLast Scan ID: {scan_id}")
            if signals_json:
                signals = json.loads(signals_json)
                print("Signals Content Keys:", list(signals.keys()))
                if "context_verification_layer" in signals:
                    print("Layer 11 Data Found in DB!")
                    print(json.dumps(signals["context_verification_layer"], indent=2))
                else:
                    print("Layer 11 Data MISSING in DB signals.")
            else:
                print("Signals field is EMPTY.")
        else:
            print("No scans found in DB.")
            
        conn.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
