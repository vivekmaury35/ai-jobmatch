export interface Recommendation {
  type: string;
  content: string;
  priority: number;
}

export interface Skill {
  skill: string;
  tier?: string;
  evidence?: string[];
  matched_as?: string;
  required?: boolean;
  related_to?: string;
  similarity?: number;
}

export interface AnalyzeResponse {
  id: string;
  resume_id: string;
  job_id: string;
  overall_score: number;
  skill_score: number;
  semantic_score: number;
  experience_score: number;
  education_score: number;
  project_evidence_score: number;
  matched_skills: Skill[];
  missing_skills: Skill[];
  related_skills: Skill[];
  explanation: string | null;
  recommendations: Recommendation[];
  cached?: boolean;
  created_at: string;
}
