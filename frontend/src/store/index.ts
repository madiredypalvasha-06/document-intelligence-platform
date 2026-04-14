import { create } from 'zustand';
import type { Book, Conversation, BookStats, HealthStatus } from '@/types';

interface BookStore {
  books: Book[];
  selectedBook: Book | null;
  stats: BookStats | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    search: string;
    genre: string;
    source: string;
    sort: string;
  };
  pagination: {
    page: number;
    total: number;
    hasMore: boolean;
  };
  setBooks: (books: Book[]) => void;
  addBook: (book: Book) => void;
  updateBook: (id: number, updates: Partial<Book>) => void;
  removeBook: (id: number) => void;
  setSelectedBook: (book: Book | null) => void;
  setStats: (stats: BookStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<BookStore['filters']>) => void;
  setPage: (page: number) => void;
  setTotal: (total: number) => void;
  setHasMore: (hasMore: boolean) => void;
}

export const useBookStore = create<BookStore>((set) => ({
  books: [],
  selectedBook: null,
  stats: null,
  isLoading: false,
  error: null,
  filters: {
    search: '',
    genre: '',
    source: '',
    sort: '-created_at',
  },
  pagination: {
    page: 1,
    total: 0,
    hasMore: true,
  },
  setBooks: (books) => set({ books }),
  addBook: (book) => set((state) => ({ books: [book, ...state.books] })),
  updateBook: (id, updates) =>
    set((state) => ({
      books: state.books.map((b) => (b.id === id ? { ...b, ...updates } : b)),
      selectedBook:
        state.selectedBook?.id === id
          ? { ...state.selectedBook, ...updates }
          : state.selectedBook,
    })),
  removeBook: (id) =>
    set((state) => ({
      books: state.books.filter((b) => b.id !== id),
      selectedBook: state.selectedBook?.id === id ? null : state.selectedBook,
    })),
  setSelectedBook: (book) => set({ selectedBook: book }),
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
      pagination: { ...state.pagination, page: 1 },
    })),
  setPage: (page) =>
    set((state) => ({
      pagination: { ...state.pagination, page },
    })),
  setTotal: (total) =>
    set((state) => ({
      pagination: { ...state.pagination, total },
    })),
  setHasMore: (hasMore) =>
    set((state) => ({
      pagination: { ...state.pagination, hasMore },
    })),
}));

interface QAStore {
  conversations: Conversation[];
  currentSessionId: string;
  isLoading: boolean;
  error: string | null;
  addConversation: (conversation: Conversation) => void;
  setConversations: (conversations: Conversation[]) => void;
  setSessionId: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearConversations: () => void;
}

export const useQAStore = create<QAStore>((set) => ({
  conversations: [],
  currentSessionId: '',
  isLoading: false,
  error: null,
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [...state.conversations, conversation],
    })),
  setConversations: (conversations) => set({ conversations }),
  setSessionId: (sessionId) => set({ currentSessionId: sessionId }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearConversations: () => set({ conversations: [] }),
}));

interface AppStore {
  health: HealthStatus | null;
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  setHealth: (health: HealthStatus) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppStore>((set) => ({
  health: null,
  sidebarOpen: true,
  theme: 'light',
  setHealth: (health) => set({ health }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
}));
