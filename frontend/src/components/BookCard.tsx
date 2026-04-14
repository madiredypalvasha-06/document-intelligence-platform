'use client';

import React from 'react';
import Link from 'next/link';
import { BookOpen, Star, ExternalLink } from 'lucide-react';
import { cn, formatRating, truncate } from '@/lib/utils';
import type { Book } from '@/types';

interface BookCardProps {
  book: Book;
  onClick?: () => void;
}

export function BookCard({ book, onClick }: BookCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'group relative bg-white rounded-2xl overflow-hidden border border-cream-200',
        'hover:shadow-elegant-lg hover:border-gold-200 transition-all duration-500',
        'cursor-pointer'
      )}
    >
      <div className="flex gap-5 p-5">
        {book.cover_image_url ? (
          <div className="relative h-40 w-28 flex-shrink-0 overflow-hidden rounded-xl bg-cream-100 shadow-elegant">
            <img
              src={book.cover_image_url}
              alt={book.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-obsidian-900/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          </div>
        ) : (
          <div className="flex h-40 w-28 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cream-100 to-cream-200 shadow-elegant">
            <BookOpen className="h-10 w-10 text-obsidian-400" />
          </div>
        )}

        <div className="flex flex-1 flex-col justify-between">
          <div>
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-serif text-lg font-semibold text-obsidian-800 line-clamp-2 group-hover:text-gold-600 transition-colors duration-300">
                {book.title}
              </h3>
              {book.is_featured && (
                <span className="flex-shrink-0 rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-3 py-1 text-xs font-medium text-white shadow-gold">
                  Featured
                </span>
              )}
            </div>

            <p className="mt-1.5 text-sm text-obsidian-500 font-medium">{book.author}</p>

            <div className="mt-3 flex items-center gap-3">
              <span className="inline-flex items-center rounded-full bg-obsidian-100 px-3 py-1 text-xs font-medium text-obsidian-700 capitalize">
                {book.genre}
              </span>

              {book.rating && (
                <div className="flex items-center gap-1.5 text-sm">
                  <Star className="h-4 w-4 text-gold-500 fill-gold-500" />
                  <span className="font-semibold text-obsidian-800">
                    {formatRating(book.rating)}
                  </span>
                  {book.num_ratings !== undefined && (
                    <span className="text-obsidian-400">({book.num_ratings})</span>
                  )}
                </div>
              )}
            </div>

            {book.description && (
              <p className="mt-3 text-sm text-obsidian-500 line-clamp-2 leading-relaxed">
                {truncate(book.description, 100)}
              </p>
            )}
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              {book.is_processed && (
                <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700 border border-green-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  AI Processed
                </span>
              )}
              {book.source && (
                <span className="text-xs text-obsidian-400 capitalize">
                  via {book.source}
                </span>
              )}
            </div>

            {book.book_url && (
              <a
                href={book.book_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-1 text-xs font-medium text-gold-600 hover:text-gold-700 transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                View
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="h-1 w-full bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    </div>
  );
}

interface BookGridProps {
  books: Book[];
  onBookClick?: (book: Book) => void;
  loading?: boolean;
}

export function BookGrid({ books, onBookClick, loading }: BookGridProps) {
  if (loading) {
    return (
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="animate-pulse bg-white rounded-2xl border border-cream-200 p-5"
          >
            <div className="flex gap-5">
              <div className="h-40 w-28 rounded-xl bg-cream-200" />
              <div className="flex-1 space-y-4">
                <div className="h-6 w-3/4 rounded bg-cream-200" />
                <div className="h-4 w-1/2 rounded bg-cream-200" />
                <div className="h-4 w-full rounded bg-cream-200" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-cream-100 mb-6">
          <BookOpen className="h-10 w-10 text-obsidian-400" />
        </div>
        <h3 className="font-serif text-xl font-semibold text-obsidian-800">No books found</h3>
        <p className="mt-2 text-sm text-obsidian-500 max-w-md">
          Try adjusting your filters or add some books to get started.
        </p>
        <Link
          href="/books"
          className="mt-6 btn-primary"
        >
          Browse Books
        </Link>
      </div>
    );
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {books.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          onClick={() => onBookClick?.(book)}
        />
      ))}
    </div>
  );
}
