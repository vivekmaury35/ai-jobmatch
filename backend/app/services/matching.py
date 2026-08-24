from typing import List, Dict, Any, Optional
from app.services.ai import AIService
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.analysis import ExpertEvaluationSchema
from app.services.confidence import ConfidenceService
from app.services import skill_normalization as norm
from app.services import semantic_match
from app.core.scoring_config import (
    CATEGORY_WEIGHTS,
    OVERALL_SCORE_MAX_DEVIATION,
    PRIORITY_WEIGHTS,
    SEMANTIC_MATCH_THRESHOLD,
)

# Categories whose scoring bucket is "technical_skills" (general tools included).
_TECHNICAL_CATEGORIES = {"TECHNICAL", "TOOL"}
_LOCATION_CATEGORIES = {"LOCATION", "WORK_ARRANGEMENT"}
# Categories where a missing verdict is worth a second, code-level semantic look.
_SEMANTIC_BOOST_CATEGORIES = {"RESPONSIBILITY", "SOFT"}
_MISSING_STATUSES = {"MISSING_BUT_OPTIONAL", "MISSING_AND_REQUIRED"}


def _status_to_match_status(status: str) -> str:
    return {
        "SATISFIED": "FULL_MATCH",
        "PARTIALLY_SATISFIED": "PARTIAL_MATCH",
        "MISSING_BUT_OPTIONAL": "NO_MATCH",
        "MISSING_AND_REQUIRED": "NO_MATCH",
    }.get(status, "NO_MATCH")


def _status_to_score(status: str) -> float:
    return {
        "SATISFIED": 100.0,
        "PARTIALLY_SATISFIED": 60.0,
        "MISSING_BUT_OPTIONAL": 0.0,
        "MISSING_AND_REQUIRED": 0.0,
    }.get(status, 0.0)


class MatchingEngine:
    def __init__(self):
        self.ai_service = AIService()

    def calculate_match(self, resume: Resume, job: Job) -> Dict[str, Any]:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(lambda: asyncio.run(self.calculate_match_expert_llm(resume, job))).result()
        except RuntimeError:
            pass
        return asyncio.run(self.calculate_match_expert_llm(resume, job))

    async def calculate_match_expert_llm(self, resume: Resume, job: Job, debug: bool = False) -> Dict[str, Any]:
        """
        Executes the LLM evaluation against the raw documents, then
        deterministically re-verifies TECHNICAL/TOOL requirements (compound
        decomposition + alias/fuzzy matching against actual resume evidence)
        and cross-checks RESPONSIBILITY/SOFT misses against sentence-level
        semantic similarity, so the parts of the score that can be objectively
        verified in code never rest solely on the LLM's self-reported verdict.
        """
        evaluation: ExpertEvaluationSchema = await self.ai_service.evaluate_candidate_expertly(
            resume_text=resume.raw_text,
            job_text=job.raw_text
        )

        resume_parsed = resume.parsed_data or {}
        resume_skill_list: List[str] = list(resume_parsed.get("skills") or [])
        resume_cert_list: List[str] = list(resume_parsed.get("certifications") or [])
        resume_sentences = semantic_match.split_into_sentences(resume.raw_text)

        missing_required_count = 0
        matched: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        debug_requirements: List[Dict[str, Any]] = []

        for req in evaluation.all_requirements_evaluation:
            category_tag = req.category

            # INFORMATIONAL items (stipend, duration, company description,
            # marketing/culture copy, etc.) are job metadata, never candidate gaps.
            if category_tag == "INFORMATIONAL":
                continue

            # Defensive: a certification that slipped past the prompt's
            # instructions gets dropped here rather than scored as a tech gap
            # (it should have come through evaluation.certifications instead).
            if category_tag == "CERTIFICATION":
                continue

            priority = getattr(req, "priority", "IMPORTANT") or "IMPORTANT"
            llm_status = req.status
            deterministic: Optional[norm.RequirementMatchResult] = None

            item_data: Dict[str, Any] = {
                "skill": req.skill_name,
                "category": category_tag,
                "priority": priority,
                "required": req.is_required,
                "reasoning": req.reasoning,
                "evidence_snippet": req.evidence_snippet,
                "source_section": req.source_section,
                "proficiency_level": req.proficiency_level,
            }

            if category_tag in _TECHNICAL_CATEGORIES:
                # --- Deterministic re-verification (spec items 1-4, 9, 10) ---
                requirement_text = req.skill_name
                if req.atomic_components:
                    joiner = " or " if req.logical_operator == "OR" else ", "
                    requirement_text = joiner.join(req.atomic_components)

                deterministic = norm.evaluate_requirement_match(
                    requirement_text, resume.raw_text, resume_skill_list
                )
                item_data["normalized_requirement"] = deterministic.normalized_requirement
                item_data["logical_operator"] = deterministic.logical_operator
                item_data["match_status"] = deterministic.match_status
                item_data["match_score"] = deterministic.match_score
                item_data["matched_resume_evidence"] = (
                    deterministic.matched_resume_evidence or req.matched_resume_evidence or []
                )
                item_data["reason"] = deterministic.reason

                # Only ever BOOST the LLM's verdict when our deterministic
                # check finds real evidence the LLM missed - never downgrade a
                # SATISFIED verdict, since the LLM can see semantic context
                # (e.g. a project paragraph) that a flat skill list can't.
                if deterministic.match_status in ("FULL_MATCH", "PARTIAL_MATCH", "WEAK_MATCH") and llm_status in _MISSING_STATUSES:
                    llm_status = "SATISFIED" if deterministic.match_status == "FULL_MATCH" else "PARTIALLY_SATISFIED"
                    item_data["reasoning"] = deterministic.reason
            else:
                item_data["match_status"] = _status_to_match_status(llm_status)
                item_data["match_score"] = _status_to_score(llm_status)
                item_data["matched_resume_evidence"] = req.matched_resume_evidence or (
                    [req.evidence_snippet] if req.evidence_snippet else []
                )
                item_data["reason"] = req.reasoning

                # --- Semantic cross-validation for RESPONSIBILITY / SOFT misses (item 6, 7) ---
                if category_tag in _SEMANTIC_BOOST_CATEGORIES and llm_status in _MISSING_STATUSES:
                    best_sentence, similarity = semantic_match.best_semantic_match(
                        req.skill_name, resume_sentences, self.ai_service
                    )
                    if best_sentence and similarity >= SEMANTIC_MATCH_THRESHOLD:
                        llm_status = "PARTIALLY_SATISFIED"
                        item_data["match_status"] = "PARTIAL_MATCH"
                        item_data["match_score"] = round(similarity * 100, 1)
                        item_data["matched_resume_evidence"] = [best_sentence]
                        item_data["reason"] = f"Semantic match ({similarity:.0%}) found in resume: \"{best_sentence}\""
                        item_data["reasoning"] = item_data["reason"]

            if debug:
                debug_requirements.append({
                    "requirement": req.skill_name,
                    "source_section": req.source_section,
                    "category": category_tag,
                    "priority": priority,
                    "atomic_components": req.atomic_components,
                    "logical_operator": req.logical_operator,
                    "llm_status": req.status,
                    "final_status": llm_status,
                    "deterministic_check": None if deterministic is None else {
                        "normalized_requirement": deterministic.normalized_requirement,
                        "match_status": deterministic.match_status,
                        "match_score": deterministic.match_score,
                        "matched_resume_evidence": deterministic.matched_resume_evidence,
                        "missing": deterministic.missing,
                    },
                    "evidence_snippet": req.evidence_snippet,
                })

            if llm_status in ("SATISFIED", "PARTIALLY_SATISFIED"):
                item_data["tier"] = "exact" if llm_status == "SATISFIED" else "related"
                if req.matched_as:
                    item_data["matched_as"] = req.matched_as
                matched.append(item_data)
            else:
                missing.append(item_data)
                if priority == "MANDATORY" and category_tag in _TECHNICAL_CATEGORIES:
                    missing_required_count += 1

        exp_gap = max(0.0, float(evaluation.years_required_by_job) - float(evaluation.years_found_on_resume))

        tier_id, tier_label, tier_advice = ConfidenceService.calculate_tier(
            missing_required_count=missing_required_count,
            experience_gap_years=exp_gap,
            education_gate=evaluation.education_gate.lower()
        )

        # ===================================================================
        # Priority-weighted category scoring (spec items 12, 13)
        # ===================================================================
        # A missed MANDATORY requirement hurts a category score far more than
        # a missed PREFERRED/OPTIONAL one - see PRIORITY_WEIGHTS.
        def _bucket_score(categories, llm_value):
            bucket_matched = [m for m in matched if m.get("category") in categories]
            bucket_missing = [m for m in missing if m.get("category") in categories]
            w_matched = sum(PRIORITY_WEIGHTS.get(m.get("priority", "IMPORTANT"), 0.8) for m in bucket_matched)
            w_missing = sum(PRIORITY_WEIGHTS.get(m.get("priority", "IMPORTANT"), 0.8) for m in bucket_missing)
            w_total = w_matched + w_missing
            calculated = round((w_matched / w_total) * 100.0, 2) if w_total > 0 else 100.0
            score = float(llm_value) if llm_value is not None else calculated
            return score, bucket_matched, bucket_missing

        tech_score, tech_items, tech_missing = _bucket_score(_TECHNICAL_CATEGORIES, evaluation.technical_skills_score)
        soft_score, soft_items, soft_missing = _bucket_score({"SOFT"}, evaluation.soft_skills_score)
        ai_score, ai_items, ai_missing = _bucket_score({"AI_TOOL"}, evaluation.ai_tools_score)
        resp_score, resp_items, resp_missing = _bucket_score({"RESPONSIBILITY"}, evaluation.responsibilities_score)
        loc_score, loc_items, loc_missing = _bucket_score(_LOCATION_CATEGORIES, evaluation.location_score)

        edu_score = float(evaluation.education_score) if evaluation.education_score is not None else (
            100.0 if evaluation.education_gate.lower() == "met" else 50.0
        )
        exp_score = float(evaluation.experience_score) if evaluation.experience_score is not None else (
            100.0 if evaluation.experience_status in ["MET", "FRESHER_ELIGIBLE"] else max(0.0, 100.0 - exp_gap * 20.0)
        )
        proj_score = float(evaluation.project_evidence_score) if evaluation.project_evidence_score is not None else 100.0

        # ===================================================================
        # Certifications - scored and reported entirely separately (spec item 8)
        # ===================================================================
        certifications: List[Dict[str, Any]] = []
        required_certs = [c for c in evaluation.certifications if c.priority == "REQUIRED"]
        for c in evaluation.certifications:
            certifications.append({
                "name": c.name,
                "priority": c.priority,
                "matched": c.matched,
                "matched_resume_evidence": c.matched_resume_evidence,
                "reasoning": c.reasoning,
            })

        if evaluation.certification_score is not None:
            cert_score = float(evaluation.certification_score)
        elif required_certs:
            cert_score = round(sum(1 for c in required_certs if c.matched) / len(required_certs) * 100.0, 2)
        else:
            cert_score = 100.0  # No mandatory certifications -> never penalize the candidate.

        # ===================================================================
        # Weighted overall score (spec item 12), validated against the LLM's own figure
        # ===================================================================
        llm_overall = max(0.0, min(100.0, float(evaluation.overall_match_percentage_justified)))

        weight_sum = sum(CATEGORY_WEIGHTS.values())
        computed_overall = (
            CATEGORY_WEIGHTS["technical_skills"] * tech_score +
            CATEGORY_WEIGHTS["soft_skills"] * soft_score +
            CATEGORY_WEIGHTS["ai_tools"] * ai_score +
            CATEGORY_WEIGHTS["responsibilities"] * resp_score +
            CATEGORY_WEIGHTS["experience"] * exp_score +
            CATEGORY_WEIGHTS["education"] * edu_score +
            CATEGORY_WEIGHTS["project_evidence"] * proj_score +
            CATEGORY_WEIGHTS["location"] * loc_score +
            CATEGORY_WEIGHTS["certifications"] * cert_score
        ) / weight_sum

        # Use the lower of (LLM overall, computed average) to prevent inflation
        if llm_overall > computed_overall + OVERALL_SCORE_MAX_DEVIATION:
            overall = round(computed_overall, 2)
        else:
            overall = round(llm_overall, 2)

        # ===================================================================
        # Evidence-aware recommendation filtering (spec item 16)
        # ===================================================================
        matched_names = {m["skill"].lower() for m in matched}
        matched_atoms = set()
        for m in matched:
            for evd in (m.get("matched_resume_evidence") or []):
                matched_atoms.add(str(evd).lower())
            for atom_key in (m.get("normalized_requirement") or []):
                matched_atoms.add(atom_key.replace("_", " "))

        filtered_recommendations = []
        for r in evaluation.actionable_recommendations:
            rec_content_lower = r.content.lower()
            already_satisfied = (
                any(name in rec_content_lower for name in matched_names if len(name) > 3) or
                any(atom in rec_content_lower for atom in matched_atoms if len(atom) > 3)
            )
            if already_satisfied and r.type in ["add_skill", "MISSING_SKILL"]:
                continue
            filtered_recommendations.append({"type": r.type, "content": r.content, "priority": r.priority})

        tech_total = len(tech_items) + len(tech_missing)

        result: Dict[str, Any] = {
             "overall_score": round(overall, 2),
             "sub_scores": {
                 "skill_score": round(tech_score, 2),
                 "experience_score": round(exp_score, 2),
                 "education_score": round(edu_score, 2),
                 "project_evidence_score": round(proj_score, 2),
                 "soft_skills_score": round(soft_score, 2),
                 "ai_tools_score": round(ai_score, 2),
                 "responsibilities_score": round(resp_score, 2),
                 "location_score": round(loc_score, 2),
                 "certification_score": round(cert_score, 2),
             },
             "matched_skills": matched,
             "missing_skills": missing,
             "related_skills": [],
             "certifications": certifications,
             "metrics": {
                 "req_total": evaluation.required_technical_skills_total_logical or tech_total,
                 "req_matched": evaluation.required_technical_skills_met or len(tech_items),
                 "pref_total": 0,
                 "pref_matched": 0,
                 "exp_cand": evaluation.years_found_on_resume,
                 "exp_req": evaluation.years_required_by_job,
                 "exp_gap": exp_gap,
                 "education_gate": evaluation.education_gate.lower(),
                 "education_req": evaluation.detected_education
             },
             "confidence": {
                 "tier": tier_id,
                 "label": tier_label,
                 "advice": tier_advice
             },
             "explanation": evaluation.analysis_explanation,
             "recommendations": filtered_recommendations
        }

        if debug:
            result["debug_info"] = {
                "resume_skills_extracted": resume_skill_list,
                "resume_certifications_extracted": resume_cert_list,
                "resume_sentences_considered": resume_sentences[:50],
                "requirements": debug_requirements,
                "category_scores": result["sub_scores"],
                "category_weights": CATEGORY_WEIGHTS,
                "priority_weights": PRIORITY_WEIGHTS,
                "llm_overall_score": llm_overall,
                "computed_overall_score": round(computed_overall, 2),
                "final_overall_score": result["overall_score"],
            }

        return result
