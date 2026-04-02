import sqlite3
import os

db_path = "./data/prohr.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get current columns
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in 'jobs': {columns}")

    missing_columns = [
        ("outreach_completed", "BOOLEAN DEFAULT 0"),
        ("offer_sent", "BOOLEAN DEFAULT 0"),
        ("avg_match_percentage", "FLOAT DEFAULT 0.0")
    ]

    for col_name, col_type in missing_columns:
        if col_name not in columns:
            print(f"Adding missing column: {col_name}")
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    print("Schema repair complete.")

except Exception as e:
    print(f"Error during schema repair: {e}")
    conn.rollback()

finally:
    conn.close()
