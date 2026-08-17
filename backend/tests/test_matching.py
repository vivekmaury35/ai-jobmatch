import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.resume import Resume, ResumeSkill
from app.models.job import Job, JobSkill
from app.services.matching import MatchingEngine
import uuid

def test_engine():
    print("Testing Deterministic Matching Engine...")

    # Mock Data
    resume = Resume(
        id=uuid.uuid4(),
        raw_text="Experienced engineer with a background in Python, machine learning, and React. Built a massive REST API with FastAPI.",
        parsed_data={"experience": [{}], "education": [{}], "projects": [{}]}
    )

    # Simulate DB relationships mapped by normalizer
    python_id = uuid.uuid4()
    fastapi_id = uuid.uuid4()

    resume.skills = [
        ResumeSkill(skill_id=python_id, raw_text="Python", evidence_source="skills", confidence=1.0),
        ResumeSkill(skill_id=fastapi_id, raw_text="FastAPI", evidence_source="projects", confidence=1.0),
        ResumeSkill(skill_id=None, raw_text="Machine Learning", evidence_source="summary", confidence=1.0),
        ResumeSkill(skill_id=None, raw_text="React", evidence_source="skills", confidence=1.0),
    ]

    job = Job(
        id=uuid.uuid4(),
        raw_text="Looking for a Python backend engineer. Must know FastAPI. Experience with Deep Learning is a plus. Needs to understand Kubernetes orchestration.",
        parsed_data={"experience_years_required": 1}
    )

    job.skills = [
        JobSkill(skill_id=python_id, raw_text="Python", required=True, importance=1.0),
        JobSkill(skill_id=fastapi_id, raw_text="Fast API", required=True, importance=1.0), # Alias mapping behavior mock
        JobSkill(skill_id=None, raw_text="Deep Learning", required=False, importance=1.0), # Semantic Test! Resume has "Machine Learning"
        JobSkill(skill_id=None, raw_text="Kubernetes", required=True, importance=1.0) # Completely missing
    ]

    engine = MatchingEngine()

    print("Running matrix...")
    ans = engine.calculate_match(resume, job)

    print("\n--- MATRIX OUTPUT ---")
    print(f"Overall Score:  {ans['overall_score']}")
    print(f"Sub-Scores:     {ans['sub_scores']}")
    print(f"\nMatched Skills: {ans['matched_skills']}")
    print(f"Related Skills: {ans['related_skills']}")
    print(f"Missing Skills: {ans['missing_skills']}")

if __name__ == "__main__":
    test_engine()
