'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BookOpen,
  MessageCircle,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  Activity,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/store';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Books', href: '/books', icon: BookOpen },
  { name: 'Q&A Assistant', href: '/qa', icon: MessageCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar, health } = useAppStore();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-obsidian-900 transition-all duration-500 ease-out',
        sidebarOpen ? 'w-72' : 'w-24'
      )}
    >
      <div className="flex h-full flex-col">
        <div className={cn(
          "flex items-center border-b border-obsidian-700/50 px-6 py-6 transition-all duration-500",
          sidebarOpen ? 'justify-between' : 'justify-center'
        )}>
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-gold-400 via-gold-500 to-gold-600 shadow-gold">
                  <BookOpen className="h-6 w-6 text-white" />
                </div>
                <div className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full bg-gold-400 animate-pulse" />
              </div>
              <div>
                <h1 className="font-serif text-xl font-bold text-white tracking-wide">DocIntel</h1>
                <p className="text-xs text-obsidian-400">Document Intelligence</p>
              </div>
            </div>
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-gold-400 via-gold-500 to-gold-600 shadow-gold">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
          )}
          <button
            onClick={toggleSidebar}
            className="rounded-lg p-2 text-obsidian-400 hover:bg-obsidian-800 hover:text-white transition-all duration-200"
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-5 w-5" />
            ) : (
              <ChevronRight className="h-5 w-5" />
            )}
          </button>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-6">
          {navigation.map((item, index) => {
            const isActive =
              pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group flex items-center gap-4 rounded-xl px-4 py-3.5 text-sm font-medium transition-all duration-300',
                  isActive
                    ? 'bg-gradient-to-r from-gold-500/20 to-gold-600/10 text-gold-400 border-l-4 border-gold-500'
                    : 'text-obsidian-300 hover:bg-obsidian-800/50 hover:text-white',
                  !sidebarOpen && 'justify-center px-0'
                )}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <item.icon className={cn(
                  'h-5 w-5 flex-shrink-0 transition-all duration-300',
                  isActive ? 'text-gold-400' : 'text-obsidian-400 group-hover:text-white'
                )} />
                {sidebarOpen && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {sidebarOpen && health && (
          <div className="border-t border-obsidian-700/50 p-6">
            <div className="flex items-center gap-2 text-xs text-obsidian-400 mb-4">
              <Activity className="h-4 w-4" />
              <span className="font-medium uppercase tracking-wider">System Status</span>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-obsidian-300">Database</span>
                <span
                  className={cn(
                    'flex items-center gap-1.5 text-sm font-medium',
                    health.database ? 'text-green-400' : 'text-red-400'
                  )}
                >
                  <span className={cn(
                    'h-2 w-2 rounded-full',
                    health.database ? 'bg-green-400' : 'bg-red-400'
                  )} />
                  {health.database ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-obsidian-300">Vector DB</span>
                <span
                  className={cn(
                    'flex items-center gap-1.5 text-sm font-medium',
                    health.chromadb ? 'text-green-400' : 'text-amber-400'
                  )}
                >
                  <span className={cn(
                    'h-2 w-2 rounded-full',
                    health.chromadb ? 'bg-green-400' : 'bg-amber-400'
                  )} />
                  {health.chromadb ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        )}

      </div>
    </aside>
  );
}
