import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getApiUrl(): string {
  let envUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  envUrl = envUrl.trim().replace(/\/+$/, '');
  if (!envUrl.endsWith('/api')) {
    envUrl += '/api';
  }
  return envUrl;
}

