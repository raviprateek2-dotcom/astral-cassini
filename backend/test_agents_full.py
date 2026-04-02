import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def test_full_agent_workflow():
    print("--- Starting Agent Intelligence Validation ---")
    
    # 1. Login
    print("\n[1/5] Authenticating as HR Manager...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "hr@prohr.ai", "password": "hr123"})
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("OK: Auth Successful.")
    except Exception as e:
        print(f"ERR: Auth Failed: {e}")
        return

    # 2. Create Job
    print("\n[2/5] Creating 'Senior AI Architect' Requisition...")
    payload = {
        "job_title": "Senior AI Architect",
        "department": "Engineering",
        "requirements": ["Python", "LangGraph", "Vector DBs", "OpenAI API"],
        "preferred_qualifications": ["PhD in CS", "5+ years LLM Experience"],
        "location": "San Francisco / Remote",
        "salary_range": "$200k - $250k"
    }
    resp = requests.post(f"{BASE_URL}/jobs", json=payload, headers=headers)
    resp.raise_for_status()
    job_id = resp.json()["job_id"]
    print(f"OK: Job Created with ID: {job_id}")

    # 3. Wait for JD Architect (Agent 1)
    print("\n[3/5] Waiting for JD Architect Agent to draft the description...")
    max_retries = 40
    for i in range(max_retries):
        resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        status = resp.json()
        stage = status.get("current_stage")
        error = status.get("state", {}).get("error")
        
        if error:
            print(f"ERR: Agent Error Detected: {error}")
            return

        print(f"   - Polling... Current Stage: {stage}")
        
        if stage == "jd_review":
            print("OK: Agent 1 (JD Architect) finished! JD Content length:", len(status.get("state", {}).get("job_description", "")))
            break
        time.sleep(2)
    else:
        print("ERR: Timeout waiting for JD Architect.")
        return

    # 4. Approve JD (HITL - Liaison Agent)
    print("\n[4/5] Liaison Agent: Simulating HR Approval of JD...")
    resp = requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Looks great, proceed with sourcing."}, headers=headers)
    resp.raise_for_status()
    print("OK: JD Approved. Pipeline resuming...")

    # 5. Wait for Scout & Screener (Agent 3 & 4)
    print("\n[5/5] Waiting for Scout (Sourcing) and Screener (Scoring) Agents...")
    max_retries = 40
    for i in range(max_retries):
        resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        status = resp.json()
        stage = status.get("current_stage")
        scored_candidates = status.get("state", {}).get("scored_candidates", [])
        
        print(f"   - Polling... Current Stage: {stage} | Candidates Scored: {len(scored_candidates)}")
        
        if stage == "shortlist_review" and len(scored_candidates) > 0:
            print(f"OK: Agent 4 (Screener) has scored {len(scored_candidates)} candidates!")
            for c in scored_candidates:
                print(f"     - Candidate: {c.get('name', 'Unknown')} | Score: {c.get('overall_score', 0):.1f}/100")
            break
        time.sleep(3)
    else:
        print("ERR: Timeout waiting for Sourcing/Screening results.")
        return

    print("\nSystem: ALL AGENTS VALIDATED. SYSTEM IS FULLY OPERATIONAL.")

if __name__ == "__main__":
    test_full_agent_workflow()
