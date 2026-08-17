import sys
import os
import pytest
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.resume import Resume, ResumeSkill
from app.models.job import Job, JobSkill
from app.models.analysis import Analysis
from app.models.session import SessionModel
from app.services.matching import MatchingEngine
from app.core.database import SessionLocal, get_db
from fastapi.testclient import TestClient
from app.main import app

# =========================================================================
# 1. Deterministic Engine Logic Core Tests
# =========================================================================

def _build_mock_resume_and_job():
    resume = Resume(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        filename="test.pdf",
        raw_text="Experienced engineer with a background in Python, machine learning, and React. Built a massive REST API with FastAPI.",
        parsed_data={"experience": [{}], "education": [{}], "projects": [{}]},
        content_hash="mockhash123",
    )

    python_id = uuid.uuid4()
    fastapi_id = uuid.uuid4()

    resume.skills = [
        ResumeSkill(skill_id=python_id, raw_text="Python", evidence_source="skills", confidence=1.0),
        ResumeSkill(skill_id=fastapi_id, raw_text="FastAPI", evidence_source="projects", confidence=1.0),
        ResumeSkill(skill_id=None, raw_text="Artificial Intelligence", evidence_source="summary", confidence=1.0),
        ResumeSkill(skill_id=None, raw_text="React", evidence_source="skills", confidence=1.0),
    ]

    job = Job(
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        title="Backend Dev",
        raw_text="Looking for a Python backend engineer. Must know FastAPI. Experience with Deep Learning is a plus. Needs to understand Kubernetes orchestration.",
        parsed_data={"experience_years_required": 1},
        content_hash="mockhash456"
    )

    job.skills = [
        JobSkill(skill_id=python_id, raw_text="Python", required=True, importance=1.0),
        JobSkill(skill_id=fastapi_id, raw_text="Fast API", required=True, importance=1.0),
        JobSkill(skill_id=None, raw_text="AI Systems", required=False, importance=1.0),
        JobSkill(skill_id=None, raw_text="Kubernetes", required=True, importance=1.0)
    ]
    return resume, job


def test_matching_engine_basic_scoring():
    resume, job = _build_mock_resume_and_job()

    engine = MatchingEngine()
    ans = engine.calculate_match(resume, job)

    assert "overall_score" in ans, "Should calculate global score"
    assert "sub_scores" in ans, "Should calculate matrix array"

    assert any(ms["tier"] == "exact" and ms["skill"] == "Python" for ms in ans["matched_skills"])
    assert any(ms["tier"] == "alias" and ms["skill"] == "Fast API" for ms in ans["matched_skills"])

    # Expects relation logic bridging the 0.75 margin (Artificial Intelligence / AI Systems = 0.7852)
    assert any(rs["skill"] == "AI Systems" for rs in ans["related_skills"])
    assert any(ms["skill"] == "Kubernetes" for ms in ans["missing_skills"])

    ans2 = engine.calculate_match(resume, job)
    assert ans["overall_score"] == ans2["overall_score"], "Output must be completely deterministic without LLM calls"

def test_engine_missing_skills():
    resume, job = _build_mock_resume_and_job()

    # Intentionally empty out the resume skills to force fail
    resume.skills = []

    engine = MatchingEngine()
    ans = engine.calculate_match(resume, job)

    assert len(ans["missing_skills"]) == 4, "All 4 job skills should be classified as missing."
    assert ans["sub_scores"]["skill_score"] == 0.0

# =========================================================================
# 2. End-to-End Dependency Injected Caching Tests against Real PostgreSQL
# =========================================================================

# Database testing isolation: Instead of simple standard session rollbacks, we manually tear down
# generated specific records at the end of the test explicitly to prevent global cascades.
@pytest.fixture(name="db_session")
def db_session_fixture():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(name="client")
def client_fixture(db_session):
    def override_get_db():
        # Important: generate unique inner connections so transactions don't collide
        inner_db = SessionLocal()
        try:
           yield inner_db
        finally:
           inner_db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_content_hash_caching_behavior(client, db_session):
    # Unique scoping to completely prevent test collision
    session_id = uuid.uuid4()
    run_hash = str(uuid.uuid4())

    sess = SessionModel(id=session_id)
    db_session.add(sess)
    db_session.flush()

    # Resume A
    resume_a = Resume(
        id=uuid.uuid4(),
        session_id=session_id,
        filename="resume_a.pdf",
        raw_text="Test resume A content.",
        parsed_data={},
        content_hash=f"resume_hash_A_{run_hash}"
    )
    # Resume B (Identical hash as A)
    resume_b = Resume(
        id=uuid.uuid4(),
        session_id=session_id,
        filename="resume_b.pdf",
        raw_text="Test resume B content.",
        parsed_data={},
        content_hash=f"resume_hash_A_{run_hash}" # IDENTICAL CONTENT HASH
    )
    # Resume C (Different Hash)
    resume_c = Resume(
        id=uuid.uuid4(),
        session_id=session_id,
        filename="resume_c.pdf",
        raw_text="Completely different resume C",
        parsed_data={},
        content_hash=f"resume_hash_X_{run_hash}"
    )

    # Job A
    job_a = Job(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Job A",
        raw_text="Job raw text 1",
        parsed_data={},
        content_hash=f"job_hash_A_{run_hash}"
    )
    # Job B (Identical hash as A)
    job_b = Job(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Job B",
        raw_text="Different job raw text",
        parsed_data={},
        content_hash=f"job_hash_A_{run_hash}" # IDENTICAL CONTENT HASH
    )
    # Job C (Different hash)
    job_c = Job(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Job C",
        raw_text="Completely different Job C text",
        parsed_data={},
        content_hash=f"job_hash_X_{run_hash}"
    )

    db_session.add_all([resume_a, resume_b, resume_c, job_a, job_b, job_c])
    db_session.commit()

    try:
        # A. First hit: Should calculate and return cached=False
        resp1 = client.post("/api/analyze", json={"resume_id": str(resume_a.id), "job_id": str(job_a.id)})
        assert resp1.status_code == 200, f"Failed: {resp1.json()}"
        data1 = resp1.json()
        assert data1["cached"] is False, "First request must calculate the match, not be cached."

        # B. Second hit (Same Exact Models): Should return cached=True
        resp2 = client.post("/api/analyze", json={"resume_id": str(resume_a.id), "job_id": str(job_a.id)})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["cached"] is True, "Identical request must hit cache."
        assert data1["id"] == data2["id"], "Must return exactly the same database Analysis ID."

        # C. Third hit (Different UUIDs, but IDENTICAL content_hash texts)
        resp3 = client.post("/api/analyze", json={"resume_id": str(resume_b.id), "job_id": str(job_b.id)})
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["cached"] is True, "Different UUIDs with identical content_hash must correctly hit the cache."

        # D. Fourth hit (Resume has DIFFERENT content_hash)
        resp4 = client.post("/api/analyze", json={"resume_id": str(resume_c.id), "job_id": str(job_a.id)})
        assert resp4.status_code == 200
        data4 = resp4.json()
        assert data4["cached"] is False, "A changed resume content_hash must force recomputation."

        # E. Fifth hit (Job has DIFFERENT content_hash)
        resp5 = client.post("/api/analyze", json={"resume_id": str(resume_a.id), "job_id": str(job_c.id)})
        assert resp5.status_code == 200
        data5 = resp5.json()
        assert data5["cached"] is False, "A changed job content_hash must force recomputation."

    finally:
        # Explicit test cleanup - delete in FK order: recommendations -> analyses -> jobs/resumes -> session
        from app.models.analysis import Recommendation
        analysis_ids = [
            row.id for row in db_session.query(Analysis.id).filter(Analysis.session_id == session_id)
        ]
        if analysis_ids:
            db_session.query(Recommendation).filter(Recommendation.analysis_id.in_(analysis_ids)).delete(synchronize_session=False)
        db_session.query(Analysis).filter(Analysis.session_id == session_id).delete()
        db_session.query(Job).filter(Job.session_id == session_id).delete()
        db_session.query(Resume).filter(Resume.session_id == session_id).delete()
        db_session.query(SessionModel).filter(SessionModel.id == session_id).delete()
        db_session.commit()
