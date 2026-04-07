import requests
url = 'http://127.0.0.1:8000/api/jobs'
headers = {'Content-Type': 'application/json'}
data = {"job_title": "Lead Architect", "department": "Engineering", "requirements": [], "preferred_qualifications": [], "location": "Remote", "salary_range": "Competitive"}
res = requests.post('http://127.0.0.1:8000/api/auth/login', data={'username': 'admin@prohr.ai', 'password': 'admin123'})
token = res.json()['access_token']
headers['Authorization'] = f'Bearer {token}'
res = requests.post(url, json=data, headers=headers)
print(res.status_code, res.text)
