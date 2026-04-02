import sqlite3
import os

DB_PATH = "data/prohr.db"

MIGRATIONS = {
    "jobs": [
        ("outreach_completed",   "BOOLEAN DEFAULT 0"),
        ("offer_sent",           "BOOLEAN DEFAULT 0"),
        ("avg_match_percentage", "REAL DEFAULT 0.0"),
    ],
    "candidate_scores": [
        ("match_percentage",  "REAL DEFAULT 0.0"),
        ("missing_skills",    "TEXT DEFAULT '[]'"),
        ("overqualification", "TEXT DEFAULT '[]'"),
    ],
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    print(f"DB: {DB_PATH} ({os.path.getsize(DB_PATH)} bytes)")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [r[0] for r in cur.fetchall()]
    print(f"Tables: {all_tables}\n")

    for table, columns in MIGRATIONS.items():
        if table not in all_tables:
            print(f"[SKIP] Table '{table}' not found.")
            continue

        cur.execute(f"PRAGMA table_info({table})")
        existing_cols = {r[1] for r in cur.fetchall()}
        print(f"[{table}] {len(existing_cols)} columns")

        for col_name, col_def in columns:
            if col_name not in existing_cols:
                sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"
                print(f"  + Adding: {col_name}")
                cur.execute(sql)
            else:
                print(f"  ✓ {col_name} already exists")

    conn.commit()
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
