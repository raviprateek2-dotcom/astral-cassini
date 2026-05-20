import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("Testing manual pipeline creation...")
    
    # 1. Login
    login_data = {"username": "admin@prohr.ai", "password": "password123"}
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        sys.exit(1)
        
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        sys.exit(1)
        
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Successfully logged in.")
    
    # 2. Create Job
    job_payload = {
        "job_title": "Security Architect",
        "department": "Security",
        "requirements": ["7+ years of security experience.", "Experience with ISO 27001 / SOC 2."],
        "preferred_qualifications": ["CISSP certification"],
        "location": "Remote",
        "salary_range": "$150,000 - $180,000"
    }
    
    res = requests.post(f"{BASE_URL}/api/jobs/", json=job_payload, headers=headers)
    if res.status_code != 200:
        print(f"Failed to create job: {res.text}")
        sys.exit(1)
        
    job_data = res.json()
    job_id = job_data.get("job_id")
    print(f"Successfully created job 'Security Architect' with ID: {job_id}")
    
    # 3. Verify in Jobs List
    list_res = requests.get(f"{BASE_URL}/api/jobs/", headers=headers)
    if list_res.status_code != 200:
        print(f"Failed to list jobs: {list_res.text}")
        sys.exit(1)
        
    jobs = list_res.json()
    found = False
    for j in jobs:
        if j.get("job_id") == job_id:
            found = True
            print(f"Verified: Job found in jobs list with status: {j.get('status')}")
            break
            
    if found:
        print("Manual pipeline creation verified successfully!")
    else:
        print("Error: Job created but not found in list.")
        sys.exit(1)

if __name__ == "__main__":
    main()
