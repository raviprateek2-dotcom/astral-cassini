import random
from locust import HttpUser, task, between, events
import json

class ProHrUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a Locust user starts before any task is scheduled"""
        self.login()

    def login(self):
        # We assume the default test admin credentials exist for load testing
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "password"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            
    @task(3)
    def view_dashboard(self):
        """Simulate loading the main dashboard jobs list"""
        if self.headers:
            self.client.get("/api/jobs", headers=self.headers)
            
    @task(1)
    def view_specific_job_workflow(self):
        """Simulate clicking into a specific job and viewing its pipeline"""
        if self.headers:
            # First fetch jobs
            resp = self.client.get("/api/jobs", headers=self.headers)
            if resp.status_code == 200:
                jobs = resp.json().get("jobs", [])
                if jobs:
                    # Pick a random job to view
                    job_id = random.choice(jobs)["id"]
                    self.client.get(f"/api/workflow/{job_id}/state", headers=self.headers)
                    self.client.get(f"/api/candidates?job_id={job_id}", headers=self.headers)
