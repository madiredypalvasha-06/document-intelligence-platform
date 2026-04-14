/**
 * API Client for Document Intelligence Platform
 * Handles all HTTP requests to the backend API
 */
import axios from 'axios';
import type {
  Book,
  Review,
  QARequest,
  QAResponse,
  Conversation,
  ScrapingJob,
  BookStats,
  HealthStatus,
  PaginatedResponse,
} from '@/types';

// Base URL for the backend API
const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 60000, // 60 second timeout for long-running requests
});

// Request interceptor - logs all outgoing requests
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - logs all responses and handles errors
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Book API - Endpoints for book operations
 */
export const bookApi = {
  /**
   * List all books with optional filtering
   * @param params - Query parameters for filtering and pagination
   */
  list: async (params?: {
    page?: number;
    search?: string;
    genre?: string;
    source?: string;
    featured?: boolean;
    sort?: string;
  }): Promise<PaginatedResponse<Book>> => {
    const { data } = await api.get('/books/', { params });
    return data;
  },

  /**
   * Get a single book by ID
   * @param id - Book ID
   */
  get: async (id: number): Promise<Book> => {
    const { data } = await api.get(`/books/${id}/`);
    return data;
  },

  create: async (book: Partial<Book>): Promise<Book> => {
    const { data } = await api.post('/books/', book);
    return data;
  },

  update: async (id: number, book: Partial<Book>): Promise<Book> => {
    const { data } = await api.patch(`/books/${id}/`, book);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/books/${id}/`);
  },

  process: async (id: number, background: boolean = false): Promise<{ 
    message: string; 
    chunks_created?: number; 
    ai_insights?: Book['ai_insights'];
    task_ids?: { insights: string; chunks: string };
    status?: string;
  }> => {
    const { data } = await api.post(`/books/${id}/process/`, { background });
    return data;
  },

  recommendations: async (id: number): Promise<Book[]> => {
    const { data } = await api.get(`/books/${id}/recommendations/`);
    return data;
  },

  chunks: async (id: number): Promise<{ id: number; chunk_index: number; content: string; chunk_type: string }[]> => {
    const { data } = await api.get(`/books/${id}/chunks/`);
    return data;
  },

  upload: async (formData: FormData): Promise<Book> => {
    const { data } = await api.post('/books/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  stats: async (): Promise<BookStats> => {
    const { data } = await api.get('/books/stats/');
    return data;
  },

  loadSamples: async (): Promise<{
    message: string;
    total_books: number;
    books: Book[];
  }> => {
    const { data } = await api.post('/books/load-samples/');
    return data;
  },
};

export const qaApi = {
  ask: async (request: QARequest): Promise<QAResponse> => {
    const { data } = await api.post('/qa/', request);
    return data;
  },

  getHistory: async (sessionId: string): Promise<Conversation[]> => {
    const { data } = await api.get(`/conversations/${sessionId}/`);
    return data;
  },
};

export const reviewApi = {
  list: async (params?: { book_id?: number }): Promise<PaginatedResponse<Review>> => {
    const { data } = await api.get('/reviews/', { params });
    return data;
  },

  create: async (review: Partial<Review>): Promise<Review> => {
    const { data } = await api.post('/reviews/', review);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/reviews/${id}/`);
  },
};

export const scrapingApi = {
  start: async (request: { source: string; url: string; max_books?: number; async_mode?: boolean }): Promise<{
    job_id: number;
    status: string;
    books_scraped: number;
    books: Book[];
  }> => {
    const { data } = await api.post('/scrape/', request);
    return data;
  },

  status: async (jobId?: number): Promise<ScrapingJob | ScrapingJob[]> => {
    const params = jobId ? { job_id: jobId } : {};
    const { data } = await api.get('/scrape/', { params });
    return data;
  },
};

export const recommendationsApi = {
  get: async (bookId: number, limit?: number): Promise<{
    source_book: Book;
    recommendations: { book: Book; reason: string; match_score: number }[];
  }> => {
    const { data } = await api.post('/recommendations/', { book_id: bookId, limit });
    return data;
  },
};

export const insightsApi = {
  generate: async (bookId: number, types?: string[]): Promise<{
    book_id: number;
    insights: Record<string, unknown>;
  }> => {
    const { data } = await api.post('/insights/generate/', { book_id: bookId, types });
    return data;
  },
};

export const healthApi = {
  check: async (): Promise<HealthStatus> => {
    const { data } = await api.get('/health/');
    return data;
  },
};

export const sourcesApi = {
  list: async (): Promise<string[]> => {
    const { data } = await api.get('/sources/');
    return data.sources;
  },
};

export const favoritesApi = {
  list: async (): Promise<{ id: number; book: Book; created_at: string }[]> => {
    const { data } = await api.get('/books/favorites/');
    return data;
  },
  
  add: async (bookId: number): Promise<{ message: string; favorite_id: number; book: Book }> => {
    const { data } = await api.post('/books/favorites/', { book_id: bookId });
    return data;
  },
  
  remove: async (bookId: number): Promise<{ message: string }> => {
    const { data } = await api.delete(`/books/favorites/${bookId}/`);
    return data;
  },
};

export const ratingApi = {
  rate: async (bookId: number, rating: number, review?: string): Promise<{
    message: string;
    review_id: number;
    new_average: number;
    total_reviews: number;
  }> => {
    const { data } = await api.post('/books/rate/', {
      book_id: bookId,
      rating,
      review,
    });
    return data;
  },
};

export const exportApi = {
  exportBooks: async (format: 'json' | 'csv' = 'json', includeInsights: boolean = true): Promise<Response> => {
    const url = `${API_BASE_URL}/books/export/?format=${format}&insights=${includeInsights}`;
    window.open(url, '_blank');
    return new Response('Exporting...');
  },
};

export const searchApi = {
  suggestions: async (query: string): Promise<{ suggestions: { type: string; text: string; author?: string; id: string | number }[] }> => {
    const { data } = await api.get('/books/search-suggestions/', { params: { q: query } });
    return data;
  },
};

export default api;
