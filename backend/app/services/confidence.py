from typing import Dict, Any, Tuple

class ConfidenceService:
    """
    Handles calculation of the Confidence Tier (Option B+).
    This replaces the overall percentage as the primary decision metric,
    providing actionable guidance based on specific gaps.
    """

    @classmethod
    def calculate_tier(cls,
                       missing_required_count: int,
                       experience_gap_years: float,
                       education_gate: str) -> Tuple[str, str, str]:
        """
        Determine confidence tier based on real-world hiring gates.
        Returns: (tier_id, tier_label, tier_advice)
        """

        # If required education is missing, that's a hard block for many roles
        if education_gate == "required_missing":
            # Demote tier by one level minimum
            missing_required_count += 2

        if missing_required_count == 0 and experience_gap_years <= 0:
            tier = "strong_match"
            label = "STRONG MATCH"
            advice = "Apply with confidence. Your profile strongly matches this role's requirements."

        elif missing_required_count <= 1 and experience_gap_years <= 0.5:
            tier = "strong_match"
            label = "STRONG MATCH"
            advice = "Apply with confidence. You meet almost all core requirements."

        elif missing_required_count <= 3 and experience_gap_years <= 1.0:
            tier = "viable_with_gaps"
            label = "VIABLE WITH GAPS"
            advice = "Apply, but proactively address your skill gaps in your cover letter or interview prep."

        elif missing_required_count <= 5 or experience_gap_years <= 2.0:
            tier = "stretch_application"
            label = "STRETCH APPLICATION"
            advice = "Consider applying if you're a fast learner. Highlight highly transferable skills."

        else:
            tier = "build_skills_first"
            label = "BUILD SKILLS FIRST"
            advice = "Focus on building the missing required skills before applying. See recommendations below."

        return tier, label, advice
