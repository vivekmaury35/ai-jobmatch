import { Card } from './Card';

interface SubScore {
    label: string;
    value: number;
    icon?: string;
}

const getScoreColor = (value: number): string => {
  if (value >= 80) return 'text-emerald-400';
  if (value >= 60) return 'text-yellow-400';
  return 'text-red-400';
};

const getScoreBgColor = (value: number): string => {
  if (value >= 80) return 'bg-emerald-500/10 border-emerald-500/30';
  if (value >= 60) return 'bg-yellow-500/10 border-yellow-500/30';
  return 'bg-red-500/10 border-red-500/30';
};

export const SubScoreCard = ({ scores }: { scores: SubScore[] }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {scores.map((s) => {
      const colorClass = getScoreColor(s.value);
      const bgClass = getScoreBgColor(s.value);

      return (
        <Card key={s.label} className={`p-5 flex flex-col items-center justify-center space-y-2 ${bgClass} transition-all hover:scale-105`}>
          <span className="text-[11px] uppercase font-bold text-zinc-400 tracking-wider text-center leading-tight">{s.label}</span>
          <span className={`text-3xl font-extrabold ${colorClass}`}>{s.value}%</span>
          <div className="w-full bg-zinc-800 rounded-full h-1.5 mt-1">
            <div
              className={`h-1.5 rounded-full transition-all ${s.value >= 80 ? 'bg-emerald-500' : s.value >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${s.value}%` }}
            />
          </div>
        </Card>
      );
    })}
  </div>
);
