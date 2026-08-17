import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input: React.FC<InputProps> = ({ label, className = '', ...props }) => {
  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{label}</label>}
      <input
        className={`px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-md text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all ${className}`}
        {...props}
      />
    </div>
  );
};
