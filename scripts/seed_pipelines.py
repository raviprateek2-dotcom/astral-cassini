import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("🚀 Starting Manual E2E Pipeline Testing...")
    
    # 1. Login to get token
    login_data = {"username": "admin@prohr.ai", "password": "password123"}
    r = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    
    if r.status_code != 200:
        print(f"❌ Login failed: {r.text}")
        return
        
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in successfully.")
    
    # 2. Create 3 Jobs (Pipelines)
    jobs_data = [
        {"job_title": "Senior Frontend Engineer", "department": "Engineering", "description": "React/Next.js expert needed.", "requirements": ["5+ years JS experience."]},
        {"job_title": "Product Marketing Manager", "department": "Marketing", "description": "GTM strategy experience.", "requirements": ["Previous B2B SaaS experience."]},
        {"job_title": "DevOps Specialist", "department": "Infrastructure", "description": "AWS, Docker, CI/CD pipelines.", "requirements": ["AWS Certified."]}
    ]
    
    created_jobs = []
    for job in jobs_data:
        time.sleep(1) # Avoid rate limits
        res = requests.post(f"{BASE_URL}/api/jobs/", json=job, headers=headers)
        if res.status_code == 200:
            job_id = res.json().get("job_id")
            created_jobs.append((job_id, job["job_title"]))
            print(f"✅ Created Job: {job['job_title']} (ID: {job_id})")
        else:
            print(f"❌ Failed to create job: {res.text}")

    # 3. Add Candidates to Jobs and Move them through Pipeline using State Patching
    candidates_templates = [
        [
            {"id": f"c_{uuid.uuid4().hex[:8]}", "name": "Alice Smith", "email": "alice@example.com", "skills": ["React", "TypeScript"], "experience_years": 6, "source": "manual_upload", "relevance_score": 0.95, "screening_score": 85, "screening_rationale": "Strong frontend background.", "status": "shortlisted"},
            {"id": f"c_{uuid.uuid4().hex[:8]}", "name": "Bob Miller", "email": "bob@example.com", "skills": ["Vue.js"], "experience_years": 2, "source": "manual_upload", "relevance_score": 0.45, "screening_score": 40, "screening_rationale": "Insufficient experience.", "status": "rejected"}
        ],
        [
            {"id": f"c_{uuid.uuid4().hex[:8]}", "name": "Charlie Brown", "email": "charlie@example.com", "skills": ["Marketing", "SaaS"], "experience_years": 8, "source": "manual_upload", "relevance_score": 0.90, "screening_score": 90, "screening_rationale": "Excellent product launch experience.", "status": "shortlisted"}
        ],
        [
            {"id": f"c_{uuid.uuid4().hex[:8]}", "name": "Diana Prince", "email": "diana@example.com", "skills": ["AWS", "Kubernetes", "Docker"], "experience_years": 5, "source": "manual_upload", "relevance_score": 0.88, "screening_score": 80, "screening_rationale": "Solid cloud certifications.", "status": "shortlisted"}
        ]
    ]

    for idx, (job_id, job_title) in enumerate(created_jobs):
        candidates = candidates_templates[idx]
        
        # Patch the state to screening stage with candidates
        patch_payload = {
            "action": "manual_patch",
            "reason": "Populating manual test data",
            "state_updates": {
                "current_stage": "screening",
                "candidates": candidates
            }
        }
        
        time.sleep(1)
        patch_res = requests.patch(f"{BASE_URL}/api/workflow/{job_id}/state", json=patch_payload, headers=headers)
        
        if patch_res.status_code == 200:
            print(f"✅ Successfully seeded candidates for '{job_title}' (ID: {job_id})")
            for c in candidates:
                print(f"  -> Added Candidate: {c['name']} (Status: {c['status']})")
        else:
            print(f"❌ Failed to seed candidates for '{job_title}': {patch_res.text}")

    print("🎉 Manual Pipeline Testing Seed Script Complete!")

if __name__ == "__main__":
    main()
