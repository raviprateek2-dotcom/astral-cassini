import requests, json, time

BASE_URL = 'http://127.0.0.1:8000/api'
job_id = '9db8de49'

requests.post(f'{BASE_URL}/workflow/{job_id}/approve', json={'feedback': 'Shortlist looks good.'})
time.sleep(5)

st = requests.get(f'{BASE_URL}/jobs/{job_id}').json()
state = st.get('state', {})

print('--- OUTREACH EMAILS (Top 2) ---')
for email in state.get('outreach_emails', [])[:2]:
    print(f"To: {email.get('candidate_name')} | Subject: {email.get('subject')}")
    print(f"{email.get('body')[:150]}...\n")

print('--- CANDIDATE RESPONSES ---')
for resp in state.get('candidate_responses', []):
    print(f"From: {resp.get('candidate_name')} | Intent: {resp.get('intent')} | Engagement: {resp.get('engagement_level')}")

print('\n--- FINAL RECOMMENDATIONS ---')
for rec in state.get('final_recommendations', []):
    print(f"{rec.get('candidate_name')}: {rec.get('decision')} (Score: {rec.get('overall_weighted_score')})")
