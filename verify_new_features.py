import asyncio
import sqlite3
import json
from app.config import settings

async def verify():
    conn = sqlite3.connect("recruitment.db")
    cursor = conn.cursor()
    
    # Get the latest job
    cursor.execute("SELECT id, state FROM jobs ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("No jobs found in DB.")
        return
    
    job_id, state_json = row
    state = json.loads(state_json)
    
    print(f"\n--- Verifying Job: {job_id} ---")
    
    # 1. Check Ghosting Prevention in Audit Log
    audit_log = state.get("audit_log", [])
    ghosting_updates = [e for e in audit_log if e.get("action") == "ghosting_prevention_update"]
    print(f"\n[Ghosting Prevention] Found {len(ghosting_updates)} updates.")
    for e in ghosting_updates:
        print(f"  - {e.get('details')}")

    # 2. Check Suggested Questions
    suggested = state.get("suggested_questions", [])
    print(f"\n[Contextual Questions] Found {len(suggested)} candidate interview guides.")
    for s in suggested:
        print(f"  - Candidate: {s.get('candidate_name')}")
        for q in s.get('questions', [])[:2]:
            print(f"    ? {q}")

    # 3. Check JD Inclusion
    jd = state.get("job_description", "")
    if "Inclusivity Audit Summary" in jd:
        print("\n[JD Inclusivity] Found audit summary in Job Description.")
    else:
        print("\n[JD Inclusivity] Audit summary not found in JD (may be mock data).")

    conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
