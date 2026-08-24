'use client';
import { use, useEffect, useState } from 'react';
import { SubScoreCard } from '../../components/ui/SubScoreCard';
import { Card } from '../../components/ui/Card';
import { AnalyzeResponse } from '../../types';
import { CheckCircle2, AlertCircle, TrendingUp, Target } from 'lucide-react';
import { getApiUrl } from '../../lib/utils';

export default function Results({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = getApiUrl();
    fetch(`${apiUrl}/analyze/${id}`)

      .then(res => {
         if (!res.ok) throw new Error("Load failed");
         return res.json();
      })
      .then((d: AnalyzeResponse) => setData(d))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error"));
  }, [id]);

  if (error) return <div className="text-red-500 font-semibold p-8">{error}</div>;
  if (!data) return <div className="text-zinc-500 p-8">Loading analysis...</div>;

  const displaySubScores = [
    { label: "Technical Skills", value: Math.round(data.skill_score) },
    { label: "Soft Skills", value: Math.round(data.soft_skills_score ?? data.overall_score) },
    { label: "AI Tools", value: Math.round(data.ai_tools_score ?? data.overall_score) },
    { label: "Responsibilities", value: Math.round(data.responsibilities_score ?? data.overall_score) },
    { label: "Experience", value: Math.round(data.experience_score) },
    { label: "Education", value: Math.round(data.education_score) },
    { label: "Projects", value: Math.round(data.project_evidence_score) },
    { label: "Location", value: Math.round(data.location_score ?? 100) }
  ];

  // Determine match tier
  const getMatchTier = (score: number) => {
    if (score >= 80) return { label: 'EXCELLENT', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
    if (score >= 60) return { label: 'GOOD', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' };
    if (score >= 40) return { label: 'FAIR', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' };
    return { label: 'NEEDS WORK', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' };
  };

  const tier = getMatchTier(data.overall_score);

  return (
    <main className="max-w-5xl mx-auto p-8 space-y-6">
      {/* Header with Match Tier Badge */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-extrabold text-white mb-2">Match Analysis</h1>
          <p className="text-zinc-400">Prescriptive career coaching based on your profile</p>
        </div>

        {data.confidence_tier ? (
            <div className={`
              ${data.confidence_tier === 'strong_match' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : ''}
              ${data.confidence_tier === 'viable_with_gaps' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400' : ''}
              ${data.confidence_tier === 'stretch_application' ? 'bg-orange-500/10 border-orange-500/30 text-orange-400' : ''}
              ${data.confidence_tier === 'build_skills_first' ? 'bg-red-500/10 border-red-500/30 text-red-400' : ''}
              border-2 px-6 py-4 rounded-xl flex flex-col items-center gap-1 min-w-[200px] text-center
            `}>
              <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Decision</span>
              <span className="text-xl font-bold tracking-tight">{data.tier_label}</span>
            </div>
        ) : (
             <div className={`${tier.bg} ${tier.border} border-2 px-6 py-4 rounded-xl flex flex-col items-center gap-1`}>
               <span className="text-xs uppercase font-bold text-zinc-500">Overall Match</span>
               <span className={`text-5xl font-black ${tier.color}`}>{Math.round(data.overall_score)}%</span>
               <span className={`text-xs uppercase font-bold ${tier.color} tracking-wider`}>{tier.label}</span>
             </div>
        )}
      </div>

      {data.confidence_tier && (
          <div className={`p-4 rounded-lg flex items-start gap-3 border
              ${data.confidence_tier === 'strong_match' ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-300' : ''}
              ${data.confidence_tier === 'viable_with_gaps' ? 'bg-yellow-950/30 border-yellow-900/50 text-yellow-300' : ''}
              ${data.confidence_tier === 'stretch_application' ? 'bg-orange-950/30 border-orange-900/50 text-orange-300' : ''}
              ${data.confidence_tier === 'build_skills_first' ? 'bg-red-950/30 border-red-900/50 text-red-300' : ''}
          `}>
             <AlertCircle size={20} className="shrink-0 mt-0.5" />
             <div>
                <p className="font-medium text-sm">{data.tier_advice}</p>
                <p className="text-xs opacity-70 mt-1">Based on required skills gaps and experience alignment.</p>
             </div>
          </div>
      )}

      {/* Sub-Score Breakdown */}
      <div>
        <h2 className="text-sm uppercase font-bold text-zinc-500 mb-3 flex items-center gap-2">
          <TrendingUp size={16} />
          Score Breakdown
        </h2>
        <SubScoreCard scores={displaySubScores} />
      </div>

      {/* FRACTION METRICS */}
      {data.confidence_tier && (
          <div className="grid md:grid-cols-3 gap-4">
              {/* Skill Fraction Card */}
              <Card className="bg-zinc-900 border-zinc-800 p-5">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Required Technical Skills Match</span>
                  <div className="flex items-end gap-2 mt-2">
                       <span className="text-3xl font-bold text-white">{data.required_skills_matched}</span>
                       <span className="text-zinc-500 font-medium mb-1">/ {data.required_skills_total}</span>
                  </div>
                  {data.preferred_skills_total! > 0 && (
                      <div className="mt-3 pt-3 border-t border-zinc-800 flex justify-between text-xs">
                          <span className="text-zinc-500">Preferred skills:</span>
                          <span className="text-zinc-400 font-medium">{data.preferred_skills_matched} / {data.preferred_skills_total}</span>
                      </div>
                  )}
              </Card>

              {/* Experience Card */}
              <Card className="bg-zinc-900 border-zinc-800 p-5">
                   <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Experience Level</span>
                   <div className="flex items-end gap-2 mt-2">
                        <span className="text-3xl font-bold text-white">{(data.experience_years_candidate ?? 0).toFixed(1)}</span>
                        <span className="text-zinc-500 font-medium mb-1">years</span>
                   </div>
                   <div className="mt-3 pt-3 border-t border-zinc-800 flex justify-between text-xs">
                       <span className="text-zinc-500">Requirement: {data.experience_years_required} years</span>
                       {data.experience_gap_years! > 0 ? (
                           <span className="text-red-400 font-medium">Gap: -{data.experience_gap_years}y</span>
                       ) : (
                           <span className="text-emerald-400 font-medium">Met ✓</span>
                       )}
                   </div>
              </Card>

              {/* Education Gate Card */}
              <Card className={`p-5 flex flex-col justify-between border
                  ${data.education_gate === 'met' ? 'bg-emerald-950/20 border-emerald-900/50' : ''}
                  ${data.education_gate === 'preferred_missing' ? 'bg-yellow-950/20 border-yellow-900/50' : ''}
                  ${data.education_gate === 'required_missing' ? 'bg-red-950/20 border-red-900/50' : ''}
              `}>
                  <div>
                      <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Education Requirement Gate</span>
                      <p className="text-white text-sm font-medium mt-2">{data.education_requirement || "No specific requirement"}</p>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                      {data.education_gate === 'met' && <><CheckCircle2 size={16} className="text-emerald-500"/><span className="text-xs text-emerald-400 font-bold">MET / NOT REQUIRED</span></>}
                      {data.education_gate === 'preferred_missing' && <><AlertCircle size={16} className="text-yellow-500"/><span className="text-xs text-yellow-400 font-bold">PREFERRED MISSING</span></>}
                      {data.education_gate === 'required_missing' && <><AlertCircle size={16} className="text-red-500"/><span className="text-xs text-red-400 font-bold">REQUIRED MISSING</span></>}
                  </div>
              </Card>
          </div>
      )}

      {/* ACTION DASHBOARD */}
      {data.recommendations && data.recommendations.length > 0 && (
        <Card className="bg-gradient-to-br from-indigo-950/40 to-purple-950/40 border-indigo-500/30 p-8">
          <div className="flex items-center gap-3 mb-6">
            <Target className="text-indigo-400" size={28} />
            <div>
              <h2 className="text-2xl font-bold text-white">Action Plan to Improve Your Match</h2>
              <p className="text-zinc-400 text-sm">Specific steps you can take today to boost your score</p>
            </div>
          </div>
          <div className="space-y-4">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="bg-zinc-900/80 border border-zinc-700 rounded-lg p-5 flex gap-4 hover:border-indigo-500/50 transition-all">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-sm">
                    {rec.priority || i + 1}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs uppercase font-bold text-indigo-400 tracking-wide">
                      {rec.type?.replace('_', ' ') || 'Action'}
                    </span>
                  </div>
                  <p className="text-zinc-200 leading-relaxed">{rec.content}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* AI Explanation */}
      {data.explanation && (
        <Card className="bg-zinc-900 border-zinc-800 p-6">
          <h2 className="text-sm uppercase font-bold text-zinc-500 mb-4 flex items-center gap-2">
            <AlertCircle size={16} />
            AI Analysis
          </h2>
          <p className="text-zinc-300 leading-relaxed">{data.explanation}</p>
        </Card>
      )}

      {/* Requirements Categorization Breakdown */}
      <h2 className="text-xl uppercase font-bold text-white mt-12 mb-6 border-b border-zinc-800 pb-2">Requirement Matches</h2>
      <div className="grid md:grid-cols-2 gap-6">

        {/* TECHNICAL SKILLS CARD */}
        <Card className="bg-zinc-950/50 border-zinc-800 p-6 flex flex-col gap-6">
          <h3 className="text-sm uppercase font-bold text-zinc-300 flex items-center justify-between">
            <span>💻 Technical Skills</span>
            <span className="text-xs text-emerald-400 font-bold">{Math.round(data.skill_score)}% Match</span>
          </h3>
          <div>
            <h4 className="text-xs font-bold text-emerald-400 mb-2">Matched</h4>
            <div className="flex flex-wrap gap-2">
                {data.matched_skills?.filter(s => s.category === 'TECHNICAL' || !s.category).length > 0 ? (
                  data.matched_skills.filter(s => s.category === 'TECHNICAL' || !s.category).map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-emerald-950 text-emerald-300 text-xs rounded-md border border-emerald-900" title={s.reasoning || ""}>{s.skill}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold text-red-400 mb-2">Missing</h4>
            <div className="flex flex-wrap gap-2">
                {data.missing_skills?.filter(s => s.category === 'TECHNICAL' || !s.category).length > 0 ? (
                  data.missing_skills.filter(s => s.category === 'TECHNICAL' || !s.category).map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-red-950 text-red-300 text-xs rounded-md border border-red-900" title={s.reasoning || ""}>{s.skill} {s.required && "*"}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
        </Card>

        {/* SOFT SKILLS CARD */}
        <Card className="bg-zinc-950/50 border-zinc-800 p-6 flex flex-col gap-6">
          <h3 className="text-sm uppercase font-bold text-zinc-300 flex items-center justify-between">
            <span>🤝 Soft Skills</span>
            <span className="text-xs text-emerald-400 font-bold">{Math.round(data.soft_skills_score ?? 100)}% Match</span>
          </h3>
          <div>
            <h4 className="text-xs font-bold text-emerald-400 mb-2">Matched Evidence</h4>
            <div className="flex flex-wrap gap-2">
                {data.matched_skills?.filter(s => s.category === 'SOFT').length > 0 ? (
                  data.matched_skills.filter(s => s.category === 'SOFT').map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-emerald-950 text-emerald-300 text-xs rounded-md border border-emerald-900" title={s.reasoning || ""}>{s.skill}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold text-red-400 mb-2">Missing Evidence</h4>
            <div className="flex flex-wrap gap-2">
                {data.missing_skills?.filter(s => s.category === 'SOFT').length > 0 ? (
                  data.missing_skills.filter(s => s.category === 'SOFT').map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-red-950 text-red-300 text-xs rounded-md border border-red-900" title={s.reasoning || ""}>{s.skill}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
        </Card>

        {/* AI TOOLS CARD */}
        {(data.matched_skills?.some(s => s.category === 'AI_TOOL') || data.missing_skills?.some(s => s.category === 'AI_TOOL')) && (
            <Card className="bg-zinc-950/50 border-zinc-800 p-6 flex flex-col gap-6">
              <h3 className="text-sm uppercase font-bold text-zinc-300 flex items-center justify-between">
                <span>🤖 AI Development Tools</span>
                <span className="text-xs text-emerald-400 font-bold">{Math.round(data.ai_tools_score ?? 100)}% Match</span>
              </h3>
              <div>
                <h4 className="text-xs font-bold text-emerald-400 mb-2">Matched</h4>
                <div className="flex flex-wrap gap-2">
                    {data.matched_skills?.filter(s => s.category === 'AI_TOOL').length > 0 ? (
                      data.matched_skills.filter(s => s.category === 'AI_TOOL').map((s, i) => (
                        <span key={i} className="px-3 py-1.5 bg-emerald-950 text-emerald-300 text-xs rounded-md border border-emerald-900" title={s.reasoning || ""}>{s.skill}</span>
                      ))
                    ) : <span className="text-zinc-600 italic text-xs">None</span>}
                </div>
              </div>
              <div>
                <h4 className="text-xs font-bold text-red-400 mb-2">Missing</h4>
                <div className="flex flex-wrap gap-2">
                    {data.missing_skills?.filter(s => s.category === 'AI_TOOL').length > 0 ? (
                      data.missing_skills.filter(s => s.category === 'AI_TOOL').map((s, i) => (
                        <span key={i} className="px-3 py-1.5 bg-red-950 text-red-300 text-xs rounded-md border border-red-900" title={s.reasoning || ""}>{s.skill}</span>
                      ))
                    ) : <span className="text-zinc-600 italic text-xs">None</span>}
                </div>
              </div>
            </Card>
        )}

        {/* ELIGIBILITY & LOCATION CARD */}
        <Card className="bg-zinc-950/50 border-zinc-800 p-6 flex flex-col gap-6">
          <h3 className="text-sm uppercase font-bold text-zinc-300 flex items-center justify-between">
            <span>✅ Eligibility & Location</span>
            <span className="text-xs text-emerald-400 font-bold">Matched</span>
          </h3>
          <div>
            <h4 className="text-xs font-bold text-emerald-400 mb-2">Matched Criteria</h4>
            <div className="flex flex-wrap gap-2">
                {data.matched_skills?.filter(s => s.category === 'ELIGIBILITY' || s.category === 'LOCATION' || s.category === 'WORK_ARRANGEMENT').length > 0 ? (
                  data.matched_skills.filter(s => s.category === 'ELIGIBILITY' || s.category === 'LOCATION' || s.category === 'WORK_ARRANGEMENT').map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-emerald-950 text-emerald-300 text-xs rounded-md border border-emerald-900" title={s.reasoning || ""}>{s.skill}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold text-red-400 mb-2">Unmatched Criteria</h4>
            <div className="flex flex-wrap gap-2">
                {data.missing_skills?.filter(s => s.category === 'ELIGIBILITY' || s.category === 'LOCATION' || s.category === 'WORK_ARRANGEMENT').length > 0 ? (
                  data.missing_skills.filter(s => s.category === 'ELIGIBILITY' || s.category === 'LOCATION' || s.category === 'WORK_ARRANGEMENT').map((s, i) => (
                    <span key={i} className="px-3 py-1.5 bg-red-950 text-red-300 text-xs rounded-md border border-red-900" title={s.reasoning || ""}>{s.skill}</span>
                  ))
                ) : <span className="text-zinc-600 italic text-xs">None</span>}
            </div>
          </div>
        </Card>

        {/* RESPONSIBILITIES CARD */}
        {(data.matched_skills?.some(s => s.category === 'RESPONSIBILITY') || data.missing_skills?.some(s => s.category === 'RESPONSIBILITY')) && (
            <Card className="bg-zinc-950/50 border-zinc-800 p-6 flex flex-col gap-6 md:col-span-2">
              <h3 className="text-sm uppercase font-bold text-zinc-300">
                <span>📋 Key Responsibilities</span>
              </h3>
              <div>
                <div className="flex flex-wrap gap-2">
                    {[...(data.matched_skills || []), ...(data.missing_skills || [])].filter(s => s.category === 'RESPONSIBILITY').length > 0 ? (
                      [...(data.matched_skills || []), ...(data.missing_skills || [])].filter(s => s.category === 'RESPONSIBILITY').map((s, i) => (
                        <span key={i} className="px-3 py-1.5 bg-zinc-900 text-zinc-300 text-xs rounded-md border border-zinc-700" title={s.reasoning || ""}>{s.skill}</span>
                      ))
                    ) : <span className="text-zinc-600 italic text-xs">None</span>}
                </div>
              </div>
            </Card>
        )}

      </div>
    </main>
  );
}
