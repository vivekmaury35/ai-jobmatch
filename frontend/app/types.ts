export interface Recommendation {
  type: string;
  content: string;
  priority: number;
}

export interface Skill {
  skill: string;
  category?: 'TECHNICAL' | 'TOOL' | 'SOFT' | 'ROLE' | 'LOCATION' | 'WORK_ARRANGEMENT' | 'ELIGIBILITY' | 'EDUCATION_REQUIREMENT' | 'AI_TOOL' | 'RESPONSIBILITY' | 'LANGUAGE' | 'LANGUAGE_PROFICIENCY' | 'EMPLOYMENT_TYPE' | 'INFORMATIONAL';
  priority?: 'MANDATORY' | 'IMPORTANT' | 'PREFERRED' | 'OPTIONAL' | 'INFORMATIONAL';
  tier?: string;
  evidence?: string[];
  evidence_snippet?: string;
  source_section?: string;
  proficiency_level?: string;
  matched_as?: string;
  required?: boolean;
  related_to?: string;
  similarity?: number;
  reasoning?: string;
  normalized_requirement?: string[];
  logical_operator?: 'AND' | 'OR';
  match_status?: 'FULL_MATCH' | 'PARTIAL_MATCH' | 'WEAK_MATCH' | 'NO_MATCH';
  match_score?: number;
  matched_resume_evidence?: string[];
  reason?: string;
}

export interface Certification {
  name: string;
  priority: 'REQUIRED' | 'PREFERRED' | 'RECOMMENDED' | 'INFORMATIONAL';
  matched: boolean;
  matched_resume_evidence?: string | null;
  reasoning?: string;
}

export interface AnalyzeResponse {
  id: string;
  resume_id: string;
  job_id: string;
  job_title?: string;
  overall_score: number;

  confidence_tier?: string;
  tier_label?: string;
  tier_advice?: string;

  required_skills_matched?: number;
  required_skills_total?: number;
  preferred_skills_matched?: number;
  preferred_skills_total?: number;

  experience_years_candidate?: number;
  experience_years_required?: number;
  experience_gap_years?: number;

  education_gate?: string;
  education_requirement?: string;

  skill_score: number;
  experience_score: number;
  education_score: number;
  project_evidence_score: number;
  soft_skills_score?: number;
  ai_tools_score?: number;
  responsibilities_score?: number;
  location_score?: number;
  certification_score?: number;

  matched_skills: Skill[];
  missing_skills: Skill[];
  related_skills: Skill[];
  certifications?: Certification[];
  explanation: string | null;
  recommendations: Recommendation[];
  cached?: boolean;
  created_at: string;
  debug_info?: Record<string, unknown> | null;
}
