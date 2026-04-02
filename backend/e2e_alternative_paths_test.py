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
    
    # 1. Create Job (Non-blocking now)
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
    print(f"✓ Job created: {job_id} (Status: {res.json().get('status')})")

    # Wait for JD Architect (Agent 01) - Needs more time for background task
    print("... Waiting for background JD generation (Agent 01) ...")
    time.sleep(20)

    # 2. Reject JD with feedback
    rejection_data = {
        "feedback": "Stop talking about cats. Focus on 'Entanglement Protocols' specifically."
    }
    res = requests.post(f"{BASE_URL}/workflow/{job_id}/reject", json=rejection_data, headers=headers)
    if res.status_code != 200:
        print(f"✘ Rejection failed: {res.status_code} - {res.text}")
        return
    print(f"✘ JD Rejected with feedback: {rejection_data['feedback']}")

    # Wait for re-drafting (Agent 01 Refinement)
    print("... Waiting for JD refinement ...")
    time.sleep(15)
    
    # 3. Check if JD updated
    res = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    job_detail = res.json()
    new_jd = job_detail.get("state", {}).get("job_description", "")
    
    if "Entanglement Protocols" in new_jd:
        print("✓ SUCCESS: JD refined successfully based on feedback!")
    else:
        print(f"⚠ FAILURE: JD refinement missed the feedback. JD: {new_jd[:100]}...")

def test_shortlist_rejection_loop():
    print("\n--- TESTING ALTERNATIVE PATH: SHORTLIST REJECTION ---")
    headers = get_headers()
    
    # Create another job
    job_id = f"test_{int(time.time())}"
    patch_data = {
        "action": "inject_jd",
        "state_updates": {
            "job_id": job_id,
            "job_title": "Deep Sea Archaeologist",
            "job_description": "We need archaeologists who can dive.",
            "jd_approval": "approved",
            "current_stage": "shortlist_review",
            "candidates": [{"id": "c1", "name": "Indiana Jones", "skills": ["History"]}]
        }
    }
    # Create job via patch bypass for speed
    requests.patch(f"{BASE_URL}/workflow/{job_id}/state", json=patch_data, headers=headers)
    
    # Reject Shortlist
    rejection_data = {
        "feedback": "I need more candidates with 'Underwater Welding' skills specifically."
    }
    requests.post(f"{BASE_URL}/workflow/{job_id}/reject", json=rejection_data, headers=headers)
    print(f"✘ Shortlist Rejected with feedback: {rejection_data['feedback']}")
    
    # Give time for The Scout to run again with feedback
    print("... Waiting for re-sourcing with feedback ...")
    time.sleep(15)
    
    # Check if new candidates found
    res = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    candidates = res.json().get("state", {}).get("candidates", [])
    
    found_welder = any("Welding" in str(c.get("skills", [])) for c in candidates)
    
    if found_welder:
        print("✓ SUCCESS: The Scout found 'Finn Kelly' based on feedback!")
    else:
        print("⚠ FAILURE: The Scout ignored the rejection feedback.")

if __name__ == "__main__":
    test_jd_rejection_loop()
    # test_shortlist_rejection_loop() # Disabled for now to focus on the FIRST loop
