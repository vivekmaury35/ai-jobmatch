'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  // When the component mounts, fetch the health endpoint from the backend
  useEffect(() => {
    // We use NEXT_PUBLIC_API_URL or fallback to localhost directly
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    
    fetch(`${apiUrl}/health`)
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((data) => {
        setHealthStatus(JSON.stringify(data));
      })
      .catch((error) => {
        console.error('Failed to connect to backend:', error);
        setHealthStatus('error connecting to backend');
      });
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-zinc-950 text-white">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-blue-400">AI JobMatch</h1>
        
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 max-w-md">
          <h2 className="text-xl font-semibold mb-4">Phase 0 Status</h2>
          <div className="flex items-center gap-4">
            <div className="text-zinc-400">Backend Health:</div>
            <code className={`px-2 py-1 rounded ${
              healthStatus === '{"status":"ok"}' 
                ? 'bg-green-900/50 text-green-400 border border-green-800' 
                : 'bg-red-900/50 text-red-400 border border-red-800'
            }`}>
              {healthStatus}
            </code>
          </div>
          <p className="mt-4 text-xs text-zinc-500">
            If this says {"{\"status\":\"ok\"}"}, the Next.js frontend is successfully talking to the FastAPI backend!
          </p>
        </div>
      </div>
    </main>
  );
}
