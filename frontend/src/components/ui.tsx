'use client';

import React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

export function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-6xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-obsidian-900/60 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
        <div
          className={cn(
            'relative w-full rounded-2xl bg-white shadow-elegant-lg transform transition-all',
            sizeClasses[size]
          )}
        >
          {title && (
            <div className="flex items-center justify-between border-b border-cream-200 px-6 py-4">
              <h2 className="font-serif text-xl font-semibold text-obsidian-800">{title}</h2>
              <button
                onClick={onClose}
                className="rounded-lg p-2 text-obsidian-400 hover:bg-cream-100 hover:text-obsidian-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  );
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'gold';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: 'bg-obsidian-900 text-white hover:bg-obsidian-950 focus:ring-obsidian-800',
    secondary: 'bg-gold-500 text-white hover:bg-gold-600 focus:ring-gold-400',
    gold: 'bg-gradient-to-r from-gold-500 to-gold-600 text-white hover:from-gold-600 hover:to-gold-700 focus:ring-gold-400 shadow-gold',
    outline: 'border-2 border-obsidian-800 text-obsidian-800 hover:bg-obsidian-800 hover:text-white focus:ring-obsidian-800',
    ghost: 'text-obsidian-600 hover:bg-cream-100 focus:ring-obsidian-400',
  };

  const sizeClasses = {
    sm: 'px-4 py-2 text-xs',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'transition-all duration-300',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg
          className="h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : icon ? (
        icon
      ) : null}
      {children}
    </button>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export function Input({
  label,
  error,
  icon,
  className,
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-medium text-obsidian-700">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            {icon}
          </div>
        )}
        <input
          className={cn(
            'block w-full rounded-lg border-2 border-obsidian-200 bg-white px-4 py-3',
            'text-sm text-obsidian-800 placeholder:text-obsidian-400',
            'transition-all duration-200',
            'focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-200/50',
            'disabled:bg-cream-50 disabled:text-obsidian-500',
            error && 'border-red-500 focus:border-red-500 focus:ring-red-200/50',
            icon && 'pl-10',
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="mt-1.5 text-sm text-red-600">{error}</p>}
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({
  label,
  error,
  className,
  ...props
}: TextareaProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-medium text-obsidian-700">
          {label}
        </label>
      )}
      <textarea
        className={cn(
          'block w-full rounded-lg border-2 border-obsidian-200 bg-white px-4 py-3',
          'text-sm text-obsidian-800 placeholder:text-obsidian-400',
          'transition-all duration-200',
          'focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-200/50',
          'disabled:bg-cream-50 disabled:text-obsidian-500',
          'resize-none',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-200/50',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-red-600">{error}</p>}
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export function Select({
  label,
  error,
  options,
  className,
  ...props
}: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-medium text-obsidian-700">
          {label}
        </label>
      )}
      <select
        className={cn(
          'block w-full rounded-lg border-2 border-obsidian-200 bg-white px-4 py-3',
          'text-sm text-obsidian-800',
          'transition-all duration-200',
          'focus:border-gold-500 focus:outline-none focus:ring-2 focus:ring-gold-200/50',
          'disabled:bg-cream-50 disabled:text-obsidian-500',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-200/50',
          className
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1.5 text-sm text-red-600">{error}</p>}
    </div>
  );
}

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'gold';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className,
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-cream-100 text-obsidian-700 border border-cream-200',
    success: 'bg-green-50 text-green-700 border border-green-200',
    warning: 'bg-gold-50 text-gold-700 border border-gold-200',
    error: 'bg-red-50 text-red-700 border border-red-200',
    info: 'bg-blue-50 text-blue-700 border border-blue-200',
    gold: 'bg-gradient-to-r from-gold-400 to-gold-500 text-white',
  };

  const sizeClasses = {
    sm: 'px-2.5 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <svg
      className={cn('animate-spin text-gold-500', sizeClasses[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
