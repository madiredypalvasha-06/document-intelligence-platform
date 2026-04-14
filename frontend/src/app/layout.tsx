import type { Metadata } from 'next';
import { Toaster } from 'react-hot-toast';
import { Sidebar } from '@/components/Sidebar';
import './globals.css';

export const metadata: Metadata = {
  title: 'Document Intelligence Platform',
  description: 'AI-powered book analysis and Q&A platform with RAG pipeline',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-cream-50">
        <Sidebar />
        <main className="pl-72 transition-all duration-500">
          <div className="min-h-screen">{children}</div>
        </main>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1a1a1a',
              color: '#fff',
              borderRadius: '0.75rem',
              fontFamily: 'DM Sans, system-ui, sans-serif',
            },
            success: {
              iconTheme: {
                primary: '#d4821f',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </body>
    </html>
  );
}
