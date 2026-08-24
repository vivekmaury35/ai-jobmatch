"""
Deterministic skill normalization, compound-requirement decomposition, and
requirement matching utilities.

This module is intentionally free of any LLM / network dependency so it can
be unit tested in isolation and used as a fast, reliable cross-check layer
on top of the LLM's own judgement (see app/services/matching.py). It exists
to fix a specific class of bugs where compound requirements such as
"Microsoft Office Suite (Word, Excel, PowerPoint)" were being treated as one
opaque, exact-match-only string instead of a set of atomic, aliasable
requirements.

Pipeline implemented here:
    requirement text -> decompose_requirement()   [compound parsing + AND/OR]
                      -> normalize_skill()/normalize_key()  [aliasing/canon.]
                      -> evaluate_requirement_match()       [exact/alias/fuzzy
                                                              matching against
                                                              resume evidence]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Tuple, Set

from rapidfuzz import fuzz

Operator = Literal["AND", "OR"]
MatchStatus = Literal["FULL_MATCH", "PARTIAL_MATCH", "WEAK_MATCH", "NO_MATCH"]

# ---------------------------------------------------------------------------
# Canonical alias map
# ---------------------------------------------------------------------------
# Keys MUST already be run through `_basic_clean()` before lookup (lowercase,
# punctuation stripped to spaces, collapsed whitespace).
ALIAS_MAP: dict[str, str] = {
    # Microsoft Office family
    "microsoft office": "Microsoft Office Suite",
    "ms office": "Microsoft Office Suite",
    "office suite": "Microsoft Office Suite",
    "office 365": "Microsoft Office Suite",
    "microsoft 365": "Microsoft Office Suite",
    "word": "Microsoft Word",
    "ms word": "Microsoft Word",
    "microsoft word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "ms excel": "Microsoft Excel",
    "microsoft excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "power point": "Microsoft PowerPoint",
    "ms powerpoint": "Microsoft PowerPoint",
    "microsoft powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "ms outlook": "Microsoft Outlook",
    "onenote": "Microsoft OneNote",
    "teams": "Microsoft Teams",
    "ms teams": "Microsoft Teams",
    "access": "Microsoft Access",
    "ms access": "Microsoft Access",
    # Web / dev language & framework aliases
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "react": "React",
    "reactjs": "React",
    "react js": "React",
    "next": "Next.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue js": "Vue.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgre sql": "PostgreSQL",
    "mysql": "MySQL",
    "my sql": "MySQL",
    "github": "GitHub",
    "git hub": "GitHub",
    "git": "Git",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "html5": "HTML",
    "html": "HTML",
    "css3": "CSS",
    "css": "CSS",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "sql": "SQL",
    "vscode": "VS Code",
    "vs code": "VS Code",
    "visual studio code": "VS Code",
}

# Words that must never be singularized / are already canonical short forms.
_KEEP_AS_IS = {"js", "ts", "css", "aws", "gcp", "iis", "ms", "os", "bi"}


def _basic_clean(text: str) -> str:
    """Lowercase, strip punctuation to spaces, collapse whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("c++", "cplusplus").replace("c#", "csharp").replace(".net", "dotnet")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _singularize(token: str) -> str:
    words = token.split(" ")
    out = []
    for w in words:
        if w in _KEEP_AS_IS or len(w) <= 3:
            out.append(w)
        elif w.endswith("ies"):
            out.append(w[:-3] + "y")
        elif w.endswith(("ses", "xes")):
            out.append(w[:-2])
        elif w.endswith("s") and not w.endswith("ss"):
            out.append(w[:-1])
        else:
            out.append(w)
    return " ".join(out)


def _smart_title(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    if raw.isupper() or raw.islower():
        return raw.title() if raw.islower() else raw
    return raw  # already mixed-case (e.g. "FastAPI", "PostgreSQL") - keep as authored


def normalize_skill(raw: str) -> str:
    """Return the canonical, human-displayable form of a skill/tool token."""
    cleaned = _basic_clean(raw)
    if not cleaned:
        return raw.strip()
    if cleaned in ALIAS_MAP:
        return ALIAS_MAP[cleaned]
    singular = _singularize(cleaned)
    if singular in ALIAS_MAP:
        return ALIAS_MAP[singular]
    return _smart_title(raw.strip())


def normalize_key(raw: str) -> str:
    """Return a machine-comparable canonical key, e.g. 'microsoft_excel'."""
    canonical = normalize_skill(raw)
    return _basic_clean(canonical).replace(" ", "_")


# ---------------------------------------------------------------------------
# Compound requirement decomposition
# ---------------------------------------------------------------------------
@dataclass
class RequirementGroup:
    original: str
    parent_label: Optional[str]
    atoms: List[str]
    operator: Operator


def decompose_requirement(text: str) -> RequirementGroup:
    """
    Parses a (possibly compound) requirement phrase into atomic requirements
    plus the logical relationship between them.

    Examples handled:
        "Microsoft Office Suite (Word, Excel, PowerPoint)" -> AND [Word, Excel, PowerPoint]
        "HTML, CSS, and JavaScript"                        -> AND [HTML, CSS, JavaScript]
        "MySQL/PostgreSQL"                                 -> OR  [MySQL, PostgreSQL]
        "Django / Flask / FastAPI"                         -> OR  [Django, Flask, FastAPI]
        "Git/GitHub"                                       -> OR  [Git, GitHub]
        "Node.js or Laravel/PHP"                           -> OR  [Node.js, Laravel, PHP]
    """
    original = text.strip()
    if not original:
        return RequirementGroup(original=original, parent_label=None, atoms=[], operator="AND")

    parent_label: Optional[str] = None
    body = original

    paren_match = re.search(r"\(([^)]+)\)", original)
    if paren_match:
        prefix = original[: paren_match.start()].strip(" :-\u2013")
        if prefix:
            parent_label = prefix
        body = paren_match.group(1)

    lower_body = body.lower()
    atoms: List[str]
    operator: Operator

    if re.search(r"\bor\b", lower_body):
        operator = "OR"
        raw_parts = re.split(r"\bor\b", body, flags=re.IGNORECASE)
        atoms = []
        for part in raw_parts:
            part = part.strip()
            if "/" in part:
                atoms.extend(a.strip() for a in part.split("/") if a.strip())
            elif "," in part:
                atoms.extend(a.strip() for a in part.split(",") if a.strip())
            elif part:
                atoms.append(part)
    elif "/" in body and not re.search(r",|\band\b", lower_body):
        operator = "OR"
        atoms = [a.strip() for a in body.split("/") if a.strip()]
    elif "," in body or re.search(r"\band\b", lower_body):
        operator = "AND"
        cleaned_body = re.sub(r"\band\b", ",", body, flags=re.IGNORECASE)
        atoms = [a.strip() for a in cleaned_body.split(",") if a.strip()]
    else:
        operator = "AND"
        atoms = [body.strip()] if body.strip() else [original]

    atoms = [a for a in (a.strip(" .;") for a in atoms) if a]
    if not atoms:
        atoms = [original]

    return RequirementGroup(original=original, parent_label=parent_label, atoms=atoms, operator=operator)


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
@dataclass
class RequirementMatchResult:
    requirement: str
    normalized_requirement: List[str]
    match_status: MatchStatus
    match_score: float
    matched_resume_evidence: List[str]
    missing: List[str]
    reason: str
    logical_operator: Operator
    parent_label: Optional[str]


def _find_in_resume(atom: str, resume_text_clean: str, resume_skill_keys: Set[str]) -> Tuple[bool, Optional[str]]:
    canonical = normalize_skill(atom)
    key = normalize_key(atom)

    # Tier A/B: exact or alias match against the resume's own extracted skill list
    if key in resume_skill_keys:
        return True, canonical

    # Tier C: substring match against the full resume text (catches skills
    # mentioned in prose/bullets that weren't captured in a flat skill list)
    atom_clean = _basic_clean(canonical)
    if atom_clean and f" {atom_clean} " in f" {resume_text_clean} ":
        return True, canonical
    raw_clean = _basic_clean(atom)
    if raw_clean and raw_clean != atom_clean and f" {raw_clean} " in f" {resume_text_clean} ":
        return True, canonical

    # Tier D: fuzzy match against resume skill list (typos / minor variations)
    if resume_skill_keys:
        best_key, best_score = None, 0.0
        for candidate in resume_skill_keys:
            score = fuzz.token_set_ratio(key, candidate)
            if score > best_score:
                best_key, best_score = candidate, score
        if best_score >= 88:
            return True, canonical

    return False, None


def evaluate_requirement_match(
    requirement_text: str,
    resume_text: str,
    resume_skills: List[str],
) -> RequirementMatchResult:
    """
    Deterministically evaluates a single (possibly compound) job requirement
    against resume evidence, returning a fully explainable result. Supports
    FULL_MATCH / PARTIAL_MATCH / WEAK_MATCH / NO_MATCH.
    """
    group = decompose_requirement(requirement_text)
    resume_text_clean = _basic_clean(resume_text or "")
    resume_skill_keys = {normalize_key(s) for s in (resume_skills or []) if s and s.strip()}

    matched: List[str] = []
    missing: List[str] = []
    for atom in group.atoms:
        found, canonical = _find_in_resume(atom, resume_text_clean, resume_skill_keys)
        if found:
            matched.append(canonical or normalize_skill(atom))
        else:
            missing.append(normalize_skill(atom))

    total = len(group.atoms) or 1
    ratio = len(matched) / total
    status: MatchStatus
    score: float

    if group.operator == "OR":
        if matched:
            status, score = "FULL_MATCH", 100.0
            missing = []  # OR requirement is satisfied; unused alternatives aren't "missing"
        else:
            status, score = "NO_MATCH", 0.0
    else:  # AND
        if ratio >= 0.999:
            status, score = "FULL_MATCH", 100.0
        elif ratio >= 0.5:
            status, score = "PARTIAL_MATCH", round(ratio * 100, 1)
        elif ratio > 0:
            status, score = "WEAK_MATCH", round(ratio * 100, 1)
        else:
            status, score = "NO_MATCH", 0.0

    label = group.parent_label or requirement_text
    if status == "FULL_MATCH":
        if len(group.atoms) > 1:
            reason = f"All components of '{label}' were found in the resume ({', '.join(matched)})."
        else:
            reason = f"'{label}' was found in the resume."
    elif status in ("PARTIAL_MATCH", "WEAK_MATCH"):
        reason = (
            f"{len(matched)} of {total} components of '{label}' were found "
            f"({', '.join(matched)}); missing: {', '.join(missing)}."
        )
    else:
        if group.operator == "OR":
            reason = f"None of the alternatives for '{label}' ({', '.join(group.atoms)}) were found in the resume."
        else:
            reason = f"'{label}' was not found in the resume."

    return RequirementMatchResult(
        requirement=requirement_text,
        normalized_requirement=[normalize_key(a) for a in group.atoms],
        match_status=status,
        match_score=score,
        matched_resume_evidence=matched,
        missing=missing,
        reason=reason,
        logical_operator=group.operator,
        parent_label=group.parent_label,
    )


# ---------------------------------------------------------------------------
# Education / eligibility field mapping (item 11)
# ---------------------------------------------------------------------------
DEGREE_FIELD_MAP: dict[str, str] = {
    "bca": "computer science",
    "bachelor of computer applications": "computer science",
    "b sc computer science": "computer science",
    "bsc computer science": "computer science",
    "mca": "computer science",
    "master of computer applications": "computer science",
    "b tech": "engineering",
    "btech": "engineering",
    "be": "engineering",
    "b e": "engineering",
    "m tech": "engineering",
    "mtech": "engineering",
    "bba": "business",
    "mba": "business",
    "bachelor of business administration": "business",
    "master of business administration": "business",
    "b com": "finance",
    "bcom": "finance",
    "m com": "finance",
    "mcom": "finance",
    "bachelor of commerce": "finance",
}


def infer_degree_field(degree_text: str) -> Optional[str]:
    """Maps a raw degree string (e.g. 'Bachelor of Computer Applications')
    to a broad canonical field (e.g. 'computer science')."""
    cleaned = _basic_clean(degree_text)
    if not cleaned:
        return None
    for key, field_name in DEGREE_FIELD_MAP.items():
        key_clean = _basic_clean(key)
        if key_clean and (key_clean in cleaned or cleaned in key_clean):
            return field_name
    return None


def degree_matches_any(degree_text: str, allowed_fields: List[str]) -> bool:
    """True if `degree_text`'s inferred field overlaps any of `allowed_fields`."""
    inferred = infer_degree_field(degree_text)
    if not inferred:
        return False
    allowed_clean = [_basic_clean(f) for f in allowed_fields]
    return any(inferred in a or a in inferred for a in allowed_clean if a)
