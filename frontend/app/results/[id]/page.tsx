'use client';
import { use, useEffect, useState } from 'react';

export default function Results({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/analyze/${id}`)
      .then(res => {
        if (!res.ok) throw new Error(res.status === 404 ? "Analysis not found" : "Failed to fetch results");
        return res.json();
      })
      .then(setData)
      .catch(e => setError(e.message));
  }, [id]);

  if (error) return <main className="max-w-4xl mx-auto p-8 text-red-500 font-semibold">{error}</main>;
  if (!data) return <main className="max-w-4xl mx-auto p-8 text-zinc-400">Loading analysis results...</main>;

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-zinc-50">Analysis Results</h1>
        <div className="text-4xl font-black text-indigo-400">{data.overall_score}%</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-zinc-900/50 p-6 rounded-lg border border-zinc-800">
          <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-4 font-semibold">Matched Skills</h3>
          {data.matched_skills.length === 0 ? <p className="text-zinc-600 italic">No matches found.</p> :
           <div className="flex flex-wrap gap-2">
             {data.matched_skills.map((s: any) => (
                <span key={s.skill} className="px-2 py-1 bg-emerald-950 text-emerald-400 border border-emerald-900 rounded text-xs">{s.skill}</span>
             ))}
           </div>}
        </div>
        <div className="bg-zinc-900/50 p-6 rounded-lg border border-zinc-800">
           <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-4 font-semibold">Missing Skills</h3>
           {data.missing_skills.length === 0 ? <p className="text-zinc-600 italic">None.</p> :
            <div className="flex flex-wrap gap-2">
              {data.missing_skills.map((s: any) => (
                <span key={s.skill} className="px-2 py-1 bg-red-950 text-red-400 border border-red-900 rounded text-xs">{s.skill}</span>
              ))}
            </div>}
        </div>
      </div>

      <div className="bg-zinc-900 p-6 rounded-lg border border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-300 mb-2">Coach Explanation</h3>
        <p className="text-zinc-400 leading-relaxed">{data.explanation || "No explanation provided."}</p>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-bold text-zinc-50">Actionable Recommendations</h3>
        {data.recommendations.map((r: any, i: number) => (
          <div key={i} className="flex gap-4 p-4 bg-zinc-800/50 rounded-lg border border-zinc-700">
            <span className="flex-none text-indigo-400 font-mono">0{i+1}</span>
            <p className="text-zinc-200">{r.content}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
