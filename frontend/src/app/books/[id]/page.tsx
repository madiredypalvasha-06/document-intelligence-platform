'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  BookOpen,
  Star,
  ExternalLink,
  MessageCircle,
  Sparkles,
  ThumbsUp,
  Tag,
  Calendar,
  FileText,
} from 'lucide-react';
import { bookApi } from '@/lib/api';
import { Button, LoadingSpinner, Badge } from '@/components/ui';
import {
  formatDate,
  getGenreColor,
  getSentimentColor,
  cn,
} from '@/lib/utils';
import type { Book } from '@/types';

export default function BookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [book, setBook] = useState<Book | null>(null);
  const [similarBooks, setSimilarBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'ai' | 'similar'>('overview');

  const bookId = params?.id ? parseInt(params.id as string) : null;

  useEffect(() => {
    const fetchBookData = async () => {
      if (!bookId || isNaN(bookId)) {
        router.push('/books');
        return;
      }

      try {
        const bookData = await bookApi.get(bookId);
        setBook(bookData);

        if (bookData.is_processed) {
          const recommendations = await bookApi.recommendations(bookId).catch(() => []);
          setSimilarBooks(recommendations);
        }
      } catch (error) {
        console.error('Failed to fetch book:', error);
        router.push('/books');
      } finally {
        setLoading(false);
      }
    };

    fetchBookData();
  }, [bookId, router]);

  const handleProcess = async () => {
    if (!book) return;
    setProcessing(true);
    try {
      const result = await bookApi.process(book.id);
      setBook({ ...book, is_processed: true, ai_insights: result.ai_insights });
    } catch (error) {
      console.error('Failed to process book:', error);
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-cream-50">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-gold-200 border-t-gold-500 mx-auto" />
          <p className="mt-4 text-obsidian-500">Loading book details...</p>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="flex h-screen items-center justify-center bg-cream-50">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-obsidian-800">Book not found</h2>
          <Link href="/books" className="mt-4 inline-block text-gold-600 hover:text-gold-700">
            Back to Books
          </Link>
        </div>
      </div>
    );
  }

  const rating = book.rating ? parseFloat(String(book.rating)) : null;

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <div className="bg-white border-b border-cream-200">
        <div className="mx-auto max-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <Link href="/books" className="flex items-center gap-2 text-obsidian-600 hover:text-obsidian-800">
              <ArrowLeft className="h-5 w-5" />
              Back to Books
            </Link>
          </div>
        </div>
      </div>

      <div className="mx-auto max-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Book Info Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-cream-200 p-6">
              <div className="flex gap-6">
                <div className="flex h-48 w-32 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-obsidian-100 to-obsidian-200 shadow-md">
                  <BookOpen className="h-16 w-16 text-obsidian-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4">
                    <h1 className="font-serif text-3xl font-bold text-obsidian-800">{book.title}</h1>
                    {book.is_featured && (
                      <span className="rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-4 py-1 text-xs font-medium text-white">
                        Featured
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-lg text-obsidian-600">{book.author}</p>
                  
                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <span className={cn('rounded-full px-4 py-1.5 text-sm font-medium capitalize', getGenreColor(book.genre))}>
                      {book.genre}
                    </span>
                    {rating && (
                      <div className="flex items-center gap-1.5">
                        <Star className="h-5 w-5 text-gold-500 fill-gold-500" />
                        <span className="font-semibold text-obsidian-800">{rating.toFixed(1)}</span>
                        {book.num_ratings !== undefined && (
                          <span className="text-obsidian-500">({book.num_ratings.toLocaleString()} ratings)</span>
                        )}
                      </div>
                    )}
                    {book.is_processed && (
                      <span className="flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1.5 text-sm font-medium text-green-700">
                        <span className="h-2 w-2 rounded-full bg-green-500" />
                        AI Processed
                      </span>
                    )}
                  </div>

                  {book.description && (
                    <p className="mt-4 text-obsidian-600 leading-relaxed">{book.description}</p>
                  )}

                  <div className="mt-6 flex gap-3">
                    <Link href={`/qa?book=${book.id}`}>
                      <Button variant="gold" icon={<MessageCircle className="h-4 w-4" />}>
                        Ask Questions
                      </Button>
                    </Link>
                    {!book.is_processed && (
                      <Button variant="outline" onClick={handleProcess} loading={processing} icon={<Sparkles className="h-4 w-4" />}>
                        Generate AI Insights
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-2xl shadow-sm border border-cream-200 overflow-hidden">
              <div className="flex border-b border-cream-200">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={cn(
                    'flex-1 px-6 py-4 text-sm font-medium transition-colors',
                    activeTab === 'overview'
                      ? 'border-b-2 border-gold-500 text-gold-600'
                      : 'text-obsidian-500 hover:text-obsidian-700'
                  )}
                >
                  Overview
                </button>
                <button
                  onClick={() => setActiveTab('ai')}
                  className={cn(
                    'flex-1 px-6 py-4 text-sm font-medium transition-colors',
                    activeTab === 'ai'
                      ? 'border-b-2 border-gold-500 text-gold-600'
                      : 'text-obsidian-500 hover:text-obsidian-700'
                  )}
                >
                  AI Insights
                </button>
                <button
                  onClick={() => setActiveTab('similar')}
                  className={cn(
                    'flex-1 px-6 py-4 text-sm font-medium transition-colors',
                    activeTab === 'similar'
                      ? 'border-b-2 border-gold-500 text-gold-600'
                      : 'text-obsidian-500 hover:text-obsidian-700'
                  )}
                >
                  Similar Books
                </button>
              </div>

              <div className="p-6">
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      {book.publisher && (
                        <div className="p-4 rounded-xl bg-cream-50">
                          <div className="flex items-center gap-2 text-obsidian-500 mb-1">
                            <FileText className="h-4 w-4" />
                            <span className="text-sm">Publisher</span>
                          </div>
                          <p className="font-medium text-obsidian-800">{book.publisher}</p>
                        </div>
                      )}
                      {book.published_date && (
                        <div className="p-4 rounded-xl bg-cream-50">
                          <div className="flex items-center gap-2 text-obsidian-500 mb-1">
                            <Calendar className="h-4 w-4" />
                            <span className="text-sm">Published</span>
                          </div>
                          <p className="font-medium text-obsidian-800">{formatDate(book.published_date)}</p>
                        </div>
                      )}
                      {book.page_count && (
                        <div className="p-4 rounded-xl bg-cream-50">
                          <div className="flex items-center gap-2 text-obsidian-500 mb-1">
                            <BookOpen className="h-4 w-4" />
                            <span className="text-sm">Pages</span>
                          </div>
                          <p className="font-medium text-obsidian-800">{book.page_count}</p>
                        </div>
                      )}
                      {book.language && (
                        <div className="p-4 rounded-xl bg-cream-50">
                          <div className="flex items-center gap-2 text-obsidian-500 mb-1">
                            <Tag className="h-4 w-4" />
                            <span className="text-sm">Language</span>
                          </div>
                          <p className="font-medium text-obsidian-800 capitalize">{book.language}</p>
                        </div>
                      )}
                    </div>

                    {book.tags && book.tags.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-obsidian-500 mb-3">Tags</h3>
                        <div className="flex flex-wrap gap-2">
                          {book.tags.map((tag, i) => (
                            <span key={i} className="rounded-full bg-obsidian-100 px-3 py-1 text-sm text-obsidian-600">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'ai' && (
                  <div>
                    {!book.is_processed ? (
                      <div className="text-center py-8">
                        <Sparkles className="h-12 w-12 mx-auto text-obsidian-300" />
                        <h3 className="mt-4 font-semibold text-obsidian-800">AI Insights Not Available</h3>
                        <p className="mt-2 text-sm text-obsidian-500">
                          Generate AI insights to see analysis, summaries, and recommendations.
                        </p>
                        <Button variant="gold" onClick={handleProcess} loading={processing} className="mt-4">
                          Generate Insights
                        </Button>
                      </div>
                    ) : book.ai_insights ? (
                      <div className="space-y-6">
                        {book.ai_insights.summary && (
                          <div>
                            <h3 className="flex items-center gap-2 text-sm font-semibold text-obsidian-700 mb-3">
                              <Sparkles className="h-4 w-4 text-gold-500" />
                              AI Summary
                            </h3>
                            <p className="text-obsidian-600 leading-relaxed">{book.ai_insights.summary}</p>
                          </div>
                        )}

                        {book.ai_insights.genre_analysis && (
                          <div>
                            <h3 className="flex items-center gap-2 text-sm font-semibold text-obsidian-700 mb-3">
                              <Tag className="h-4 w-4 text-gold-500" />
                              Genre Analysis
                            </h3>
                            <div className="p-4 rounded-xl bg-cream-50">
                              <p className="font-medium text-obsidian-800 capitalize">
                                Primary: {book.ai_insights.genre_analysis.primary_genre}
                              </p>
                              {book.ai_insights.genre_analysis.secondary_genres?.length > 0 && (
                                <p className="text-sm text-obsidian-600 mt-1">
                                  Related: {book.ai_insights.genre_analysis.secondary_genres.join(', ')}
                                </p>
                              )}
                              <p className="text-xs text-obsidian-500 mt-2">
                                Confidence: {(book.ai_insights.genre_analysis.confidence * 100).toFixed(0)}%
                              </p>
                            </div>
                          </div>
                        )}

                        {book.ai_insights.review_sentiment && (
                          <div>
                            <h3 className="flex items-center gap-2 text-sm font-semibold text-obsidian-700 mb-3">
                              <ThumbsUp className="h-4 w-4 text-gold-500" />
                              Reader Sentiment
                            </h3>
                            <div className="p-4 rounded-xl bg-cream-50">
                              <div className="flex items-center gap-2">
                                <span className={cn('rounded-full px-3 py-1 text-sm font-medium capitalize', getSentimentColor(book.ai_insights.review_sentiment.sentiment_label))}>
                                  {book.ai_insights.review_sentiment.sentiment_label}
                                </span>
                                <span className="text-sm text-obsidian-500">
                                  Score: {book.ai_insights.review_sentiment.sentiment_score.toFixed(1)}
                                </span>
                              </div>
                              {book.ai_insights.review_sentiment.tone && (
                                <p className="text-sm text-obsidian-600 mt-2">
                                  Tone: {book.ai_insights.review_sentiment.tone}
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-center text-obsidian-500">No AI insights available for this book.</p>
                    )}
                  </div>
                )}

                {activeTab === 'similar' && (
                  <div>
                    {similarBooks.length > 0 ? (
                      <div className="grid gap-4 sm:grid-cols-2">
                        {similarBooks.map((similarBook) => (
                          <Link
                            key={similarBook.id}
                            href={`/books/${similarBook.id}`}
                            className="flex gap-4 p-4 rounded-xl bg-cream-50 hover:bg-cream-100 transition-colors"
                          >
                            <div className="flex h-16 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-obsidian-200">
                              <BookOpen className="h-6 w-6 text-obsidian-400" />
                            </div>
                            <div>
                              <h4 className="font-medium text-obsidian-800 line-clamp-1">{similarBook.title}</h4>
                              <p className="text-sm text-obsidian-500">{similarBook.author}</p>
                              <span className="text-xs text-obsidian-400 capitalize">{similarBook.genre}</span>
                            </div>
                          </Link>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-obsidian-500">No similar books found.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {book.source && (
              <div className="bg-white rounded-2xl shadow-sm border border-cream-200 p-6">
                <h3 className="font-semibold text-obsidian-800 mb-3">Source</h3>
                <p className="text-sm text-obsidian-600 capitalize">{book.source}</p>
              </div>
            )}

            <div className="bg-gradient-to-br from-gold-50 via-white to-cream-50 rounded-2xl border border-gold-200 p-6">
              <h3 className="font-semibold text-obsidian-800 mb-3 flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-gold-500" />
                Ask About This Book
              </h3>
              <p className="text-sm text-obsidian-600 mb-4">
                Get answers about this book&apos;s themes, characters, and insights.
              </p>
              <Link href={`/qa?book=${book.id}`}>
                <Button variant="gold" className="w-full">
                  Start Q&A Session
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
