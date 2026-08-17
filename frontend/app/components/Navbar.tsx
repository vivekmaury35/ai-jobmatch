import Link from 'next/link';

export const Navbar = () => (
  <nav className="border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-sm sticky top-0 z-50">
    <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
      <Link href="/" className="font-bold text-lg text-white flex items-center gap-2">
        <span className="w-6 h-6 bg-indigo-600 rounded"></span>
        AI JobMatch
      </Link>
      <div className="flex gap-6">
        <Link href="/" className="text-sm text-zinc-400 hover:text-white transition">Analyze</Link>
        <Link href="/history" className="text-sm text-zinc-400 hover:text-white transition">History</Link>
      </div>
    </div>
  </nav>
);
