# Document Intelligence Platform

![Platform Banner](docs/images/banner.png)

A full-stack web application with AI/RAG integration for processing book data and enabling intelligent querying. Features include book management, AI-powered insights (summaries, genre classification, sentiment analysis), an intelligent Q&A system, book recommendations, and web scraping capabilities.

---

## Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)
*The main dashboard displays platform statistics, featured books, and system health status.*

### Book Library
![Book Library](docs/images/books.png)
*Browse, search, and filter your book collection with beautiful card-based layouts.*

### Book Detail
![Book Detail](docs/images/book-detail.png)
*View detailed book information including AI-generated insights, price, and recommendations.*

### Q&A Interface
![Q&A Interface](docs/images/qa.png)
*Ask questions about books and get contextual, AI-powered answers.*

---

## Features

- **Book Management**: Upload, scrape, and manage book collections
- **AI-Powered Insights**: Generate summaries, genre classification, sentiment analysis
- **RAG Pipeline**: Question-answering over book content with source citations
- **Book Recommendations**: AI-driven similar book suggestions
- **Web Scraping**: Automated book data collection from Goodreads, Amazon, Open Library
- **Modern UI**: Professional gold, cream, black and white themed interface

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Django REST Framework | REST API backend |
| SQLite | Primary database (MySQL supported) |
| ChromaDB | Vector database for embeddings |
| Selenium | Web scraping automation |
| Sentence Transformers | Embedding generation |
| LM Studio | Local LLM (no API costs) |

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework with App Router |
| Tailwind CSS | Professional gold/cream theme |
| Zustand | State management |
| React Hot Toast | Notifications |

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/madiredypalvasha-06/document-intelligence-platform.git
cd document-intelligence-platform

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## LM Studio Setup (Recommended)

For AI features without external API costs:

1. Download [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Llama 2, Mistral, Phi-2)
3. Start the local server (click "Start Server" in LM Studio)
4. The platform will automatically connect to `http://localhost:1234`

---

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Books API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books/` | List all books (paginated) |
| GET | `/books/{id}/` | Get book details |
| POST | `/books/upload/` | Upload a book |
| POST | `/books/{id}/process/` | Generate AI insights |
| GET | `/books/{id}/recommendations/` | Similar books |
| GET | `/books/stats/` | Platform statistics |

### Q&A API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/qa/` | Ask a question |
| GET | `/conversations/{session_id}/` | Chat history |

### Scraping API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scrape/` | Start scraping job |
| GET | `/scrape/` | List scraping jobs |

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/favorites/` | User favorites |
| POST | `/rate/` | Rate a book |
| GET | `/search/suggestions/` | Search suggestions |
| GET | `/export/` | Export books (JSON/CSV) |
| GET | `/health/` | System health check |

### Example API Calls

```bash
# Get all books
curl http://localhost:8000/api/books/

# Get specific book
curl http://localhost:8000/api/books/1/

# Ask a question
curl -X POST http://localhost:8000/api/qa/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the genre?", "book_id": 1}'

# Start scraping
curl -X POST http://localhost:8000/api/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"source": "goodreads", "max_books": 10}'
```

---

## Sample Questions and Answers

The Q&A system can answer various questions about books. Here are examples:

### Genre Classification
**Q:** "What genre is this book?"
**A:** Returns the primary genre and related genres based on content analysis.

### Price Information
**Q:** "How much does this book cost?"
**A:** Returns the current price from the database.

### Book Summary
**Q:** "Give me a brief summary of the plot"
**A:** Returns an AI-generated summary from the book's insights.

### Author Information
**Q:** "Who is the author?"
**A:** Returns the author's name with proper formatting.

### Similar Books
**Q:** "What books would you recommend?"
**A:** Returns similar books based on genre, themes, and content.

### Example API Response

```json
{
  "answer": "# The Great Gatsby\n\n## Summary\nA novel set in the Jazz Age that examines the American Dream through the lens of wealth, love, and tragedy.\n\n## Genre\n**Primary Genre:** Literary Fiction\n**Key Themes:** American Dream, wealth, love",
  "sources": [],
  "session_id": "session_1234567890",
  "retrieved_chunks": 0,
  "confidence": 1.0,
  "model_used": "lm-studio",
  "response_time": 0.45,
  "cached": false
}
```

---

## Project Structure

```
document-intelligence-platform/
├── backend/
│   ├── books/
│   │   ├── models.py          # Database models (Book, Review, etc.)
│   │   ├── views.py           # API endpoints
│   │   ├── serializers.py     # DRF serializers
│   │   ├── ai_services.py     # AI/LLM integration
│   │   ├── rag_pipeline.py    # RAG implementation
│   │   ├── scraper.py         # Web scraping
│   │   └── middleware.py       # Rate limiting
│   ├── config/                 # Django settings
│   ├── tests/                  # Unit tests
│   ├── requirements.txt        # Python dependencies
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   ├── components/         # React components
│   │   ├── lib/               # API client
│   │   └── store/             # Zustand store
│   ├── package.json
│   └── tailwind.config.js
├── docs/
│   └── USER_GUIDE.md          # Complete user guide
├── docker-compose.yml
└── README.md
```

---

## Color Theme

Professional Gold, Cream, Black & White:

| Color | Hex | Usage |
|-------|-----|-------|
| Gold | `#d4821f` | Primary accent |
| Light Gold | `#e6a54a` | Hover states |
| Cream | `#fefef9` | Background |
| Warm Cream | `#fcf9ed` | Cards |
| Obsidian | `#1a1a1a` | Primary text |
| Charcoal | `#3d3d3d` | Secondary text |
| White | `#ffffff` | Content areas |

---

## Adding Screenshots

Place your screenshots in `docs/images/` with these names:
- `dashboard.png` - Dashboard page screenshot
- `books.png` - Book library page screenshot
- `book-detail.png` - Book detail page screenshot
- `qa.png` - Q&A interface screenshot

---

## Documentation

For detailed instructions, see [USER_GUIDE.md](docs/USER_GUIDE.md).

---

## License

MIT License - feel free to use this project for personal or commercial purposes.
