import sqlite3

conn = sqlite3.connect("prohr.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

for table in tables:
    c.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in c.fetchall()]
    print(f"  {table}: {cols}")

conn.close()
