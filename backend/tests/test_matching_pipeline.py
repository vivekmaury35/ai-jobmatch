"""
Integration-style tests for app/services/matching.py that mock out the LLM
call (AIService.evaluate_candidate_expertly) so the deterministic parts of
the pipeline - compound-requirement re-verification, certification
separation, INFORMATIONAL filtering, and priority-weighted scoring - can be
exercised quickly and without network access or an API key.

Covers spec test cases:
    C. Compound Match (via the LLM-missed-it-but-code-catches-it path)
    H. Preferred Skill Missing (should not cause a major score reduction)
    I. Company Description Noise (INFORMATIONAL items never become gaps)
    J. Certification Separation
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.matching import MatchingEngine
from app.schemas.analysis import (
    ExpertEvaluationSchema,
    SkillEvidenceSchema,
    CertificationEvidenceSchema,
)


class FakeResume:
    def __init__(self, raw_text, parsed_data):
        self.raw_text = raw_text
        self.parsed_data = parsed_data


class FakeJob:
    def __init__(self, raw_text):
        self.raw_text = raw_text


def _base_evaluation(**overrides) -> ExpertEvaluationSchema:
    base = dict(
        overall_match_percentage_justified=80.0,
        all_requirements_evaluation=[],
        certifications=[],
        required_technical_skills_met=0,
        required_technical_skills_total_logical=0,
        years_required_by_job=0.0,
        years_found_on_resume=0.0,
        experience_status="FRESHER_ELIGIBLE",
        education_gate="MET",
        detected_education="Bachelor's",
        analysis_explanation="Solid match.",
        actionable_recommendations=[],
    )
    base.update(overrides)
    return ExpertEvaluationSchema(**base)


@pytest.fixture
def engine():
    eng = MatchingEngine.__new__(MatchingEngine)
    eng.ai_service = MagicMock()
    return eng


@pytest.mark.asyncio
async def test_case_c_compound_requirement_upgraded_when_llm_misses_it(engine):
    """The reported bug: the LLM marks 'Microsoft Office Suite (...)' missing
    verbatim, but the resume clearly has Word/Excel/PowerPoint individually -
    the deterministic layer must upgrade this to a full match."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Microsoft Office Suite (Word, Excel, PowerPoint)",
                category="TOOL",
                priority="MANDATORY",
                is_required=True,
                status="MISSING_AND_REQUIRED",
                reasoning="Not explicitly mentioned as 'Microsoft Office Suite'.",
                atomic_components=["Word", "Excel", "PowerPoint"],
                logical_operator="AND",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)

    resume = FakeResume(
        raw_text="Proficient in Microsoft Word, Excel, and PowerPoint for reporting.",
        parsed_data={"skills": ["Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint"], "certifications": []},
    )
    job = FakeJob(raw_text="Proficiency in Microsoft Office Suite (Word, Excel, PowerPoint)")

    result = await engine.calculate_match_expert_llm(resume, job)

    assert result["missing_skills"] == []
    assert len(result["matched_skills"]) == 1
    assert result["matched_skills"][0]["match_status"] == "FULL_MATCH"
    assert result["sub_scores"]["skill_score"] > 90.0


@pytest.mark.asyncio
async def test_case_c_partial_compound_match_when_one_component_missing(engine):
    """Word + Excel present but PowerPoint isn't -> PARTIAL_MATCH, not a
    total miss, and the missing atom is reported precisely."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Microsoft Office Suite (Word, Excel, PowerPoint)",
                category="TOOL",
                priority="MANDATORY",
                is_required=True,
                status="MISSING_AND_REQUIRED",
                reasoning="Umbrella phrase not found verbatim.",
                atomic_components=["Word", "Excel", "PowerPoint"],
                logical_operator="AND",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)

    resume = FakeResume(
        raw_text="Daily use of Microsoft Word and Excel for client reporting.",
        parsed_data={"skills": ["Microsoft Word", "Microsoft Excel"], "certifications": []},
    )
    job = FakeJob(raw_text="Proficiency in Microsoft Office Suite (Word, Excel, PowerPoint)")

    result = await engine.calculate_match_expert_llm(resume, job)

    assert len(result["matched_skills"]) == 1
    item = result["matched_skills"][0]
    assert item["match_status"] == "PARTIAL_MATCH"
    assert "Microsoft PowerPoint" in item["reason"]


@pytest.mark.asyncio
async def test_case_j_certifications_are_scored_separately(engine):
    """A preferred certification must never end up counted as a missing
    technical skill, and shouldn't crater the score."""
    evaluation = _base_evaluation(
        certifications=[
            CertificationEvidenceSchema(
                name="Tableau Desktop Specialist",
                priority="PREFERRED",
                matched=False,
                reasoning="Not found in resume; listed under Certifications, not mandatory.",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)

    resume = FakeResume(raw_text="Experienced analyst.", parsed_data={"skills": [], "certifications": []})
    job = FakeJob(raw_text="Certifications: Tableau Desktop Specialist (preferred)")

    result = await engine.calculate_match_expert_llm(resume, job)

    assert len(result["certifications"]) == 1
    assert result["certifications"][0]["name"] == "Tableau Desktop Specialist"
    assert result["sub_scores"]["certification_score"] == 100.0  # no REQUIRED certs missing
    assert all(m["skill"] != "Tableau Desktop Specialist" for m in result["missing_skills"])


@pytest.mark.asyncio
async def test_case_i_informational_items_never_become_missing_gaps(engine):
    """Company-marketing noise tagged INFORMATIONAL must never appear as a
    missing requirement or affect scoring."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="AI Gigafactory / digital transformation",
                category="INFORMATIONAL",
                priority="INFORMATIONAL",
                is_required=False,
                status="MISSING_BUT_OPTIONAL",
                reasoning="Company marketing text, not a candidate requirement.",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)
    resume = FakeResume(raw_text="Some resume text.", parsed_data={"skills": [], "certifications": []})
    job = FakeJob(raw_text="... AI Gigafactory ... digital transformation ...")

    result = await engine.calculate_match_expert_llm(resume, job)

    assert result["missing_skills"] == []
    assert result["matched_skills"] == []


@pytest.mark.asyncio
async def test_case_h_preferred_skill_missing_does_not_crater_score(engine):
    """A missing PREFERRED skill should barely move the score, unlike a
    missing MANDATORY one."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Python", category="TECHNICAL", priority="MANDATORY",
                is_required=True, status="SATISFIED", reasoning="Found in resume.",
            ),
            SkillEvidenceSchema(
                skill_name="Tableau", category="TOOL", priority="PREFERRED",
                is_required=False, status="MISSING_BUT_OPTIONAL", reasoning="Not found; preferred only.",
            ),
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)
    resume = FakeResume(
        raw_text="Experienced Python developer.",
        parsed_data={"skills": ["Python"], "certifications": []},
    )
    job = FakeJob(raw_text="Required: Python. Preferred: Tableau.")

    result = await engine.calculate_match_expert_llm(resume, job)

    # Naive equal-weight average of 1-of-2 matched would be 50%; priority
    # weighting should keep it comfortably above that since Tableau is only
    # PREFERRED, not MANDATORY.
    assert result["sub_scores"]["skill_score"] > 65.0


@pytest.mark.asyncio
async def test_recommendations_are_filtered_for_already_matched_atoms(engine):
    """Spec item 16: never recommend adding a skill whose atoms are already matched."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Microsoft Office Suite (Word, Excel, PowerPoint)",
                category="TOOL",
                priority="MANDATORY",
                is_required=True,
                status="MISSING_AND_REQUIRED",
                reasoning="Umbrella phrase not found verbatim.",
                atomic_components=["Word", "Excel", "PowerPoint"],
                logical_operator="AND",
            )
        ],
        actionable_recommendations=[
            {"type": "add_skill", "content": "Add Microsoft Excel to your resume", "priority": 1},
            {"type": "add_skill", "content": "Add SQL to your resume", "priority": 2},
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)
    resume = FakeResume(
        raw_text="Proficient in Microsoft Word, Excel, and PowerPoint.",
        parsed_data={"skills": ["Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint"], "certifications": []},
    )
    job = FakeJob(raw_text="Proficiency in Microsoft Office Suite (Word, Excel, PowerPoint)")

    result = await engine.calculate_match_expert_llm(resume, job)

    rec_texts = [r["content"] for r in result["recommendations"]]
    assert not any("excel" in t.lower() for t in rec_texts)
    assert any("sql" in t.lower() for t in rec_texts)


@pytest.mark.asyncio
async def test_case_f_responsibility_semantic_match_boosts_a_missed_item(engine, monkeypatch):
    """Spec item 7 / test case F: paraphrased responsibility evidence should
    be caught by the semantic cross-check even if the LLM missed it."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Prepare reports and presentations",
                category="RESPONSIBILITY",
                priority="IMPORTANT",
                is_required=True,
                status="MISSING_AND_REQUIRED",
                reasoning="No exact mention of preparing reports/presentations.",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)

    resume_text = "Created analytical reports and presented insights to stakeholders."
    resume = FakeResume(raw_text=resume_text, parsed_data={"skills": [], "certifications": []})
    job = FakeJob(raw_text="Prepare reports and presentations for senior leadership.")

    def fake_best_semantic_match(query, candidates, ai_service):
        return "Created analytical reports and presented insights to stakeholders.", 0.82

    monkeypatch.setattr(
        "app.services.matching.semantic_match.best_semantic_match",
        fake_best_semantic_match,
    )

    result = await engine.calculate_match_expert_llm(resume, job)

    assert len(result["matched_skills"]) == 1
    assert result["matched_skills"][0]["match_status"] == "PARTIAL_MATCH"
    assert "presented insights" in result["matched_skills"][0]["matched_resume_evidence"][0]


@pytest.mark.asyncio
async def test_case_g_soft_skill_evidence_based_match(engine, monkeypatch):
    """Spec item 6 / test case G: soft skills need real evidence, and the
    semantic cross-check should find it even with different wording."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="Teamwork",
                category="SOFT",
                priority="IMPORTANT",
                is_required=True,
                status="MISSING_AND_REQUIRED",
                reasoning="No explicit mention of teamwork found.",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)

    resume_text = "Collaborated with a 5-member development team to ship the project."
    resume = FakeResume(raw_text=resume_text, parsed_data={"skills": [], "certifications": []})
    job = FakeJob(raw_text="Ability to work independently and as part of a team.")

    def fake_best_semantic_match(query, candidates, ai_service):
        return "Collaborated with a 5-member development team to ship the project.", 0.71

    monkeypatch.setattr(
        "app.services.matching.semantic_match.best_semantic_match",
        fake_best_semantic_match,
    )

    result = await engine.calculate_match_expert_llm(resume, job)

    assert len(result["matched_skills"]) == 1
    assert result["matched_skills"][0]["category"] == "SOFT"
    assert "Collaborated" in result["matched_skills"][0]["matched_resume_evidence"][0]


@pytest.mark.asyncio
async def test_semantic_boost_does_not_fire_below_threshold(engine, monkeypatch):
    """A weak/irrelevant sentence similarity must not fabricate a match."""
    evaluation = _base_evaluation(
        all_requirements_evaluation=[
            SkillEvidenceSchema(
                skill_name="People Leadership",
                category="SOFT",
                priority="PREFERRED",
                is_required=False,
                status="MISSING_BUT_OPTIONAL",
                reasoning="No evidence of people leadership found.",
            )
        ],
    )
    engine.ai_service.evaluate_candidate_expertly = AsyncMock(return_value=evaluation)
    resume = FakeResume(raw_text="Built a to-do list app in React.", parsed_data={"skills": [], "certifications": []})
    job = FakeJob(raw_text="People Leadership is a plus.")

    def fake_best_semantic_match(query, candidates, ai_service):
        return "Built a to-do list app in React.", 0.1

    monkeypatch.setattr(
        "app.services.matching.semantic_match.best_semantic_match",
        fake_best_semantic_match,
    )

    result = await engine.calculate_match_expert_llm(resume, job)

    assert len(result["missing_skills"]) == 1
    assert result["missing_skills"][0]["match_status"] == "NO_MATCH"
