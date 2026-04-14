'use client';

import React, { Suspense, useEffect, useState, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  MessageCircle,
  Send,
  BookOpen,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Clock,
  Zap,
  Brain,
} from 'lucide-react';
import { qaApi, bookApi } from '@/lib/api';
import { useQAStore } from '@/store';
import { Button, Select, LoadingSpinner, SkeletonChat, Toast } from '@/components/ui';
import { copyToClipboard, generateSessionId, formatDateTime } from '@/lib/utils';
import type { Book, Conversation } from '@/types';

const SAMPLE_QUESTIONS = [
  'What is the main theme of this book?',
  'Give me a brief summary of the plot',
  'Who would enjoy reading this book?',
  'What are the key takeaways from this book?',
  'How does this book compare to similar works?',
];

function QAPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const {
    conversations,
    currentSessionId,
    setConversations,
    addConversation,
    setSessionId,
    clearConversations,
  } = useQAStore();

  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [model, setModel] = useState<'lm-studio' | 'openai' | 'anthropic'>('lm-studio');
  const [useRag, setUseRag] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      setSessionId(sessionId);
      loadHistory(sessionId);
    } else if (!currentSessionId) {
      setSessionId(generateSessionId());
    }

    const bookId = searchParams.get('book_id');
    if (bookId) {
      loadSelectedBook(parseInt(bookId));
    }

    loadBooks();
  }, [searchParams, currentSessionId, setSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  const loadBooks = async () => {
    try {
      const data = await bookApi.list({ page: 1 });
      setBooks(data.results);
    } catch (error) {
      console.error('Failed to load books:', error);
    }
  };

  const loadSelectedBook = async (bookId: number) => {
    try {
      const book = await bookApi.get(bookId);
      setSelectedBook(book);
    } catch (error) {
      console.error('Failed to load book:', error);
    }
  };

  const loadHistory = async (sessionId: string) => {
    try {
      const history = await qaApi.getHistory(sessionId);
      setConversations(history);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const currentQuestion = question;
    setQuestion('');
    setIsLoading(true);

    try {
      const response = await qaApi.ask({
        question: currentQuestion,
        book_id: selectedBook?.id,
        session_id: currentSessionId,
        use_rag: useRag,
        model: model,
      });

      const newConversation: Conversation = {
        id: response.conversation_id,
        session_id: response.session_id,
        book: selectedBook?.id,
        book_title: selectedBook?.title,
        question: currentQuestion,
        answer: response.answer,
        sources: response.sources,
        model_used: response.model_used,
        response_time: response.response_time,
        retrieved_chunks: response.retrieved_chunks,
        created_at: new Date().toISOString(),
      };

      addConversation(newConversation);
      router.replace(`/qa?session_id=${currentSessionId}${selectedBook ? `&book_id=${selectedBook.id}` : ''}`);
    } catch (error) {
      console.error('Failed to ask question:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async (text: string, id: number) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleBookSelect = (bookId: string) => {
    if (bookId) {
      loadSelectedBook(parseInt(bookId));
    } else {
      setSelectedBook(null);
    }
  };

  const handleNewChat = () => {
    clearConversations();
    setSessionId(generateSessionId());
    setSelectedBook(null);
    router.replace('/qa');
  };

  const handleSampleQuestion = (sampleQuestion: string) => {
    setQuestion(sampleQuestion);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex h-screen bg-cream-50">
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-cream-200 px-6 py-4 shadow-elegant">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 shadow-gold">
                <MessageCircle className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="font-serif text-xl font-bold text-obsidian-800">Q&A Assistant</h1>
                <p className="text-sm text-obsidian-500">
                  Ask questions about books using AI
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {currentSessionId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowHistory(!showHistory)}
                  icon={<Clock className="h-4 w-4" />}
                >
                  History
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleNewChat}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                New Chat
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-elegant">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <div className="bg-white rounded-2xl border border-cream-200 p-5 mb-6 shadow-elegant">
              <div className="grid gap-4 sm:grid-cols-2 mb-5">
                <Select
                  label="Select a Book (optional)"
                  options={[
                    { value: '', label: 'Ask about any topic' },
                    ...books.map((b) => ({
                      value: b.id.toString(),
                      label: `${b.title} by ${b.author}`,
                    })),
                  ]}
                  value={selectedBook?.id?.toString() || ''}
                  onChange={(e) => handleBookSelect(e.target.value)}
                />

                <Select
                  label="AI Model"
                  options={[
                    { value: 'lm-studio', label: 'LM Studio (Local)' },
                    { value: 'openai', label: 'OpenAI GPT' },
                    { value: 'anthropic', label: 'Anthropic Claude' },
                  ]}
                  value={model}
                  onChange={(e) => setModel(e.target.value as typeof model)}
                />
              </div>

              <div className="flex items-center gap-4 mb-5">
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useRag}
                    onChange={(e) => setUseRag(e.target.checked)}
                    className="w-4 h-4 rounded border-obsidian-300 text-gold-500 focus:ring-gold-400"
                  />
                  <span className="text-sm text-obsidian-700 font-medium">
                    Use RAG (Retrieval-Augmented Generation)
                  </span>
                </label>
                <span className="text-xs text-obsidian-400 flex items-center gap-1">
                  <Zap className="h-3 w-3 text-gold-500" />
                  Requires processed books
                </span>
              </div>

              {selectedBook && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-gold-50 to-cream-50 border border-gold-200">
                  <BookOpen className="h-5 w-5 text-gold-600" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-obsidian-800">
                      {selectedBook.title}
                    </p>
                    <p className="text-xs text-obsidian-500">by {selectedBook.author}</p>
                  </div>
                  <button
                    onClick={() => setSelectedBook(null)}
                    className="text-sm text-gold-600 hover:text-gold-700 font-medium"
                  >
                    Change
                  </button>
                </div>
              )}
            </div>

            {conversations.length === 0 ? (
              <div className="text-center py-16">
                <div className="mx-auto h-20 w-20 rounded-2xl bg-gradient-to-br from-gold-100 to-cream-100 flex items-center justify-center mb-6">
                  <Brain className="h-10 w-10 text-gold-600" />
                </div>
                <h2 className="font-serif text-2xl font-bold text-obsidian-800">
                  What would you like to know?
                </h2>
                <p className="mt-3 text-obsidian-500 max-w-lg mx-auto leading-relaxed">
                  Ask questions about books and get AI-powered answers with citations
                  from the source material.
                </p>

                <div className="mt-10">
                  <p className="text-sm text-obsidian-500 mb-4 font-medium">Try these sample questions:</p>
                  <div className="flex flex-wrap justify-center gap-3">
                    {SAMPLE_QUESTIONS.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleSampleQuestion(q)}
                        className="px-5 py-2.5 rounded-xl bg-white text-sm text-obsidian-700 border border-cream-200 hover:border-gold-300 hover:bg-gold-50 transition-all font-medium shadow-sm"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {conversations.map((conv) => (
                  <div key={conv.id} className="space-y-6 animate-fade-in">
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-900">
                        <span className="text-sm font-bold text-gold-400">Q</span>
                      </div>
                      <div className="flex-1">
                        <div className="bg-white rounded-xl px-5 py-4 shadow-elegant border border-cream-100">
                          <p className="text-sm text-obsidian-800 font-medium">{conv.question}</p>
                        </div>
                        {conv.book_title && (
                          <p className="mt-2 text-xs text-obsidian-400 flex items-center gap-1">
                            <BookOpen className="h-3 w-3" />
                            About: {conv.book_title}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-gold-400 to-gold-600">
                        <Sparkles className="h-5 w-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="bg-white rounded-xl px-5 py-4 shadow-elegant border border-cream-100">
                          <p className="text-sm text-obsidian-800 leading-relaxed whitespace-pre-wrap">
                            {conv.answer}
                          </p>

                          <div className="mt-4 flex items-center gap-5 text-xs text-obsidian-400">
                            <span className="flex items-center gap-1.5">
                              <Zap className="h-3 w-3" />
                              {conv.model_used}
                            </span>
                            <span className="flex items-center gap-1.5">
                              <Clock className="h-3 w-3" />
                              {conv.response_time.toFixed(2)}s
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}

            {isLoading && (
              <div className="mt-8 animate-fade-in">
                <div className="flex gap-4">
                  <div className="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-gold-400 to-gold-600">
                    <Sparkles className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1 bg-white rounded-xl px-5 py-4 shadow-elegant border border-cream-100">
                    <div className="flex items-center gap-3">
                      <LoadingSpinner size="sm" />
                      <span className="text-sm text-obsidian-500 animate-pulse">
                        Thinking...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-8">
              <form onSubmit={handleSubmit} className="relative">
                <div className="bg-white rounded-2xl border border-cream-200 shadow-elegant overflow-hidden">
                  <textarea
                    ref={textareaRef}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question about books..."
                    rows={3}
                    className="w-full resize-none border-0 px-5 py-4 focus:outline-none focus:ring-0 text-obsidian-800 placeholder:text-obsidian-400"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                  />
                  <div className="flex items-center justify-between border-t border-cream-200 px-5 py-3 bg-cream-50">
                    <p className="text-xs text-obsidian-400">
                      Press Enter to send, Shift+Enter for new line
                    </p>
                    <Button
                      type="submit"
                      disabled={!question.trim() || isLoading}
                      loading={isLoading}
                      variant="gold"
                      icon={<Send className="h-4 w-4" />}
                    >
                      Send
                    </Button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {showHistory && (
        <div className="w-80 border-l border-cream-200 bg-white overflow-y-auto scrollbar-elegant">
          <div className="p-5 border-b border-cream-200 bg-cream-50">
            <h3 className="font-serif font-semibold text-obsidian-800">Chat History</h3>
            <p className="text-xs text-obsidian-400 mt-1">
              Session: {currentSessionId.slice(0, 12)}...
            </p>
          </div>
          <div className="p-4 space-y-3">
            {conversations.length > 0 ? (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className="p-4 rounded-xl bg-cream-50 hover:bg-cream-100 cursor-pointer transition-colors border border-cream-100"
                  onClick={() => setShowHistory(false)}
                >
                  <p className="text-sm text-obsidian-800 font-medium line-clamp-2">
                    {conv.question}
                  </p>
                  <p className="text-xs text-obsidian-400 mt-2">
                    {formatDateTime(conv.created_at)}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-obsidian-500 text-center py-8">
                No history yet
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function QAPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-cream-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-obsidian-500">Loading Q&A...</p>
        </div>
      </div>
    }>
      <QAPageContent />
    </Suspense>
  );
}
