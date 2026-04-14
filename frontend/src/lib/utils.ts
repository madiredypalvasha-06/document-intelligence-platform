import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function capitalizeFirst(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function formatRating(rating: number | string | undefined): string {
  if (rating === undefined || rating === null) return 'N/A';
  const num = typeof rating === 'string' ? parseFloat(rating) : rating;
  if (isNaN(num)) return 'N/A';
  return num.toFixed(1);
}

export function getGenreColor(genre: string): string {
  const colors: Record<string, string> = {
    fiction: 'bg-blue-50 text-blue-700 border border-blue-200',
    'non-fiction': 'bg-green-50 text-green-700 border border-green-200',
    mystery: 'bg-purple-50 text-purple-700 border border-purple-200',
    'sci-fi': 'bg-indigo-50 text-indigo-700 border border-indigo-200',
    fantasy: 'bg-pink-50 text-pink-700 border border-pink-200',
    romance: 'bg-red-50 text-red-700 border border-red-200',
    thriller: 'bg-gray-50 text-gray-700 border border-gray-200',
    horror: 'bg-red-100 text-red-800 border border-red-300',
    biography: 'bg-amber-50 text-amber-700 border border-amber-200',
    'self-help': 'bg-teal-50 text-teal-700 border border-teal-200',
    business: 'bg-cyan-50 text-cyan-700 border border-cyan-200',
    history: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
    science: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    technology: 'bg-sky-50 text-sky-700 border border-sky-200',
    other: 'bg-gray-50 text-gray-700 border border-gray-200',
  };
  return colors[genre.toLowerCase()] || colors.other;
}

export function getSentimentColor(label: string): string {
  const colors: Record<string, string> = {
    positive: 'text-green-600 bg-green-50',
    negative: 'text-red-600 bg-red-50',
    neutral: 'text-gray-600 bg-gray-50',
  };
  return colors[label.toLowerCase()] || colors.neutral;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    completed: 'text-green-600 bg-green-50',
    running: 'text-blue-600 bg-blue-50',
    pending: 'text-yellow-600 bg-yellow-50',
    failed: 'text-red-600 bg-red-50',
  };
  return colors[status.toLowerCase()] || colors.pending;
}

export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
