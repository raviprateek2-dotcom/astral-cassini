"""
Full Pipeline Audit Script - Principal Agentic Engineer (9db8de49)
Advances the pipeline stage by stage and prints a complete audit at each step.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"
JOB_ID = "9db8de49"

SEPARATOR = "=" * 70

def get_state():
    r = requests.get(f"{BASE_URL}/jobs/{JOB_ID}")
    return r.json().get("state", {})

def get_stage():
    r = requests.get(f"{BASE_URL}/workflow/{JOB_ID}/status")
    return r.json().get("current_stage", "")

def approve(feedback="Approved."):
    return requests.post(f"{BASE_URL}/workflow/{JOB_ID}/approve", json={"feedback": feedback})

def wait_for(target_stage, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        stage = get_stage()
        print(f"  ...waiting (current: {stage})")
        if stage == target_stage:
            return True
        if stage in ("completed", "error"):
            return False
        time.sleep(2)
    return False

def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)

def print_audit_since(state, stages):
    entries = [e for e in state.get("audit_log", []) if e.get("stage") in stages]
    for e in entries:
        agent = e.get("agent", "?")
        action = e.get("action", "?")
        details = e.get("details", "")
        stage = e.get("stage", "?")
        try:
            parsed = json.loads(details)
            details_str = json.dumps(parsed, indent=4)
        except Exception:
            details_str = details[:400]
        print(f"\n  [{stage.upper()}] {agent} >> {action}")
        print(f"  {details_str}")


# ──────────────────────────────────────────────────────────────────────
# Current state check
# ──────────────────────────────────────────────────────────────────────
section("CHECKING CURRENT PIPELINE STATE")
current = get_stage()
print(f"  Job ID   : {JOB_ID}")
print(f"  Stage    : {current}")


# ──────────────────────────────────────────────────────────────────────
# STAGE: shortlist_review → APPROVE → outreach → engagement → hire_review
# ──────────────────────────────────────────────────────────────────────
if current == "shortlist_review":
    section("STEP 3: APPROVING SHORTLIST → Triggering Outreach & Coordination")
    approve("Top 3 candidates approved. Proceed to outreach.")
    print("  Approval sent. Waiting for hire_review...")
    ok = wait_for("hire_review", timeout=90)
    if not ok:
        current = get_stage()
        print(f"  WARNING: Did not reach hire_review. Currently at: {current}")
    else:
        state = get_state()

        section("OUTREACH AGENT OUTPUT")
        emails = state.get("outreach_emails", [])
        print(f"  Total outreach emails generated: {len(emails)}")
        for i, em in enumerate(emails[:3], 1):
            name = em.get("candidate_name", "?")
            subj = em.get("subject", "")
            body = em.get("body", "")[:200]
            status = em.get("status", "")
            print(f"\n  [{i}] To: {name}")
            print(f"      Subject : {subj}")
            print(f"      Status  : {status}")
            print(f"      Body    : {body}...")

        section("RESPONSE TRACKER AGENT OUTPUT")
        responses = state.get("candidate_responses", [])
        print(f"  Candidate responses captured: {len(responses)}")
        for resp in responses:
            name = resp.get("candidate_name", "?")
            intent = resp.get("intent", "?")
            eng = resp.get("engagement_level", "?")
            msg = resp.get("response_text", "")[:120]
            print(f"\n  Candidate : {name}")
            print(f"  Intent    : {intent}  |  Engagement: {eng}")
            print(f"  Response  : {msg}")

        section("COORDINATOR AGENT OUTPUT (Scheduling + Interviews + Decision)")
        recs = state.get("final_recommendations", [])
        traces = state.get("decision_traces", [])
        interviews = state.get("scheduled_interviews", [])
        assessments = state.get("interview_assessments", [])

        print(f"  Scheduled interviews : {len(interviews)}")
        for iv in interviews[:3]:
            print(f"    - {iv.get('candidate_name')} @ {iv.get('interview_time')} via {iv.get('meeting_link')}")

        print(f"\n  Interview assessments : {len(assessments)}")
        for a in assessments[:3]:
            name = a.get("candidate_name", "?")
            tech = a.get("technical_score", "?")
            comm = a.get("communication_score", "?")
            cult = a.get("cultural_fit_score", "?")
            print(f"    - {name}: Tech={tech} Comm={comm} Culture={cult}")

        print(f"\n  Final Recommendations ({len(recs)} total):")
        for rec in recs:
            name = rec.get("candidate_name", "?")
            decision = rec.get("decision", "?")
            score = rec.get("overall_weighted_score", "?")
            rule = rec.get("rule_applied", "")
            print(f"    - {name}: {decision.upper()} (Weighted Score: {score})")
            print(f"      Rule applied: {rule}")

        print(f"\n  Decision Traces ({len(traces)}):")
        for t in traces[:2]:
            name = t.get("candidate_id", "?")
            print(f"    {name}: screen={t.get('screening_score')} interview={t.get('interview_score')} final={t.get('final_score')}")

        section("AUDIT LOG - Outreach + Engagement + Coordination Stages")
        print_audit_since(state, ["outreach", "engagement", "scheduling", "interviewing", "decision", "hire_review"])

        current = get_stage()


# ──────────────────────────────────────────────────────────────────────
# STAGE: hire_review → APPROVE → offer → completed
# ──────────────────────────────────────────────────────────────────────
current = get_stage()
if current == "hire_review":
    section("STEP 4: APPROVING HIRE DECISION → Triggering Offer Generator")
    approve("Approved. Generate offer for top candidate.")
    print("  Approval sent. Waiting for completed...")
    ok = wait_for("completed", timeout=60)
    state = get_state()

    section("OFFER GENERATOR OUTPUT")
    offers = state.get("offer_details", [])
    print(f"  Offers generated: {len(offers)}")
    for offer in offers:
        name = offer.get("candidate_name", "?")
        print(f"\n  Candidate : {name}")
        print(f"  Offer Letter Preview (first 600 chars):\n")
        print(offer.get("offer_markdown", "")[:600])
        print("  ...")

    section("AUDIT LOG - Offer Stage")
    print_audit_since(state, ["offer"])


# ──────────────────────────────────────────────────────────────────────
# FINAL PIPELINE SUMMARY
# ──────────────────────────────────────────────────────────────────────
final_stage = get_stage()
state = get_state()

section(f"PIPELINE COMPLETE — Final Stage: {final_stage.upper()}")
print(f"  Total audit log entries : {len(state.get('audit_log', []))}")
print(f"  Candidates sourced      : {len(state.get('candidates', []))}")
print(f"  Candidates screened     : {len(state.get('scored_candidates', []))}")
print(f"  Outreach emails sent    : {len(state.get('outreach_emails', []))}")
print(f"  Candidate responses     : {len(state.get('candidate_responses', []))}")
print(f"  Final recommendations   : {len(state.get('final_recommendations', []))}")
print(f"  Offer letters generated : {len(state.get('offer_details', []))}")
print(f"\n  Pipeline ended at stage : {final_stage}")
print(f"\n{SEPARATOR}")
print("  Done.")
print(SEPARATOR)
