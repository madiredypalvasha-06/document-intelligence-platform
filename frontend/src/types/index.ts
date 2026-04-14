export interface Book {
  id: number;
  title: string;
  author: string;
  description?: string;
  summary?: string;
  genre: string;
  isbn?: string;
  publisher?: string;
  published_date?: string;
  page_count?: number;
  rating?: number | string;
  num_ratings?: number;
  num_reviews?: number;
  cover_image_url?: string;
  book_url?: string;
  source?: string;
  price?: string;
  language?: string;
  tags: string[];
  ai_insights: AIInsights;
  is_processed: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
  reviews?: Review[];
  similar_books?: Book[];
}

export interface Review {
  id: number;
  book?: number;
  reviewer_name?: string;
  rating: number;
  title?: string;
  content: string;
  sentiment_score?: number;
  sentiment_label?: string;
  created_at: string;
  source?: string;
}

export interface AIInsights {
  summary?: string;
  genre_analysis?: {
    primary_genre: string;
    secondary_genres: string[];
    confidence: number;
    indicators: string[];
  };
  review_sentiment?: {
    sentiment_score: number;
    sentiment_label: string;
    confidence: number;
    key_phrases: string[];
    tone: string;
  };
  generated_at?: number;
}

export interface QARequest {
  question: string;
  book_id?: number;
  session_id?: string;
  use_rag?: boolean;
  model?: 'openai' | 'anthropic' | 'lm-studio';
}

export interface QAResponse {
  answer: string;
  sources: Source[];
  session_id: string;
  conversation_id: number;
  retrieved_chunks: number;
  confidence: number;
  model_used: string;
  response_time: number;
}

export interface Source {
  book_id: number;
  book_title: string;
  content_preview: string;
  relevance_score: number;
  chunk_type: string;
}

export interface Conversation {
  id: number;
  session_id: string;
  book?: number;
  book_title?: string;
  question: string;
  answer: string;
  sources: Source[];
  model_used: string;
  response_time: number;
  retrieved_chunks?: number;
  created_at: string;
}

export interface ScrapingJob {
  id: number;
  source: string;
  url: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  books_scraped: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface BookStats {
  total_books: number;
  processed_books: number;
  genre_distribution: { genre: string; count: number }[];
  avg_rating: number;
}

export interface HealthStatus {
  status: string;
  database: boolean;
  chromadb: boolean;
  embedding_model: string;
  llm_available: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}
