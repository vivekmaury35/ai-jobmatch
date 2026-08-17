from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.scoring_config import SCORING_WEIGHTS, SKILL_TIER_SCORES, SEMANTIC_SIMILARITY_THRESHOLD
from app.services.ai import AIService
from app.models.resume import Resume
from app.models.job import Job

class MatchingEngine:
    def __init__(self):
        self.ai_service = AIService()

    def _compute_semantic_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Embeds the resume text and the job description using local sentence-transformers,
        then calculates their cosine similarity (0 to 1 scaling mapping).
        """
        if not resume_text or not job_text:
            return 0.0

        resume_emb = self.ai_service.embed(resume_text).reshape(1, -1)
        job_emb = self.ai_service.embed(job_text).reshape(1, -1)

        # Output is guaranteed to be conceptually [-1, 1], map roughly to [0, 100] percentages
        sim = cosine_similarity(resume_emb, job_emb)[0][0]
        return max(0.0, float(sim) * 100.0)

    def _evaluate_skills(self, resume: Resume, job: Job) -> Tuple[float, List[Dict], List[Dict], List[Dict]]:
        """
        Maps all required and preferred skills on the JD to exactly what the resume has.
        Identifies: Match/Missing/Related. Output Score is 0 - 100.
        """
        job_skills = {js.raw_text: js for js in job.skills}
        resume_skills = resume.skills

        # Fast lookup mapping for taxonomy exact overlap
        resume_skill_ids = {rs.skill_id for rs in resume_skills if rs.skill_id}
        resume_skill_raws = {rs.raw_text.lower() for rs in resume_skills}

        matched = []
        missing = []
        related = []

        total_weight = 0.0
        earned_score = 0.0

        # We must dynamically batch embed missing job strings and unused resume strings for semantic similarity check
        # Guard: skill_id=None must NOT be considered a taxonomy match (None == None is True in Python)
        unmatched_resume_raws = []
        for rs in resume_skills:
             if rs.skill_id is not None and any(js.skill_id == rs.skill_id for js in job.skills):
                  pass # Will be tracked down below
             else:
                  unmatched_resume_raws.append(rs.raw_text)

        unmatched_resume_embs = self.ai_service.embed_batch(unmatched_resume_raws) if unmatched_resume_raws else np.array([])

        for js_raw, js in job_skills.items():
            weight = js.importance if js.required else (js.importance * 0.5)
            total_weight += weight

            # Exact or Alias/Fuzzy database taxonomy overlaps
            if js.skill_id and js.skill_id in resume_skill_ids:
                # Find matching resume skill
                matching_rs = next(rs for rs in resume_skills if rs.skill_id == js.skill_id)
                # Determine tier
                if js.raw_text.lower() == matching_rs.raw_text.lower():
                    tier = "exact"
                else:
                     # If the raw texts differ but map to the same id, we consider it an alias or fuzzy
                     tier = "alias"

                matched.append({
                    "skill": js.raw_text,
                    "tier": tier,
                    "matched_as": matching_rs.raw_text,
                    "evidence": [matching_rs.evidence_source]
                })
                earned_score += (SKILL_TIER_SCORES[tier] * weight)

            elif js.raw_text.lower() in resume_skill_raws:
                 # It's an exact raw text match even if it wasn't in taxonomy
                 tier = "exact"
                 matching_rs = next(rs for rs in resume_skills if rs.raw_text.lower() == js.raw_text.lower())
                 matched.append({
                    "skill": js.raw_text,
                    "tier": tier,
                    "matched_as": matching_rs.raw_text,
                    "evidence": [matching_rs.evidence_source]
                })
                 earned_score += (SKILL_TIER_SCORES[tier] * weight)

            else:
                 # Check semantic similarity fallbacks
                 found_semantic_match = False
                 if unmatched_resume_embs.size > 0:
                     js_emb = self.ai_service.embed(js.raw_text).reshape(1, -1)
                     similarities = cosine_similarity(js_emb, unmatched_resume_embs)[0]
                     best_idx = np.argmax(similarities)
                     best_score = similarities[best_idx]

                     if best_score > SEMANTIC_SIMILARITY_THRESHOLD:
                         found_semantic_match = True
                         tier = "related"
                         related_raw = unmatched_resume_raws[best_idx]

                         related.append({
                             "skill": js.raw_text,
                             "related_to": related_raw,
                             "similarity": round(float(best_score), 2)
                         })
                         earned_score += (SKILL_TIER_SCORES[tier] * weight)

                 if not found_semantic_match:
                     missing.append({
                         "skill": js.raw_text,
                         "required": js.required
                     })

        final_skill_score = (earned_score / total_weight) * 100.0 if total_weight > 0 else 0.0

        return final_skill_score, matched, missing, related

    def _evaluate_experience(self, resume_data: dict, job_data: dict) -> float:
        req_years = job_data.get("experience_years_required") or 0
        if req_years == 0:
            return 100.0

        # Very simple duration extraction heuristic
        # A true production system would use an LLM or date parsing
        calc_years = len(resume_data.get("experience", [])) * 1.5

        if calc_years >= req_years:
            return 100.0

        return (calc_years / float(req_years)) * 100.0

    def _evaluate_education(self, resume_data: dict, job_data: dict) -> float:
        # Simplistic stub for purely deterministic scoring matrix
        req_edu = job_data.get("education_requirement")
        if not req_edu:
            return 100.0

        has_edu = len(resume_data.get("education", [])) > 0
        return 100.0 if has_edu else 0.0

    def _evaluate_projects(self, resume_data: dict) -> float:
         has_projects = len(resume_data.get("projects", [])) > 0
         return 100.0 if has_projects else 50.0

    def calculate_match(self, resume: Resume, job: Job) -> Dict[str, Any]:
        """
        Executes the overall deterministic scoring function mapping against weighted rules.
        """
        # 1. Semantic Overview
        sem_score = self._compute_semantic_similarity(resume.raw_text, job.raw_text)

        # 2. Strict Object Evaluations
        res_dict = resume.parsed_data or {}
        job_dict = job.parsed_data or {}

        exp_score = self._evaluate_experience(res_dict, job_dict)
        edu_score = self._evaluate_education(res_dict, job_dict)
        proj_score = self._evaluate_projects(res_dict)

        # 3. Dynamic Skill Tiers
        skill_score, matched, missing, related = self._evaluate_skills(resume, job)

        # Compute Absolute Total Matrix
        overall = sum([
            skill_score * (SCORING_WEIGHTS["skill_match"] / 100.0),
            sem_score * (SCORING_WEIGHTS["semantic_similarity"] / 100.0),
            exp_score * (SCORING_WEIGHTS["experience_match"] / 100.0),
            edu_score * (SCORING_WEIGHTS["education_match"] / 100.0),
            proj_score * (SCORING_WEIGHTS["project_evidence"] / 100.0)
        ])

        return {
             "overall_score": round(overall, 2),
             "sub_scores": {
                 "skill_score": round(skill_score, 2),
                 "semantic_score": round(sem_score, 2),
                 "experience_score": round(exp_score, 2),
                 "education_score": round(edu_score, 2),
                 "project_evidence_score": round(proj_score, 2)
             },
             "matched_skills": matched,
             "missing_skills": missing,
             "related_skills": related
        }
