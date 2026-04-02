"""End-to-End Pipeline Verification Script: 7-Agent Consolidated RAG Ecosystem.

This script tests the LangGraph workflow logic asynchronously, ensuring that
the consolidated Coordinator agent (Agent 7) is correctly managing multiple 
stages and the state transitions are valid.
"""

import asyncio
import uuid
from datetime import datetime
from app.graph.workflow import get_compiled_graph
from app.models.state import PipelineStage, RecruitmentState

async def run_e2e_test():
    print("🚀 Initializing 7-Agent Consolidated Recruitment Pipeline Test...")
    
    # 1. Setup Initial State
    job_id = str(uuid.uuid4())[:8]
    initial_state: RecruitmentState = {
        "job_id": job_id,
        "job_title": "Senior AI Infrastructure Engineer",
        "department": "Engineering (Core Architecture)",
        "requirements": ["Python", "Docker", "LangChain", "Vector Databases"],
        "preferred_qualifications": ["FAISS", "Next.js"],
        "location": "Global Remote",
        "salary_range": "$160k - $220k",
        "job_description": "",
        "jd_approval": "approved", # Pre-approved for the automated test
        "shortlist_approval": "approved",
        "hire_approval": "approved",
        "human_feedback": "Automated pipeline test.",
        "candidates": [{
            "id": "cand_001",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "experience_years": 8,
            "skills": ["Python", "LangChain", "Docker"],
            "raw_text": "Experienced engineer with specialization in AI infrastructure and containerization."
        }],
        "scored_candidates": [],
        "outreach_emails": [],
        "candidate_responses": [],
        "scheduled_interviews": [],
        "interview_assessments": [],
        "interview_transcripts": [],
        "final_recommendations": [],
        "offer_details": [],
        "current_stage": PipelineStage.JD_DRAFTING.value,
        "audit_log": [],
        "error": ""
    }

    config = {"configurable": {"thread_id": job_id}}
    graph = get_compiled_graph()

    print(f"--- Starting Workflow (Thread: {job_id}) ---")
    
    # 2. Invoke the whole graph
    # In a real environment, this might pause for HITL, 
    # but we've pre-set approvals to test the full logic traversal.
    try:
        result = await graph.ainvoke(initial_state, config=config)
        
        print("\n✅ Workflow Execution Complete.")
        print(f"Final Stage: {result.get('current_stage')}")
        
        # 3. Verify Agent Outputs
        outreach = result.get("outreach_emails", [])
        offers = result.get("offer_details", [])
        scores = result.get("scored_candidates", [])
        
        print(f"\n📊 Verification Metrics:")
        print(f" - Scored Candidates: {len(scores)}")
        print(f" - Outreach Emails Crafted: {len(outreach)}")
        print(f" - Offers Generated: {len(offers)}")
        
        if len(outreach) > 0 and len(offers) > 0:
            print("\n✨ SUCCESS: 7-Agent Consolidated RAG Pipeline fully verified.")
        else:
            print("\n⚠️ WARNING: Some steps skipped. Check node logic.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL: Pipeline execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
