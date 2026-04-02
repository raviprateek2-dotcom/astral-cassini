import requests

url = "http://127.0.0.1:8000/api/analytics/dashboard"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer dev-token"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
