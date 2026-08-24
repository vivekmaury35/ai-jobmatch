'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Trash2 } from 'lucide-react';
import { AnalyzeResponse } from '../types';
import { Button } from '../components/ui/Button';
import { getApiUrl } from '../lib/utils';

export default function History() {
  const [analyses, setAnalyses] = useState<AnalyzeResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = getApiUrl();
    const storedSession = localStorage.getItem('session_id') || "";

    fetch(`${apiUrl}/analyze`, {
        credentials: 'include',
        headers: { 'X-Session-ID': storedSession }
    })
      .then(res => { if (!res.ok) throw new Error("Failed to load history"); return res.json(); })
      .then(setAnalyses)
      .catch(e => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  const deleteAnalysis = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const apiUrl = getApiUrl();
    await fetch(`${apiUrl}/analyze/${id}`, { method: 'DELETE', credentials: 'include' });
    setAnalyses(prev => prev ? prev.filter(a => a.id !== id) : null);
  };


  if (error) return <main className="p-8 text-red-500 font-semibold">{error}</main>;
  if (!analyses) return <main className="p-8 text-zinc-400">Loading analysis history...</main>;

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-2xl font-bold text-white">Analysis History</h1>
      {analyses.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-zinc-800 rounded">
          <p className="text-zinc-500 italic">No analysis history yet.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {analyses.map(a => (
            <div key={a.id} className="flex items-center p-4 bg-zinc-900 border border-zinc-700 rounded hover:border-indigo-600 transition-colors">
              <Link href={`/results/${a.id}`} className="flex-grow grid grid-cols-3 items-center">
                <span className="text-zinc-200 font-semibold">{a.job_title || "Unknown Role"}</span>
                <span className="font-bold text-indigo-400">{a.overall_score}% Match</span>
                <span className="text-zinc-400 text-sm">{new Date(a.created_at).toLocaleDateString()}</span>
              </Link>
              <Button onClick={(e) => deleteAnalysis(e, a.id)} variant="outline" className="ml-4 h-8 w-8 !p-1 text-red-400 hover:text-red-300">
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
