import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"
CREDS = {"username": "admin@prohr.ai", "password": "admin123"}

def get_headers():
    r = requests.post(f"{BASE_URL}/auth/login", data=CREDS, timeout=15)
    if r.status_code != 200:
        print(f"LOGIN FAILED: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def test_jd_rejection_loop():
    print("\n--- TESTING ALTERNATIVE PATH: JD REJECTION & REFINEMENT ---")
    headers = get_headers()
    
    # 1. Create Job (Non-blocking)
    job_data = {
        "job_title": "Quantum Mechanic",
        "department": "Physics",
        "requirements": ["10+ years with Schrödinger's CAT"],
        "location": "Superposition"
    }
    res = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers, timeout=10)
    if res.status_code != 200:
        print(f"✘ Failed to create job: {res.status_code} - {res.text}")
        return
    job_id = res.json()["job_id"]
    print(f"✓ Job created: {job_id}")

    # Wait for JD Architect (Agent 01)
    print("... Polling for JD_REVIEW state (Agent 01) ...")
    for i in range(20):
        status_res = requests.get(f"{BASE_URL}/workflow/{job_id}/status", headers=headers)
        current_stage = status_res.json().get("current_stage")
        if current_stage == "jd_review":
            print(f"    [Success] Agent 01 complete.")
            break
        print(f"    [Poll {i+1}] Stage: {current_stage}")
        time.sleep(3)
    else:
        print("✘ Failed to reach jd_review state.")
        return

    # 2. Reject JD with feedback
    rejection_data = {
        "feedback": "Focus on 'Entanglement Protocols' specifically."
    }
    res = requests.post(f"{BASE_URL}/workflow/{job_id}/reject", json=rejection_data, headers=headers)
    if res.status_code != 200:
        print(f"✘ Rejection failed: {res.status_code} - {res.text}")
        return
    print(f"✘ JD Rejected with feedback: {rejection_data['feedback']}")

    # Wait for re-drafting
    print("... Polling for refinement ...")
    time.sleep(5) # Base delay
    for i in range(15):
        det_res = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        jd_text = det_res.json().get("state", {}).get("job_description", "")
        if "Entanglement Protocols" in jd_text:
            print("✓ SUCCESS: JD refined successfully based on feedback!")
            break
        print(f"    [Poll {i+1}] Waiting for updated JD...")
        time.sleep(3)
    else:
        print("⚠ FAILURE: JD refinement missed the feedback.")

def test_shortlist_rejection_loop():
    print("\n--- TESTING ALTERNATIVE PATH: SHORTLIST REJECTION & RAG REFINEMENT ---")
    headers = get_headers()
    
    # Create another job but approve JD immediately
    job_data = {
        "job_title": "Deep Sea Archaeologist",
        "department": "Exploration",
        "requirements": ["History degree"]
    }
    res = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=headers)
    job_id = res.json()["job_id"]
    
    # Wait for JD
    while requests.get(f"{BASE_URL}/workflow/{job_id}/status", headers=headers).json().get("current_stage") != "jd_review":
        time.sleep(2)
        
    # Approve JD
    requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Looks good"}, headers=headers)
    print("✓ JD Approved, entering Sourcing...")
    
    # Wait for Sourcing (Agent 03) to hit Shortlist Review
    print("... Polling for SHORTLIST_REVIEW state (Agent 03) ...")
    for i in range(20):
        status_res = requests.get(f"{BASE_URL}/workflow/{job_id}/status", headers=headers)
        current_stage = status_res.json().get("current_stage")
        if current_stage == "shortlist_review":
            print(f"    [Success] Agent 03 (The Scout) complete.")
            break
        print(f"    [Poll {i+1}] Stage: {current_stage}")
        time.sleep(3)
    
    # Reject Shortlist
    rejection_data = {
        "feedback": "I need more candidates with 'Underwater Welding' skills specifically."
    }
    requests.post(f"{BASE_URL}/workflow/{job_id}/reject", json=rejection_data, headers=headers)
    print(f"✘ Shortlist Rejected with feedback: {rejection_data['feedback']}")
    
    # Wait for re-sourcing
    print("... Polling for re-sourcing (RAG update) ...")
    for i in range(15):
        detail_res = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        candidates = detail_res.json().get("state", {}).get("candidates", [])
        if any("Welding" in str(c.get("skills", [])) for c in candidates):
            print("✓ SUCCESS: The Scout found 'Finn Kelly' via RAG update!")
            break
        print(f"    [Poll {i+1}] Waiting for updated candidates pool...")
        time.sleep(3)
    else:
        print("⚠ FAILURE: RAG failed to adjust to rejection feedback.")

if __name__ == "__main__":
    test_jd_rejection_loop()
    print("\n" + "="*50)
    test_shortlist_rejection_loop()
