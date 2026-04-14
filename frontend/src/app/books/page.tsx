'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Filter,
  Plus,
  Upload,
  RefreshCw,
  Grid3X3,
  List,
  X,
  Library,
  BookOpen,
} from 'lucide-react';
import { bookApi, scrapingApi, sourcesApi } from '@/lib/api';
import { useBookStore } from '@/store';
import { BookCard } from '@/components/BookCard';
import { Button, Input, Select, LoadingSpinner, Modal } from '@/components/ui';
import type { Book, PaginatedResponse, ScrapingJob } from '@/types';

const GENRES = [
  { value: '', label: 'All Genres' },
  { value: 'fiction', label: 'Fiction' },
  { value: 'non-fiction', label: 'Non-Fiction' },
  { value: 'mystery', label: 'Mystery' },
  { value: 'sci-fi', label: 'Science Fiction' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'romance', label: 'Romance' },
  { value: 'thriller', label: 'Thriller' },
  { value: 'horror', label: 'Horror' },
  { value: 'biography', label: 'Biography' },
  { value: 'self-help', label: 'Self-Help' },
  { value: 'business', label: 'Business' },
  { value: 'history', label: 'History' },
  { value: 'science', label: 'Science' },
  { value: 'technology', label: 'Technology' },
  { value: 'other', label: 'Other' },
];

const SORT_OPTIONS = [
  { value: '-created_at', label: 'Newest First' },
  { value: '-rating', label: 'Highest Rated' },
  { value: 'title', label: 'Title A-Z' },
  { value: '-num_ratings', label: 'Most Reviews' },
];

export default function BooksPage() {
  const router = useRouter();
  const {
    books,
    setBooks,
    isLoading,
    setLoading,
    error,
    setError,
    filters,
    setFilters,
    pagination,
    setPage,
    setTotal,
    setHasMore,
  } = useBookStore();

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showScrapeModal, setShowScrapeModal] = useState(false);
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeSource, setScrapeSource] = useState('goodreads');
  const [scrapeMaxBooks, setScrapeMaxBooks] = useState(20);
  const [scrapeLoading, setScrapeLoading] = useState(false);
  const [scrapeJob, setScrapeJob] = useState<ScrapingJob | null>(null);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadAuthor, setUploadAuthor] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [loadingSamples, setLoadingSamples] = useState(false);

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = {
        page: pagination.page,
        sort: filters.sort,
      };
      if (filters.search) params.search = filters.search;
      if (filters.genre) params.genre = filters.genre;
      if (filters.source) params.source = filters.source;

      const data: PaginatedResponse<Book> = await bookApi.list(params);
      setBooks(data.results);
      setTotal(data.count);
      setHasMore(!!data.next);
    } catch (err) {
      setError('Failed to fetch books');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.page, setBooks, setLoading, setError, setTotal, setHasMore]);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  useEffect(() => {
    const loadSources = async () => {
      try {
        const sources = await sourcesApi.list();
        setAvailableSources(sources);
      } catch (err) {
        console.error('Failed to load sources:', err);
      }
    };
    loadSources();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchBooks();
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ [key]: value });
    setPage(1);
  };

  const handleBookClick = (book: Book) => {
    router.push(`/books/${book.id}`);
  };

  const handleLoadSamples = async () => {
    setLoadingSamples(true);
    try {
      await bookApi.loadSamples();
      await fetchBooks();
    } catch (err) {
      console.error('Failed to load samples:', err);
    } finally {
      setLoadingSamples(false);
    }
  };

  const handleScrape = async () => {
    setScrapeLoading(true);
    try {
      const result = await scrapingApi.start({
        source: scrapeSource,
        url: scrapeUrl || `https://example.com/search?q=fiction`,
        max_books: scrapeMaxBooks,
        async_mode: false,
      });
      
      setScrapeJob({
        id: result.job_id,
        source: scrapeSource,
        url: scrapeUrl || '',
        status: result.status as 'pending' | 'running' | 'completed' | 'failed',
        books_scraped: result.total_collected,
        created_at: new Date().toISOString(),
      });
      await fetchBooks();
    } catch (err) {
      console.error('Scraping failed:', err);
    } finally {
      setScrapeLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadTitle) formData.append('title', uploadTitle);
      if (uploadAuthor) formData.append('author', uploadAuthor);

      await bookApi.upload(formData);
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle('');
      setUploadAuthor('');
      await fetchBooks();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploadLoading(false);
    }
  };

  const clearFilters = () => {
    setFilters({ search: '', genre: '', source: '' });
    setPage(1);
  };

  const hasActiveFilters = filters.search || filters.genre || filters.source;

  return (
    <div className="min-h-screen bg-cream-50">
      <div className="bg-white border-b border-cream-200 sticky top-0 z-20 shadow-elegant">
        <div className="mx-auto max-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-900">
                <Library className="h-5 w-5 text-gold-400" />
              </div>
              <h1 className="font-serif text-2xl font-bold text-obsidian-800">Book Library</h1>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowScrapeModal(true)}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Scrape Books
              </Button>
              <Button
                variant="gold"
                size="sm"
                onClick={() => setShowUploadModal(true)}
                icon={<Upload className="h-4 w-4" />}
              >
                Upload Book
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between mb-8">
          <form onSubmit={handleSearch} className="flex-1 max-w-xl">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-obsidian-400" />
              <input
                type="text"
                placeholder="Search by title, author, or description..."
                value={filters.search}
                onChange={(e) => setFilters({ search: e.target.value })}
                className="input-field pl-12"
              />
            </div>
          </form>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 transition-all ${
                showFilters || hasActiveFilters
                  ? 'border-gold-500 bg-gold-50 text-gold-700'
                  : 'border-obsidian-200 bg-white text-obsidian-700 hover:border-obsidian-300'
              }`}
            >
              <Filter className="h-4 w-4" />
              <span className="font-medium">Filters</span>
            </button>

            <div className="flex items-center border-2 border-obsidian-200 rounded-xl overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2.5 transition-all ${
                  viewMode === 'grid'
                    ? 'bg-obsidian-900 text-white'
                    : 'bg-white text-obsidian-600 hover:bg-cream-50'
                }`}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2.5 transition-all ${
                  viewMode === 'list'
                    ? 'bg-obsidian-900 text-white'
                    : 'bg-white text-obsidian-600 hover:bg-cream-50'
                }`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {showFilters && (
          <div className="bg-white rounded-2xl border border-cream-200 p-6 mb-8 shadow-elegant animate-slide-up">
            <div className="grid gap-4 sm:grid-cols-3">
              <Select
                label="Genre"
                options={GENRES}
                value={filters.genre}
                onChange={(e) => handleFilterChange('genre', e.target.value)}
              />
              <Select
                label="Source"
                options={[
                  { value: '', label: 'All Sources' },
                  ...availableSources.map((s) => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) })),
                ]}
                value={filters.source}
                onChange={(e) => handleFilterChange('source', e.target.value)}
              />
              <Select
                label="Sort By"
                options={SORT_OPTIONS}
                value={filters.sort}
                onChange={(e) => handleFilterChange('sort', e.target.value)}
              />
            </div>
            {hasActiveFilters && (
              <div className="mt-5 flex justify-end">
                <Button variant="ghost" size="sm" onClick={clearFilters} icon={<X className="h-4 w-4" />}>
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
            <p className="text-red-600 font-medium">{error}</p>
            <Button variant="outline" className="mt-4" onClick={fetchBooks}>
              Try Again
            </Button>
          </div>
        ) : books.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-obsidian-200 bg-white p-16 text-center shadow-elegant">
            <div className="mx-auto h-16 w-16 rounded-2xl bg-cream-100 flex items-center justify-center mb-6">
              <BookOpen className="h-8 w-8 text-obsidian-400" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-obsidian-800">
              {hasActiveFilters ? 'No matching books' : 'Your library is empty'}
            </h3>
            <p className="mt-2 text-obsidian-500 max-w-md mx-auto">
              {hasActiveFilters
                ? 'Try adjusting your filters to find what you\'re looking for.'
                : 'Get started by loading sample books, scraping from the web, or uploading your own.'}
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              {hasActiveFilters ? (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              ) : (
                <>
                  <Button
                    variant="gold"
                    onClick={handleLoadSamples}
                    loading={loadingSamples}
                    icon={<BookOpen className="h-4 w-4" />}
                  >
                    Load Sample Books
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowScrapeModal(true)}
                    icon={<RefreshCw className="h-4 w-4" />}
                  >
                    Scrape Books
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowUploadModal(true)}
                    icon={<Upload className="h-4 w-4" />}
                  >
                    Upload Book
                  </Button>
                </>
              )}
            </div>
          </div>
        ) : (
          <>
            <div className="mb-6 text-sm text-obsidian-500 font-medium">
              Showing {books.length} of {pagination.total} books
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {books.map((book) => (
                <BookCard
                  key={book.id}
                  book={book}
                  onClick={() => handleBookClick(book)}
                />
              ))}
            </div>

            {pagination.hasMore && (
              <div className="mt-12 flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => {
                    setPage(pagination.page + 1);
                    fetchBooks();
                  }}
                  loading={isLoading}
                  icon={<RefreshCw className="h-4 w-4" />}
                >
                  Load More
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <Modal
        isOpen={showScrapeModal}
        onClose={() => {
          setShowScrapeModal(false);
          setScrapeJob(null);
        }}
        title="Scrape Books from Web"
        size="md"
      >
        {scrapeJob ? (
          <div className="text-center py-6">
            <div className="mx-auto h-14 w-14 rounded-2xl bg-green-100 flex items-center justify-center mb-4">
              <RefreshCw className="h-7 w-7 text-green-600" />
            </div>
            <h3 className="font-serif text-lg font-semibold text-obsidian-800">
              Scraping Complete!
            </h3>
            <p className="mt-2 text-sm text-obsidian-500">
              Found and processed {scrapeJob.books_scraped} books.
            </p>
            <Button
              className="mt-6"
              variant="gold"
              onClick={() => {
                setShowScrapeModal(false);
                setScrapeJob(null);
                fetchBooks();
              }}
            >
              Done
            </Button>
          </div>
        ) : (
          <div className="space-y-5">
            <Select
              label="Source"
              options={availableSources.map((s) => ({
                value: s,
                label: s.charAt(0).toUpperCase() + s.slice(1),
              }))}
              value={scrapeSource}
              onChange={(e) => setScrapeSource(e.target.value)}
            />
            <Input
              label="URL (optional)"
              placeholder="https://example.com/books"
              value={scrapeUrl}
              onChange={(e) => setScrapeUrl(e.target.value)}
            />
            <div>
              <label className="mb-2 block text-sm font-medium text-obsidian-700">
                Max Books: {scrapeMaxBooks}
              </label>
              <input
                type="range"
                min="5"
                max="100"
                value={scrapeMaxBooks}
                onChange={(e) => setScrapeMaxBooks(parseInt(e.target.value))}
                className="w-full accent-gold-500"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowScrapeModal(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleScrape} loading={scrapeLoading} variant="gold">
                Start Scraping
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setUploadFile(null);
          setUploadTitle('');
          setUploadAuthor('');
        }}
        title="Upload Book"
        size="md"
      >
        <div className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-obsidian-700">
              File (PDF, TXT, DOCX)
            </label>
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-obsidian-500 file:mr-4 file:py-3 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-gold-50 file:text-gold-700 hover:file:bg-gold-100"
            />
          </div>
          <Input
            label="Title (optional)"
            placeholder="Enter book title"
            value={uploadTitle}
            onChange={(e) => setUploadTitle(e.target.value)}
          />
          <Input
            label="Author (optional)"
            placeholder="Enter author name"
            value={uploadAuthor}
            onChange={(e) => setUploadAuthor(e.target.value)}
          />
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowUploadModal(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleUpload} loading={uploadLoading} variant="gold" disabled={!uploadFile}>
              Upload
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
