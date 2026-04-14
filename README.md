# Document Intelligence Platform

A full-stack web application with AI/RAG integration for processing book data and enabling intelligent querying.

![Document Intelligence Platform](docs/images/dashboard.png)

## Features

- **Book Management**: Upload, scrape, and manage book collections
- **AI-Powered Insights**: Generate summaries, genre classification, sentiment analysis
- **RAG Pipeline**: Question-answering over book content with source citations
- **Book Recommendations**: AI-driven similar book suggestions
- **Web Scraping**: Automated book data collection from Goodreads, Amazon, Open Library
- **Modern UI**: Professional gold, cream, black and white themed interface

## Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)
The main dashboard shows platform statistics, featured books, and system status.

### Book Library
![Book Library](docs/images/books.png)
Browse, search, and filter your book collection.

### Book Detail
![Book Detail](docs/images/book-detail.png)
View detailed information and AI-generated insights.

### Q&A Interface
![Q&A Interface](docs/images/qa.png)
Ask questions about books and get contextual answers.

## Tech Stack

### Backend
- **Django REST Framework** - REST API backend
- **SQLite** - Primary database (optional MySQL)
- **ChromaDB** - Vector database for embeddings
- **Selenium** - Web scraping automation
- **Sentence Transformers** - Embedding generation
- **LM Studio** - Local LLM (recommended)

### Frontend
- **Next.js 14** - React framework with App Router
- **Tailwind CSS** - Professional gold/cream theme
- **Zustand** - State management
- **React Hot Toast** - Notifications

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## LM Studio Setup (Recommended)

For AI features without external API costs:

1. Download [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Llama 2, Mistral)
3. Start the local server
4. The platform will automatically connect

## API Endpoints

### Books
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/books/` | List all books |
| GET | `/api/books/{id}/` | Get book details |
| POST | `/api/books/upload/` | Upload a book |
| POST | `/api/books/{id}/process/` | Generate AI insights |
| GET | `/api/books/{id}/recommendations/` | Similar books |

### Q&A
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/qa/` | Ask a question |
| GET | `/api/conversations/{session_id}/` | Chat history |

### Scraping
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scrape/` | Start scraping |
| GET | `/api/scrape/` | Job status |

## Sample Questions

1. "What is the main theme of this book?"
2. "Give me a brief summary of the plot"
3. "Who would enjoy reading this book?"
4. "What are the key takeaways?"
5. "How does this book compare to similar works?"

## Project Structure

```
document-intelligence-platform/
├── backend/
│   ├── books/
│   │   ├── models.py       # Database models
│   │   ├── views.py        # API endpoints
│   │   ├── ai_services.py  # AI/LLM integration
│   │   ├── rag_pipeline.py # RAG implementation
│   │   └── scraper.py      # Web scraping
│   └── config/             # Django settings
├── frontend/
│   ├── src/
│   │   ├── app/           # Pages
│   │   ├── components/    # UI components
│   │   ├── lib/           # API client
│   │   └── store/         # State management
│   └── package.json
├── docs/
│   └── USER_GUIDE.md      # Complete user guide
├── docker-compose.yml
└── README.md
```

## Color Theme

Professional Gold, Cream, Black & White:
- **Gold**: Primary accent (#d4821f)
- **Cream**: Background tones (#fefef9, #fcf9ed)
- **Obsidian**: Text and dark elements (#1a1a1a, #3d3d3d)
- **White**: Cards and content areas

## Documentation

For detailed instructions, see [USER_GUIDE.md](docs/USER_GUIDE.md).

## License

MIT License
