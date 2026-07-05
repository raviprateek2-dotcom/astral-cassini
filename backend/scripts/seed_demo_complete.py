"""
seed_demo_complete.py
Creates 6 realistic recruitment pipelines, each fully populated from
intake through to final decision -- covering every dashboard tab.

Run from the backend root:
    python -m scripts.seed_demo_complete
"""

import random
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

from app.core.database import SessionLocal
from app.models.db_models import (
    Job, User, CandidateScore, Interview,
    AuditEvent, Recommendation, Outreach, Offer
)

FIRST_NAMES = ["Emma", "Liam", "Sophia", "Noah", "Olivia", "James",
               "Ava", "William", "Isabella", "Oliver", "Mia", "Ethan",
               "Charlotte", "Lucas", "Amelia", "Mason", "Harper", "Logan"]

LAST_NAMES  = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
               "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
               "Lopez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore"]

PIPELINES = [
    {
        "title": "Senior Frontend Engineer",
        "dept":  "Engineering",
        "reqs":  ["React", "TypeScript", "Next.js", "CSS", "REST APIs"],
        "salary": "$130,000 - $160,000",
    },
    {
        "title": "Machine Learning Engineer",
        "dept":  "Data Science",
        "reqs":  ["Python", "PyTorch", "LLMs", "MLOps", "SQL"],
        "salary": "$150,000 - $185,000",
    },
    {
        "title": "Product Manager",
        "dept":  "Product",
        "reqs":  ["Roadmapping", "Agile", "Stakeholder Management", "Analytics"],
        "salary": "$120,000 - $145,000",
    },
    {
        "title": "DevOps Engineer",
        "dept":  "Infrastructure",
        "reqs":  ["Kubernetes", "Terraform", "AWS", "CI/CD", "Docker"],
        "salary": "$135,000 - $165,000",
    },
    {
        "title": "UX Designer",
        "dept":  "Design",
        "reqs":  ["Figma", "User Research", "Prototyping", "Accessibility", "Design Systems"],
        "salary": "$110,000 - $135,000",
    },
    {
        "title": "Backend Engineer (Python)",
        "dept":  "Engineering",
        "reqs":  ["FastAPI", "PostgreSQL", "Redis", "Docker", "System Design"],
        "salary": "$140,000 - $170,000",
    },
]

AUDIT_TIMELINE = [
    ("Architect",       "Drafted Job Description",
     "JD Architect generated a 7-section structured job description with bias audit. Critique passed on iteration 1.", "jd_drafting"),
    ("Critic",          "Approved Job Description",
     "All 7 required sections present. Bias audit: no gendered language detected. Score: 9.1/10.", "jd_review"),
    ("Scout",           "Sourced Candidates",
     "BM25 + semantic search returned 42 resume matches. Top 10 forwarded to Screener.", "sourcing"),
    ("Screener",        "Scored & Ranked Candidates",
     "Scored 10 candidates across skills, experience, education, cultural fit. 5 passed 70% threshold.", "screening"),
    ("Outreach",        "Sent Personalised Emails",
     "SendGrid delivered 5 personalised outreach emails. Subject line A/B tested for open rate.", "outreach"),
    ("ResponseTracker", "Classified Response Intent",
     "4/5 candidates responded: 3 interested, 1 asking questions. 0 declines.", "engagement"),
    ("Coordinator",     "Scheduled Interviews",
     "Google Calendar slots confirmed for 3 candidates. Technical + behavioural rounds scheduled.", "scheduling"),
    ("Interviewer",     "Completed Interview Assessments",
     "Structured interviews conducted for 3 candidates. Transcripts anonymised before LLM analysis.", "interviewing"),
    ("Decider",         "Generated Final Recommendations",
     "Weighted scoring: 60% interview, 40% screening. 2 hire, 1 no_hire. Decision trace logged.", "decision"),
]

STRENGTHS_POOL = [
    "Strong systems-level thinking with practical implementation experience",
    "Excellent communication -- clearly articulates complex trade-offs",
    "Proactive learner who regularly contributes to open-source",
    "Deep expertise in the core technical stack required by the role",
    "Cross-functional collaboration experience across 3+ teams",
    "Led projects end-to-end with measurable business outcomes",
    "Strong data-driven decision making with A/B testing background",
]

GAPS_POOL = [
    "Limited experience with large-scale distributed systems",
    "No prior management experience (not required but beneficial)",
    "Kubernetes exposure is mainly theoretical -- hands-on time limited",
    "Could benefit from more exposure to exec-level stakeholder communication",
]

OBSERVATIONS_POOL = [
    "Solved the dynamic programming problem efficiently in under 15 minutes",
    "Gave clear, structured answers using the STAR method throughout",
    "Demonstrated strong architectural instincts in the system design round",
    "Articulate communicator -- easy to follow even on complex topics",
    "Showed genuine curiosity about the product and asked excellent questions",
    "Impressive portfolio with real production impact metrics",
]

CONCERNS_POOL = [
    "Slightly hesitant on distributed systems edge cases",
    "Limited experience in the specific cloud provider we use",
    "Would need onboarding support for the internal tooling stack",
]


def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rand_score(lo=72.0, hi=97.0):
    return round(random.uniform(lo, hi), 1)


def rand_float(lo=7.0, hi=9.8):
    return round(random.uniform(lo, hi), 1)


def seed():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        admin_id = admin.id if admin else None

        total_jobs = 0
        total_candidates = 0

        for pipeline in PIPELINES:
            job_id  = f"REQ-{uuid.uuid4().hex[:6].upper()}"
            created = datetime.now(timezone.utc) - timedelta(days=random.randint(7, 21))

            job = Job(
                job_id             = job_id,
                job_title          = pipeline["title"],
                department         = pipeline["dept"],
                location           = random.choice(["Remote", "New York, NY", "San Francisco, CA", "Austin, TX"]),
                salary_range       = pipeline["salary"],
                requirements       = pipeline["reqs"],
                current_stage      = "decision",
                jd_approval        = "approved",
                shortlist_approval = "approved",
                hire_approval      = "approved",
                outreach_completed = True,
                offer_sent         = True,
                avg_match_percentage = round(random.uniform(78, 91), 1),
                job_description    = (
                    f"## {pipeline['title']}\n\n**Department:** {pipeline['dept']}\n\n"
                    "### Role Summary\nWe are seeking a highly motivated professional to join our growing team.\n\n"
                    "### Core Responsibilities\n- Lead technical design and implementation\n"
                    "- Collaborate with cross-functional stakeholders\n- Mentor junior team members\n\n"
                    "### Required Qualifications\n" +
                    "\n".join(f"- {r}" for r in pipeline["reqs"]) +
                    "\n\n### Equal Opportunity Statement\nWe are an equal opportunity employer."
                ),
                created_by_id      = admin_id,
                created_at         = created,
                completed_at       = created + timedelta(days=random.randint(10, 18)),
                workflow_state     = {},
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            total_jobs += 1

            # Audit Trail
            for idx, (agent, action, details, stage) in enumerate(AUDIT_TIMELINE):
                db.add(AuditEvent(
                    job_id    = job_id,
                    agent     = agent,
                    action    = action,
                    details   = details,
                    stage     = stage,
                    timestamp = created + timedelta(hours=idx * 5),
                ))

            # Candidates
            n_candidates  = random.randint(3, 4)
            decision_pool = (["hire", "hire", "no_hire"] + ["maybe"] * (n_candidates - 3))
            random.shuffle(decision_pool)

            for i in range(n_candidates):
                c_id   = f"CAND-{uuid.uuid4().hex[:6].upper()}"
                c_name = rand_name()
                exp_yrs = random.randint(3, 10)

                s = rand_score(); e = rand_score(); edu = rand_score(); c = rand_score()
                overall = round(s*0.35 + e*0.25 + edu*0.20 + c*0.20, 1)

                db.add(CandidateScore(
                    job_id           = job_id,
                    candidate_id     = c_id,
                    candidate_name   = c_name,
                    overall_score    = overall,
                    match_percentage = overall,
                    skills_match     = s,
                    experience_match = e,
                    education_match  = edu,
                    cultural_fit     = c,
                    strengths        = random.sample(STRENGTHS_POOL, k=3),
                    gaps             = random.sample(GAPS_POOL, k=random.randint(1, 2)),
                    missing_skills   = random.sample(pipeline["reqs"], k=random.randint(0, 1)),
                    overqualification= [],
                    reasoning        = (
                        f"{c_name} brings {exp_yrs} years of experience with strong alignment "
                        f"to the core stack. Skills match of {s:.1f}% suggests a solid technical "
                        "foundation. Minor gaps are easily addressed during onboarding."
                    ),
                ))

                intent = random.choice(["interested", "interested", "questions_asked", "reschedule_request"])
                responses = {
                    "interested":         "Thank you for reaching out! I am very excited about this opportunity.",
                    "questions_asked":    "This looks great! Could you share more about team size and growth?",
                    "reschedule_request": "I am interested but travelling. Could we schedule for next week?",
                }
                db.add(Outreach(
                    job_id         = job_id,
                    candidate_id   = c_id,
                    candidate_name = c_name,
                    email_subject  = f"Exciting Opportunity: {pipeline['title']}",
                    email_body     = f"Hi {c_name.split()[0]}, your profile stood out for the {pipeline['title']} role.",
                    response_text  = responses[intent],
                    engagement_level = "High" if intent == "interested" else "Medium",
                    status         = "responding",
                ))

                t = rand_float(); comm = rand_float(); p = rand_float(); f = rand_float()
                oi = round((t + comm + p + f) / 4, 1)

                db.add(Interview(
                    job_id                = job_id,
                    candidate_id          = c_id,
                    candidate_name        = c_name,
                    interview_type        = "technical",
                    status                = "completed",
                    duration_minutes      = random.choice([45, 60, 75]),
                    interviewers          = ["Sarah Chen (Engineering Lead)", "Marcus Webb (Staff Eng)"],
                    overall_score         = oi,
                    technical_score       = t,
                    communication_score   = comm,
                    problem_solving_score = p,
                    cultural_fit_score    = f,
                    key_observations      = random.sample(OBSERVATIONS_POOL, k=3),
                    concerns              = random.sample(CONCERNS_POOL, k=random.randint(0, 1)),
                ))

                decision    = decision_pool[i]
                sw          = round(overall * 0.40, 1)
                iw          = round(oi * 10 * 0.60, 1)
                weighted    = round(sw + iw, 1)
                confidence  = round(random.uniform(0.72, 0.96), 2)

                risk_factors = []
                if decision == "no_hire":
                    risk_factors = ["Technical score below threshold", "Experience misaligned with seniority"]
                elif decision == "maybe":
                    risk_factors = ["Additional panel interview recommended"]

                db.add(Recommendation(
                    job_id                 = job_id,
                    candidate_id           = c_id,
                    candidate_name         = c_name,
                    decision               = decision,
                    confidence             = confidence,
                    overall_weighted_score = weighted,
                    screening_weight       = sw,
                    interview_weight       = iw,
                    reasoning              = (
                        f"Aggregate: screening {sw:.1f}pts (40%) + interview {iw:.1f}pts (60%) = {weighted:.1f}. "
                        f"{c_name} is marked {decision.upper().replace('_',' ')} with {confidence*100:.0f}% confidence."
                    ),
                    risk_factors = risk_factors,
                ))

                if decision == "hire":
                    db.add(Offer(
                        job_id         = job_id,
                        candidate_id   = c_id,
                        candidate_name = c_name,
                        salary_offered = pipeline["salary"].split("-")[0].strip() + " base",
                        status         = random.choice(["sent", "accepted"]),
                        offer_markdown = (
                            f"# Offer of Employment\n\nDear {c_name},\n\n"
                            f"We are delighted to extend this offer for **{pipeline['title']}** "
                            f"in our **{pipeline['dept']}** team.\n\n"
                            f"**Compensation:** {pipeline['salary']}\n"
                            "**Benefits:** Medical, Dental, Vision, 401(k) match, Unlimited PTO, Equity\n\n"
                            "This offer is subject to successful background verification.\n\n"
                            "*PRO HR -- Equal Opportunity Employer*"
                        ),
                    ))

                total_candidates += 1

            db.commit()
            print(f"  Created [{job_id}] {pipeline['title']} with {n_candidates} candidates -> decision")

        print(f"\nDone: {total_jobs} pipelines, {total_candidates} candidates seeded.")

    except Exception as ex:
        db.rollback()
        print(f"ERROR: {ex}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
