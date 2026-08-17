'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

import { AnalyzeResponse } from '../types';

export default function History() {
  const [analyses, setAnalyses] = useState<AnalyzeResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    fetch(`${apiUrl}/analyze`)
      .then(res => { if (!res.ok) throw new Error("Failed to load history"); return res.json(); })
      .then(setAnalyses)
      .catch(e => setError(e.message));
  }, []);

  if (error) return <main className="p-8 text-red-500 font-semibold">{error}</main>;
  if (!analyses) return <main className="p-8 text-zinc-400">Loading analysis history...</main>;

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-2xl font-bold text-white">Analysis History</h1>
      {analyses.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-zinc-800 rounded">
          <p className="text-zinc-500 italic">No analysis history yet. Analyze your first resume!</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {analyses.map(a => (
            <Link href={`/results/${a.id}`} key={a.id} className="grid grid-cols-4 items-center p-4 bg-zinc-900 border border-zinc-700 rounded hover:border-indigo-600 transition-colors">
              <span className="text-zinc-500 font-mono text-xs truncate">{a.id.slice(0, 8)}</span>
              <span className="font-bold text-indigo-400 text-lg">{a.overall_score}% Match</span>
              <span className="text-zinc-400 text-sm">{new Date(a.created_at).toLocaleDateString()}</span>
              <span className="text-right text-zinc-600 font-bold">→</span>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
