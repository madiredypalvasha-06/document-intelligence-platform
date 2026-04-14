export default async function DashboardPage() {
  let health = null;
  let stats = null;
  let featuredBooks: any[] = [];
  let recentBooks: any[] = [];
  
  try {
    const apiBase = 'http://localhost:8000/api';
    
    const [healthRes, statsRes, featuredRes, recentRes] = await Promise.all([
      fetch(`${apiBase}/health/`, { cache: 'no-store' }),
      fetch(`${apiBase}/books/stats/`, { cache: 'no-store' }),
      fetch(`${apiBase}/books/?featured=true&page=1`, { cache: 'no-store' }),
      fetch(`${apiBase}/books/?page=1&sort=-created_at`, { cache: 'no-store' })
    ]);
    
    health = await healthRes.json();
    stats = await statsRes.json();
    const featuredData = await featuredRes.json();
    const recentData = await recentRes.json();
    featuredBooks = featuredData.results || [];
    recentBooks = recentData.results || [];
  } catch (err) {
    console.error('Failed to fetch data:', err);
  }

  const avgRating = stats?.avg_rating ? parseFloat(stats.avg_rating).toFixed(1) : 'N/A';

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-obsidian-900 via-obsidian-800 to-obsidian-900 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-gold-500 rounded-full filter blur-3xl -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-gold-400 rounded-full filter blur-3xl translate-x-1/2 translate-y-1/2" />
        </div>
        <div className="relative mx-auto max-7xl px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full bg-gold-500/20 px-4 py-2 mb-6">
              <svg className="h-4 w-4 text-gold-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
              <span className="text-sm font-medium text-gold-300">AI-Powered Document Intelligence</span>
            </div>
            <h1 className="font-serif text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl">
              Document Intelligence
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-gold-600">Platform</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-obsidian-300">
              Transform your reading experience with AI-powered book analysis,
              intelligent Q&A, and personalized recommendations.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <a href="/books" className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-gold-500 to-gold-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-gold-500/30 hover:from-gold-600 hover:to-gold-700">
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Explore Books
              </a>
              <a href="/qa" className="inline-flex items-center gap-2 rounded-lg bg-white/10 backdrop-blur px-6 py-3 text-base font-semibold text-white border border-white/20 hover:bg-white/20">
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Ask Questions
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-12">
            {/* Featured Books */}
            <section>
              <div className="mb-8 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-100">
                    <svg className="h-5 w-5 text-gold-600" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </div>
                  <h2 className="font-serif text-2xl font-bold text-obsidian-800">Featured Books</h2>
                </div>
                <a href="/books" className="inline-flex items-center gap-1 text-sm font-medium text-gold-600 hover:text-gold-700">
                  View all
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>

              {featuredBooks.length > 0 ? (
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {featuredBooks.map((book) => (
                    <a key={book.id} href={`/books/${book.id}`} className="group bg-white rounded-2xl overflow-hidden border border-cream-200 hover:shadow-lg hover:border-gold-200 transition-all">
                      <div className="p-5">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-serif text-lg font-semibold text-obsidian-800 line-clamp-2 group-hover:text-gold-600">{book.title}</h3>
                          {book.is_featured && (
                            <span className="flex-shrink-0 rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-3 py-1 text-xs font-medium text-white">Featured</span>
                          )}
                        </div>
                        <p className="mt-1.5 text-sm text-obsidian-500">{book.author}</p>
                        <span className="mt-3 inline-flex items-center rounded-full bg-obsidian-100 px-3 py-1 text-xs font-medium text-obsidian-700 capitalize">{book.genre}</span>
                        {book.rating && (
                          <div className="mt-3 flex items-center gap-1.5 text-sm">
                            <svg className="h-4 w-4 text-gold-500" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                            </svg>
                            <span className="font-semibold text-obsidian-800">{parseFloat(book.rating).toFixed(1)}</span>
                          </div>
                        )}
                      </div>
                      <div className="h-1 w-full bg-gradient-to-r from-gold-400 to-gold-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border-2 border-dashed border-obsidian-200 bg-white p-12 text-center">
                  <svg className="mx-auto h-14 w-14 text-obsidian-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                  </svg>
                  <h3 className="mt-4 font-serif text-lg font-medium text-obsidian-800">No featured books yet</h3>
                  <p className="mt-2 text-sm text-obsidian-500">Load sample books to get started.</p>
                  <a href="/books" className="mt-6 inline-block px-6 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-white rounded-lg font-medium hover:from-gold-600 hover:to-gold-700">
                    Browse Books
                  </a>
                </div>
              )}
            </section>

            {/* Recent Books */}
            <section>
              <div className="mb-8 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-100">
                    <svg className="h-5 w-5 text-obsidian-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h2 className="font-serif text-2xl font-bold text-obsidian-800">Recently Added</h2>
                </div>
                <a href="/books" className="inline-flex items-center gap-1 text-sm font-medium text-gold-600 hover:text-gold-700">
                  View all
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>

              {recentBooks.length > 0 ? (
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {recentBooks.slice(0, 6).map((book) => (
                    <a key={book.id} href={`/books/${book.id}`} className="group bg-white rounded-2xl overflow-hidden border border-cream-200 hover:shadow-lg hover:border-gold-200 transition-all">
                      <div className="p-5">
                        <h3 className="font-serif text-lg font-semibold text-obsidian-800 line-clamp-2 group-hover:text-gold-600">{book.title}</h3>
                        <p className="mt-1.5 text-sm text-obsidian-500">{book.author}</p>
                        <span className="mt-3 inline-flex items-center rounded-full bg-obsidian-100 px-3 py-1 text-xs font-medium text-obsidian-700 capitalize">{book.genre}</span>
                        {book.rating && (
                          <div className="mt-3 flex items-center gap-1.5 text-sm">
                            <svg className="h-4 w-4 text-gold-500" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                            </svg>
                            <span className="font-semibold text-obsidian-800">{parseFloat(book.rating).toFixed(1)}</span>
                          </div>
                        )}
                      </div>
                      <div className="h-1 w-full bg-gradient-to-r from-gold-400 to-gold-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border-2 border-dashed border-obsidian-200 bg-white p-12 text-center">
                  <svg className="mx-auto h-14 w-14 text-obsidian-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  <h3 className="mt-4 font-serif text-lg font-medium text-obsidian-800">Your library is empty</h3>
                  <a href="/books" className="mt-6 inline-block px-6 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-white rounded-lg font-medium hover:from-gold-600 hover:to-gold-700">
                    Browse Books
                  </a>
                </div>
              )}
            </section>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <div className="bg-white rounded-2xl shadow-sm border border-cream-200 p-6">
              <h3 className="font-serif text-lg font-semibold text-obsidian-800 mb-6 flex items-center gap-2">
                <svg className="h-5 w-5 text-gold-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Platform Statistics
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-cream-50">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-900">
                      <svg className="h-5 w-5 text-gold-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <span className="text-sm text-obsidian-600">Total Books</span>
                  </div>
                  <span className="text-xl font-bold text-obsidian-800">{stats?.total_books || 0}</span>
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-cream-50">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100">
                      <svg className="h-5 w-5 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                    <span className="text-sm text-obsidian-600">Processed</span>
                  </div>
                  <span className="text-xl font-bold text-green-600">{stats?.processed_books || 0}</span>
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-cream-50">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-100">
                      <svg className="h-5 w-5 text-gold-600" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                    </div>
                    <span className="text-sm text-obsidian-600">Avg Rating</span>
                  </div>
                  <span className="text-xl font-bold text-gold-600">{avgRating}</span>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-2xl shadow-sm border border-cream-200 p-6">
              <h3 className="font-serif text-lg font-semibold text-obsidian-800 mb-6 flex items-center gap-2">
                <svg className="h-5 w-5 text-gold-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                System Status
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-cream-50">
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${health?.database ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm text-obsidian-600">Database</span>
                  </div>
                  <span className={`text-sm font-semibold ${health?.database ? 'text-green-600' : 'text-red-600'}`}>
                    {health?.database ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-cream-50">
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${health?.chromadb ? 'bg-green-500' : 'bg-amber-500'}`} />
                    <span className="text-sm text-obsidian-600">Vector DB</span>
                  </div>
                  <span className={`text-sm font-semibold ${health?.chromadb ? 'text-green-600' : 'text-amber-600'}`}>
                    {health?.chromadb ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-cream-50">
                  <span className="text-sm text-obsidian-600">Embedding</span>
                  <span className="text-sm font-medium text-obsidian-700">{health?.embedding_model || 'Unknown'}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-gold-50 via-white to-cream-50 rounded-2xl border border-gold-200 p-6">
              <h3 className="font-serif text-lg font-semibold text-obsidian-800 mb-2">Quick Actions</h3>
              <p className="text-sm text-obsidian-500 mb-5">Get started with common tasks</p>
              <div className="space-y-3">
                <a href="/qa" className="flex items-center gap-4 rounded-xl bg-white p-4 text-sm font-medium text-obsidian-700 shadow-sm hover:shadow-md transition-all group">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-100 group-hover:bg-gold-500 transition-colors">
                    <svg className="h-5 w-5 text-gold-600 group-hover:text-white transition-colors" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  Ask a question about a book
                </a>
                <a href="/books" className="flex items-center gap-4 rounded-xl bg-white p-4 text-sm font-medium text-obsidian-700 shadow-sm hover:shadow-md transition-all group">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-obsidian-100 group-hover:bg-obsidian-800 transition-colors">
                    <svg className="h-5 w-5 text-obsidian-600 group-hover:text-white transition-colors" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  Browse the book library
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
