import requests
r = requests.get("http://127.0.0.1:8000/api/jobs")
print("All jobs:", [j["job_id"] for j in r.json()])

if r.json():
    job_id = r.json()[0]["job_id"]
    print("Checking job:", job_id)
    r2 = requests.get(f"http://127.0.0.1:8000/api/jobs/{job_id}")
    print("State:", r2.json().get("state"))
