'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { FileUp, X, AlertCircle, Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!file || !jd) { setError("Resume and Job Description are required."); return; }
    if (jd.split(' ').filter(Boolean).length < 50) { setError("Please paste the full job description (at least 50 words)."); return; }

    setLoading(true); setError(null);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

    setStatus("Uploading Resume...");
    try {
      const formData = new FormData(); formData.append('file', file);
      const resumeRes = await fetch(`${apiUrl}/resumes`, { method: 'POST', body: formData });
      if (!resumeRes.ok) throw new Error('Resume upload failed.');
      const resume = await resumeRes.json();

      setStatus("Analyzing Job Description...");
      const jobRes = await fetch(`${apiUrl}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: jd })
      });
      if (!jobRes.ok) throw new Error('JD submission failed.');
      const job = await jobRes.json();

      setStatus("Matching Engine running...");
      const analyzeRes = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: resume.id, job_id: job.id })
      });
      if (!analyzeRes.ok) throw new Error('Analysis failed.');
      const analysis = await analyzeRes.json();

      router.push(`/results/${analysis.id}`);
    } catch (e: unknown) {
        if (e instanceof Error) setError(e.message);
        else setError("An unexpected error occurred.");
    } finally { setLoading(false); setStatus(""); }
  };

  return (
    <main className="max-w-3xl mx-auto p-12">
      <div className="mb-10 text-center">
        <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight">AI JobMatch</h1>
        <p className="text-zinc-400 text-lg">Upload your resume to see your instant match analysis.</p>
      </div>

      <Card className="space-y-6">
        {!file ? (
            <label className="border-2 border-dashed border-zinc-700 rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-indigo-500 transition-colors">
              <input type="file" className="hidden" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <FileUp size={48} className="text-zinc-600 mb-4" />
              <div className="text-zinc-300 font-medium">Click to upload your resume (PDF)</div>
              <div className="text-zinc-500 text-sm mt-1">Maximum 5MB</div>
            </label>
        ) : (
            <div className="border border-zinc-700 rounded-lg p-4 flex items-center justify-between bg-zinc-950">
              <span className="text-zinc-300 text-sm truncate">{file.name}</span>
              <button onClick={() => setFile(null)} className="text-zinc-500 hover:text-red-400"><X size={18}/></button>
            </div>
        )}

        <div className="space-y-2">
            <label className="text-xs font-semibold text-zinc-500 uppercase tracking-widest pl-1">Job Description</label>
            <textarea
                value={jd}
                onChange={(e) => setJd(e.target.value)}
                placeholder="Paste the full job description (min 50 words)..."
                className="w-full h-48 bg-zinc-950 p-4 rounded-md border border-zinc-700 text-zinc-200 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
            <div className={`text-xs text-right ${jd.split(' ').filter(Boolean).length < 50 ? 'text-red-500' : 'text-zinc-500'}`}>
                {jd.split(' ').filter(Boolean).length} / 50+ words
            </div>
        </div>

        <Button onClick={handleSubmit} disabled={loading} className="w-full py-6 text-lg">
            {loading ? <><Loader2 className="animate-spin mr-3" />{status}</> : "Analyze Match"}
        </Button>
        {error && <div className="p-4 bg-red-900/10 border border-red-900 rounded-lg flex items-center gap-3 text-red-500 text-sm"><AlertCircle size={20}/>{error}</div>}
      </Card>
    </main>
  );
}
