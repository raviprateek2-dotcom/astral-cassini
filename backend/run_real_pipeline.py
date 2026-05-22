import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"
headers = {"Content-Type": "application/json"} # Auth disabled

def wait_for_stage(job_id, target_stage, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{BASE_URL}/workflow/{job_id}/status", headers=headers)
        if r.status_code == 200:
            current = r.json().get("current_stage")
            print(f"Waiting... current stage: {current}")
            if current == target_stage:
                return r.json()
            if current == "error" or current == "completed":
                print("Unexpectedly reached terminal state.")
                return r.json()
        time.sleep(2)
    print("Timeout waiting for stage.")
    sys.exit(1)

def main():
    print("--- 1. INTAKE (JD Architect) ---")
    job_req = {
        "job_title": "Senior AI Agent Architect",
        "department": "Advanced Agentic Coding",
        "requirements": [
            "Expert in LangGraph",
            "Python",
            "Machine Learning",
            "Distributed Systems"
        ],
        "location": "Remote",
        "salary_range": "$200k - $300k"
    }
    r = requests.post(f"{BASE_URL}/jobs", json=job_req, headers=headers)
    if r.status_code != 200:
        print("Failed to create job:", r.text)
        sys.exit(1)
    job_id = r.json()["job_id"]
    print(f"Job Created: {job_id}")
    
    # Wait for JD Review
    wait_for_stage(job_id, "jd_review")
    r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    jd = r.json().get("state", {}).get("job_description", "")
    print(f"JD Drafted ({len(jd)} chars).")

    print("\n--- 2. APPROVAL 1 (Scout + Screener) ---")
    requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Approved."}, headers=headers)
    
    # Wait for Shortlist Review
    state = wait_for_stage(job_id, "shortlist_review")
    r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    candidates = r.json().get("state", {}).get("scored_candidates", [])
    print(f"Found {len(candidates)} candidates.")
    for c in candidates[:3]:
        print(f"  - {c.get('candidate_name')} (Score: {c.get('overall_score')})")

    print("\n--- 3. APPROVAL 2 (Outreach + Coordinator) ---")
    requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Proceed."}, headers=headers)
    
    # Wait for Hire Review
    state = wait_for_stage(job_id, "hire_review")
    r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    recs = r.json().get("state", {}).get("final_recommendations", [])
    print(f"Generated {len(recs)} final recommendations.")
    for c in recs[:3]:
        print(f"  - {c.get('candidate_name')}: {c.get('decision')} (Score: {c.get('overall_weighted_score')})")

    print("\n--- 4. APPROVAL 3 (Offer Generator) ---")
    requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Hire the top candidate."}, headers=headers)
    
    # Wait for Completed
    wait_for_stage(job_id, "completed")
    r = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
    offers = r.json().get("state", {}).get("offer_details", [])
    if offers:
        print("\nOffer Generated:")
        print(offers[0].get("offer_markdown")[:300] + "...")
    else:
        print("No offer details found.")
        
    print("\n--- PIPELINE COMPLETE ---")

if __name__ == "__main__":
    main()
