import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "pcb_database.db"
IMAGE_DIR = "saved_images"

os.makedirs(IMAGE_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inference_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            detected_stage TEXT,
            total_defects INTEGER,
            granular_details TEXT, 
            image_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_inspection(stage, total_defects, details_dict, image_pil):
    """Saves the image locally and returns the generated database ID."""
    try:
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{time_str}.jpg"
        filepath = os.path.join(IMAGE_DIR, filename)
        image_pil.save(filepath, "JPEG")
        
        details_json = json.dumps(details_dict)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO inference_logs (detected_stage, total_defects, granular_details, image_path)
            VALUES (?, ?, ?, ?)
        ''', (stage, total_defects, details_json, filepath))
        
        inserted_id = cursor.lastrowid # Grab the ID that was just created
        conn.commit()
        conn.close()
        
        return inserted_id # Return the ID instead of True
    except Exception as e:
        print(f"[DB ERROR] Failed to log inspection: {e}")
        return None

def fetch_all_logs():
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    try:
        df = pd.read_sql_query("SELECT * FROM inference_logs ORDER BY timestamp DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_log(log_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inference_logs WHERE id = ?", (log_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

init_db()