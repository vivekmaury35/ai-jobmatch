"""
Automated test cases for the deterministic normalization / decomposition /
matching layer (app/services/skill_normalization.py).

Covers spec items 1-4, 9-11, and the automated test cases A-E from the
matching-pipeline audit:
    A. Exact Match
    B. Alias Match
    C. Compound Match
    D. OR Match
    E. Partial Match
"""
import pytest

from app.services.skill_normalization import (
    normalize_skill,
    normalize_key,
    decompose_requirement,
    evaluate_requirement_match,
    infer_degree_field,
    degree_matches_any,
)


# ---------------------------------------------------------------------------
# Normalization / aliasing (item 2)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected_canonical",
    [
        ("MS Excel", "Microsoft Excel"),
        ("Excel", "Microsoft Excel"),
        ("Node", "Node.js"),
        ("React JS", "React"),
        ("Next JS", "Next.js"),
        ("REST API", "REST APIs"),
        ("Postgres", "PostgreSQL"),
        ("JS", "JavaScript"),
        ("TS", "TypeScript"),
        ("Word", "Microsoft Word"),
        ("PowerPoint", "Microsoft PowerPoint"),
    ],
)
def test_alias_normalization(raw, expected_canonical):
    assert normalize_skill(raw) == expected_canonical


def test_normalize_key_is_comparable_regardless_of_casing_or_punctuation():
    assert normalize_key("Microsoft Excel") == normalize_key("MS Excel") == normalize_key("excel")


# ---------------------------------------------------------------------------
# Compound decomposition (item 1, 4)
# ---------------------------------------------------------------------------
def test_decompose_microsoft_office_suite_with_parentheses():
    group = decompose_requirement("Microsoft Office Suite (Word, Excel, PowerPoint)")
    assert group.operator == "AND"
    assert group.parent_label == "Microsoft Office Suite"
    assert [normalize_skill(a) for a in group.atoms] == [
        "Microsoft Word",
        "Microsoft Excel",
        "Microsoft PowerPoint",
    ]


def test_decompose_and_list_with_oxford_and():
    group = decompose_requirement("HTML, CSS, and JavaScript")
    assert group.operator == "AND"
    assert [normalize_skill(a) for a in group.atoms] == ["HTML", "CSS", "JavaScript"]


@pytest.mark.parametrize(
    "text,expected_atoms",
    [
        ("MySQL/PostgreSQL", ["MySQL", "PostgreSQL"]),
        ("Django / Flask / FastAPI", ["Django", "Flask", "FastAPI"]),
        ("Git/GitHub", ["Git", "GitHub"]),
    ],
)
def test_decompose_slash_alternatives_are_or(text, expected_atoms):
    group = decompose_requirement(text)
    assert group.operator == "OR"
    assert group.atoms == expected_atoms


def test_decompose_mixed_or_and_slash_flattens_alternatives():
    group = decompose_requirement("Node.js or Laravel/PHP")
    assert group.operator == "OR"
    assert group.atoms == ["Node.js", "Laravel", "PHP"]


# ---------------------------------------------------------------------------
# End-to-end requirement matching (items 3, 9, 10 + test cases A-E)
# ---------------------------------------------------------------------------
def test_case_a_exact_match():
    result = evaluate_requirement_match("Python", "Experienced in Python development.", ["Python"])
    assert result.match_status == "FULL_MATCH"
    assert result.match_score == 100.0


def test_case_b_alias_match():
    result = evaluate_requirement_match("JavaScript", "Built UIs using JS extensively.", ["JS"])
    assert result.match_status == "FULL_MATCH"
    assert "JavaScript" in result.matched_resume_evidence


def test_case_c_compound_match_full():
    resume_text = "Proficient in Microsoft Word, Excel, and PowerPoint for reporting."
    result = evaluate_requirement_match(
        "Microsoft Office Suite (Word, Excel, PowerPoint)",
        resume_text,
        ["Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint"],
    )
    assert result.match_status == "FULL_MATCH"
    assert result.match_score == 100.0
    assert set(result.matched_resume_evidence) == {
        "Microsoft Word",
        "Microsoft Excel",
        "Microsoft PowerPoint",
    }
    assert result.missing == []


def test_case_d_or_match():
    result = evaluate_requirement_match("MySQL or PostgreSQL", "Used PostgreSQL for the backend.", ["PostgreSQL"])
    assert result.match_status == "FULL_MATCH"
    assert result.matched_resume_evidence == ["PostgreSQL"]


def test_case_e_partial_match():
    resume_text = "Skilled in HTML and CSS."
    result = evaluate_requirement_match("HTML, CSS, JavaScript", resume_text, ["HTML", "CSS"])
    assert result.match_status == "PARTIAL_MATCH"
    assert result.match_score == pytest.approx(66.7, abs=0.5)
    assert set(result.matched_resume_evidence) == {"HTML", "CSS"}
    assert result.missing == ["JavaScript"]


def test_no_match_when_nothing_present():
    result = evaluate_requirement_match("Ruby on Rails", "Experience with Python and Django.", ["Python", "Django"])
    assert result.match_status == "NO_MATCH"
    assert result.match_score == 0.0


def test_compound_partial_match_two_of_three_found():
    """Microsoft Office Suite: resume has Word + Excel but not PowerPoint -> ~67%, not NO_MATCH."""
    resume_text = "Daily use of Microsoft Word and Excel for client reporting."
    result = evaluate_requirement_match(
        "Microsoft Office Suite (Word, Excel, PowerPoint)",
        resume_text,
        ["Microsoft Word", "Microsoft Excel"],
    )
    assert result.match_status == "PARTIAL_MATCH"
    assert result.match_score == pytest.approx(66.7, abs=0.5)
    assert set(result.matched_resume_evidence) == {"Microsoft Word", "Microsoft Excel"}
    assert result.missing == ["Microsoft PowerPoint"]


def test_matching_falls_back_to_full_resume_text_when_skill_list_incomplete():
    """Even if the structured resume skill list is empty, substring evidence
    in the raw resume text should still be found (Tier C)."""
    result = evaluate_requirement_match(
        "Microsoft Excel",
        "Managed budgets using Microsoft Excel spreadsheets daily.",
        [],
    )
    assert result.match_status == "FULL_MATCH"


# ---------------------------------------------------------------------------
# Degree / eligibility field mapping (item 11)
# ---------------------------------------------------------------------------
def test_degree_field_mapping_bca_to_computer_science():
    assert infer_degree_field("Bachelor of Computer Applications") == "computer science"


def test_degree_matches_any_allowed_field():
    allowed = ["business", "finance", "computer science", "engineering", "related field"]
    assert degree_matches_any("Bachelor of Computer Applications", allowed) is True


def test_degree_does_not_match_unrelated_field():
    assert degree_matches_any("Bachelor of Fine Arts", ["business", "finance", "engineering"]) is False
