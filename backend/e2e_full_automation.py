import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_EMAIL = "admin@prohr.ai"
ADMIN_PASS = "admin123"

def get_token():
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASS})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        exit(1)
    return res.json()["access_token"]

def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\n--- STEP 1: JOB INTAKE (JD ARCHITECT) ---")
    job_req = {
        "job_title": "Senior AI Research Engineer",
        "department": "Astral Cassini Core",
        "requirements": [
            "Expert in LangGraph and Agentic RAG architecture",
            "10+ years experience in Python and Distributed Systems",
            "Ph.D. in AI or related field strongly preferred"
        ],
        "location": "Remote / New York",
        "salary_range": "$250k - $400k"
    }
    res = requests.post(f"{BASE_URL}/jobs", json=job_req, headers=headers)
    job_id = res.json()["job_id"]
    print(f"Created Job: {job_id}. Current Stage: {res.json()['current_stage']}")

    # Polling for JD Arquitect completion (it usually happens in the start_workflow)
    # But we check status to be sure
    time.sleep(2)
    res = requests.get(f"{BASE_URL}/workflow/{job_id}/status", headers=headers)
    print(f"Polled Status: {res.json()['current_stage']}")

    print("\n--- STEP 2: JD APPROVAL (LIAISON GATE 1) ---")
    app_req = {"feedback": "Excellent JD. Proceed to sourcing immediately."}
    res = requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json=app_req, headers=headers)
    print(f"Approved JD. Next Stage: {res.json()['current_stage']}")

    print("\n--- STEP 3: CANDIDATE INJECTION (SCOUT & SCREENER) ---")
    mock_candidates = [
        {
            "id": "cand_001", "name": "Dr. Elena Vance", "email": "elena.vance@blackmesa.org",
            "skills": ["LangGraph", "Python", "RAG", "Distributed Systems"],
            "experience_years": 12, "source": "LinkedIn Scout", "relevance_score": 0.98,
            "overall_score": 95, "reasoning": "Top-tier profile with Ph.D. and specific LangGraph experience."
        },
        {
            "id": "cand_002", "name": "Gordon Freeman", "email": "gordon@xen.univ",
            "skills": ["Physics", "Python", "System Design"],
            "experience_years": 8, "source": "FAISS Discovery", "relevance_score": 0.82,
            "overall_score": 78, "reasoning": "Strong system design, but lacks specific agentic RAG depth."
        }
    ]
    
    # Use the new PATCH endpoint to inject scored candidates and advance to shortlist_review
    patch_req = {
        "action": "test_parallel_scoring_complete",
        "state_updates": {
            "candidates": mock_candidates, # Scout result
            "scored_candidates": mock_candidates, # Screener result
            "current_stage": "shortlist_review",
            "shortlist_approval": "pending"
        }
    }
    res = requests.patch(f"{BASE_URL}/workflow/{job_id}/state", json=patch_req, headers=headers)
    print(f"Injected Scored Candidates. Next Stage: {res.json()['current_stage']}")

    print("\n--- STEP 4: SHORTLIST APPROVAL (LIAISON GATE 2) ---")
    res = requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Top candidate is perfect."}, headers=headers)
    print(f"Approved Shortlist. Next Stage: {res.json()['current_stage']}")

    print("\n--- STEP 5: HIRE APPROVAL & OFFER (AGENT 07) ---")
    # Simulate interview completion and move to hire_review
    final_req = {
        "action": "test_interview_complete",
        "state_updates": {
            "final_recommendations": [{"candidate_id": "cand_001", "candidate_name": "Elena Vance", "decision": "hire", "confidence": 0.96}],
            "current_stage": "hire_review",
            "hire_approval": "pending"
        }
    }
    res = requests.patch(f"{BASE_URL}/workflow/{job_id}/state", json=final_req, headers=headers)
    print(f"Interviews Complete. Next Stage: {res.json()['current_stage']}")

    # Final Hire Approval
    res = requests.post(f"{BASE_URL}/workflow/{job_id}/approve", json={"feedback": "Hire Elena immediately."}, headers=headers)
    print(f"Final Hire Approved. Next Stage: {res.json()['current_stage']}")

    print("\n--- STEP 6: VERIFY AUDIT & OFFER ---")
    res = requests.get(f"{BASE_URL}/workflow/{job_id}/audit", headers=headers)
    print(f"Audit Trail Length: {len(res.json()['audit_log'])}")
    for entry in res.json()['audit_log'][-3:]:
        print(f"[{entry['agent']}] {entry['action']}: {entry['details']}")
    
    print("\n--- E2E TEST SEQUENCE SUCCESSFUL ---")

if __name__ == "__main__":
    main()
