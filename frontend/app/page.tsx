'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { getApiUrl } from './lib/utils';
import { FileUp, X, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';


const STEPS = [
  { id: 'resumes', label: 'Processing Resume...' },
  { id: 'jobs', label: 'Parsing Job Description...' },
  { id: 'analyze', label: 'Matching & AI Analysis...' },
];

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [jd, setJd] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [usePreviousResume, setUsePreviousResume] = useState(false);
  const [lastResumeId, setLastResumeId] = useState<string | null>(null);

  // Load last resume ID from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('lastResumeId');
    if (saved) {
      setLastResumeId(saved);
    }
  }, []);

  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const droppedFile = e.dataTransfer.files?.[0];
      if (droppedFile && droppedFile.type === "application/pdf") {
          setFile(droppedFile);
          setFileName(droppedFile.name);
          setError(null);
      } else {
          setError("Please drop a valid PDF file.");
      }
  };

  const handleSubmit = async () => {
    if (!file || !jd) { setError("Resume and Job Description are required."); return; }
    if (jd.split(' ').filter(Boolean).length < 50) { setError("Please paste the full job description (at least 50 words)."); return; }

    setLoading(true); setError(null);
    const apiUrl = getApiUrl();
    const storedSession = localStorage.getItem('session_id') || "";


    try {
      setCurrentStep(0);
      const formData = new FormData(); formData.append('file', file);
      const resumeRes = await fetch(`${apiUrl}/resumes`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Session-ID': storedSession
        }
      });

      if (!resumeRes.ok) {
        const errorData = await resumeRes.json().catch(() => ({}));
        const errorMsg = errorData.detail?.message || errorData.message || `Resume upload failed (${resumeRes.status})`;
        throw new Error(errorMsg);
      }

      const sessionHeader = resumeRes.headers.get("X-Session-ID");
      if (sessionHeader) localStorage.setItem('session_id', sessionHeader);

      const resume = await resumeRes.json();

      setCurrentStep(1);
      const jobRes = await fetch(`${apiUrl}/jobs`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': localStorage.getItem('session_id') || ""
        },
        body: JSON.stringify({ raw_text: jd })
      });
      if (!jobRes.ok) throw new Error('JD submission failed.');
      const jobSessionHeader = jobRes.headers.get("X-Session-ID");
      if (jobSessionHeader) localStorage.setItem('session_id', jobSessionHeader);
      const job = await jobRes.json();

      setCurrentStep(2);
      const analyzeRes = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': localStorage.getItem('session_id') || ""
        },
        body: JSON.stringify({ resume_id: resume.id, job_id: job.id })
      });

      if (!analyzeRes.ok) throw new Error('Analysis failed.');
      const analyzeSessionHeader = analyzeRes.headers.get("X-Session-ID");
      if (analyzeSessionHeader) localStorage.setItem('session_id', analyzeSessionHeader);
      const analysis = await analyzeRes.json();

      router.push(`/results/${analysis.id}`);
    } catch (e: unknown) {
        if (e instanceof Error) setError(e.message);
        else setError("An unexpected error occurred.");
    } finally { setLoading(false); }
  };

  return (
    <main className="max-w-3xl mx-auto p-12">
      <div className="mb-10 text-center">
        <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight">AI JobMatch</h1>
      </div>

      {!loading ? (
        <Card className="space-y-6">
            <div className="mb-4">
              {lastResumeId ? (
                <div className="flex items-center gap-3">
                  <span className="text-zinc-300 font-medium">Last resume:</span>
                  <span className="text-zinc-400 truncate max-w-xs">{fileName || 'Unknown'}</span>
                  <label className="flex items-center gap-2 text-sm text-zinc-500">
                    <input
                      type="checkbox"
                      checked={usePreviousResume}
                      onChange={(e) => setUsePreviousResume(e.target.checked)}
                    />
                    <span>Use this resume</span>
                  </label>
                </div>
              ) : null}
            </div>
            {!file ? (
                <label
                  onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setIsDragOver(false); }}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed ${isDragOver ? 'border-indigo-500 bg-indigo-500/10' : 'border-zinc-700'} rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer hover:border-indigo-500 transition-colors`}>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf"
                    onChange={(e) => {
                      const selectedFile = e.target.files?.[0];
                      if (selectedFile) {
                        setFile(selectedFile);
                        setFileName(selectedFile.name);
                        setError(null);
                      }
                    }}
                  />
                  <FileUp size={48} className={`${isDragOver ? 'text-indigo-400' : 'text-zinc-600'} mb-4 transition-colors`} />
                  <div className="text-zinc-300 font-medium">Click or Drag & Drop your resume (PDF)</div>
                </label>
            ) : (
                <div className="border border-emerald-700 bg-emerald-950/20 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 size={20} className="text-emerald-500" />
                    <span className="text-zinc-300 text-sm truncate">{fileName}</span>
                  </div>
                  <button onClick={() => {
                    setFile(null);
                    setFileName(null);
                    setUsePreviousResume(false);
                  }} className="text-zinc-500 hover:text-red-400"><X size={18}/></button>
                </div>
            )}
            <textarea value={jd} onChange={(e) => setJd(e.target.value)} placeholder="Paste the full job description (min 50 words)..." className="w-full h-48 bg-zinc-950 p-4 rounded-md border border-zinc-700 text-zinc-200 outline-none focus:ring-1 focus:ring-indigo-500" />
            <Button onClick={handleSubmit} className="w-full py-6 text-lg">Analyze Match</Button>
            {error && <div className="p-4 bg-red-900/10 border border-red-900 rounded-lg text-red-400 text-sm">{error}</div>}
        </Card>
      ) : (
        <Card className="space-y-8 p-12">
            <h2 className="text-2xl font-bold text-center text-white mb-8">Analyzing...</h2>
            {STEPS.map((step, i) => (
                <div key={step.id} className={`flex items-center gap-4 ${i === currentStep ? 'opacity-100 scale-105 transition-all' : 'opacity-40'}`}>
                    <div className="w-8 h-8 rounded-full flex items-center justify-center bg-zinc-800">
                        {i < currentStep ? <CheckCircle2 size={18} className="text-emerald-500"/> : i === currentStep ? <Loader2 size={18} className="animate-spin text-indigo-400" /> : <div className="w-2 h-2 rounded-full bg-zinc-600"/>}
                    </div>
                    <span className="text-white font-medium">{step.label}</span>
                </div>
            ))}
        </Card>
      )}
    </main>
  );
}
