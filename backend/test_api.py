import requests

BASE_URL = "http://localhost:8000/api"

print("1. Logging in as HR...")
resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "hr@prohr.ai", "password": "hr123"})
resp.raise_for_status()
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login successful.")

print("\n2. Getting Analytics Summary...")
resp = requests.get(f"{BASE_URL}/analytics/summary", headers=headers)
resp.raise_for_status()
print(resp.json())

print("\n3. Creating a Job Requisition...")
payload = {
    "job_title": "Senior Python Developer",
    "department": "Engineering",
    "requirements": ["Python 3.10+", "FastAPI", "PostgreSQL", "LangGraph"],
    "preferred_qualifications": ["AWS", "Docker"],
    "location": "Remote",
    "salary_range": "$120k - $150k"
}
resp = requests.post(f"{BASE_URL}/jobs", json=payload, headers=headers)
if resp.status_code != 200:
    print("Error:", resp.text)
resp.raise_for_status()
job_data = resp.json()
print("Job Created:", job_data)
job_id = job_data["job_id"]

print("\n4. Listing Jobs...")
resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
resp.raise_for_status()
print("Jobs:", resp.json())

print("\n5. Getting Workflow Status...")
resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
resp.raise_for_status()
print("Workflow Status:", resp.json())

print("\nAll Tests Passed Successfully!")
