import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "pcb_database.db"
IMAGE_DIR = "saved_images"

# Make sure the folder for saving images exists
os.makedirs(IMAGE_DIR, exist_ok=True)

def init_db():
    """Creates the SQL tables if they don't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the logging table
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
    print("[SYSTEM] SQLite Database Ready.")

def log_inspection(stage, total_defects, details_dict, image_pil):
    """Saves the image locally and writes the details to SQL."""
    try:
        # 1. Save the image physically
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{time_str}.jpg"
        filepath = os.path.join(IMAGE_DIR, filename)
        image_pil.save(filepath, "JPEG")
        
        # 2. Serialize the dictionary to a JSON string
        details_json = json.dumps(details_dict)
        
        # 3. Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO inference_logs (detected_stage, total_defects, granular_details, image_path)
            VALUES (?, ?, ?, ?)
        ''', (stage, total_defects, details_json, filepath))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] Failed to log inspection: {e}")
        return False

def fetch_all_logs():
    """Reads the database to show in the UI Explorer."""
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    try:
        df = pd.read_sql_query("SELECT * FROM inference_logs ORDER BY timestamp DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# Initialize DB when the file is loaded
init_db()


def delete_log(log_id):
    """Deletes a specific inspection record from the database by its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inference_logs WHERE id = ?", (log_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] Failed to delete record {log_id}: {e}")
        return False