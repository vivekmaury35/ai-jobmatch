import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
}

export const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', className = '', ...props }) => {
  const base = "px-4 py-2 rounded-md font-semibold text-sm transition-all focus:ring-2 ring-offset-2 ring-offset-zinc-950";
  const variants = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500",
    secondary: "bg-zinc-800 text-zinc-100 hover:bg-zinc-700 focus:ring-zinc-600",
    outline: "border border-zinc-700 text-zinc-300 hover:border-zinc-500"
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};
