import React from 'react';
import { cn } from '../lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', className, isLoading, ...props }) => {
  const base = "px-4 py-2 rounded-md font-semibold text-sm transition-all text-center flex items-center justify-center disabled:opacity-50";
  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
    secondary: "bg-zinc-800 text-zinc-100 hover:bg-zinc-700",
    outline: "border border-zinc-700 text-zinc-300 hover:border-zinc-500"
  };
  return (
    <button className={cn(base, variants[variant], className)} {...props} disabled={isLoading || props.disabled}>
      {isLoading ? "Loading..." : children}
    </button>
  );
};
