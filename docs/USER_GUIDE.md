# Document Intelligence Platform - Complete User Guide

![Document Intelligence Platform](images/platform-banner.png)

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Application Walkthrough](#application-walkthrough)
4. [Features Explained](#features-explained)
5. [LM Studio Setup](#lm-studio-setup)
6. [Troubleshooting](#troubleshooting)
7. [API Documentation](#api-documentation)

---

## Overview

The **Document Intelligence Platform** is a full-stack web application that combines:
- **Book Management**: Upload, scrape, and organize your book collection
- **AI-Powered Analysis**: Generate summaries, classify genres, analyze sentiments
- **RAG-Powered Q&A**: Ask questions about books and get contextual answers
- **Smart Recommendations**: Discover similar books based on content analysis

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) LM Studio for AI features

### Option 1: Docker (Recommended)

```bash
# From project root
cd /Users/palvashamadireddy/document-intelligence-platform
docker-compose up --build
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/

### Option 2: Manual Setup

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Application Walkthrough

### 1. Dashboard (Home Page)

The dashboard provides an overview of your library:

**Components:**
- **Hero Section**: Welcome message with quick action buttons
- **Featured Books**: Highlighted books marked as featured
- **Recently Added**: Latest additions to your library
- **Platform Statistics**: Total books, processed count, average rating
- **System Status**: Database and Vector DB connection status

**Quick Actions:**
- Click "Explore Books" to browse the library
- Click "Ask Questions" to start the Q&A interface

---

### 2. Book Library Page

The book library allows you to manage your entire collection.

**Features:**

#### Search & Filter
- **Search Bar**: Find books by title, author, or description
- **Genre Filter**: Filter by fiction, mystery, sci-fi, etc.
- **Source Filter**: Filter by scraping source (Goodreads, etc.)
- **Sort Options**: Newest, highest rated, alphabetical

#### Add Books

**Option A: Web Scraping**
1. Click "Scrape Books" button
2. Select source (Goodreads, Amazon, Open Library)
3. Optionally enter a URL
4. Set max books to scrape
5. Click "Start Scraping"

**Option B: Upload**
1. Click "Upload Book" button
2. Select file (PDF, TXT, DOCX)
3. Optionally add title and author
4. Click "Upload"

#### Book Cards
Each book displays:
- Cover image (or placeholder)
- Title and author
- Genre badge
- Rating with count
- AI Processed badge (if processed)
- Source indicator

---

### 3. Book Detail Page

Click on any book card to view detailed information.

**Tabs:**

#### Overview Tab
- Full book description
- Publisher, published date, page count
- ISBN, language
- Tags
- Summary (if AI processed)

#### Chunks Tab
- Content chunks for RAG processing
- Each chunk shows content preview
- Chunk type indicator (semantic, recursive, etc.)

#### Reviews Tab
- User reviews (if scraped)
- Sentiment analysis per review
- Star ratings

**AI Insights Panel:**
- **Summary**: Auto-generated book summary
- **Genre Analysis**: Primary and secondary genres with confidence
- **Sentiment Analysis**: Overall tone of reviews

**Actions:**
- "Ask Questions" → Opens Q&A with this book selected
- "Generate AI Insights" → Processes the book with AI
- "View Source" → Opens original book URL

---

### 4. Q&A Assistant Page

The AI-powered question answering interface.

**Components:**

#### Configuration Panel
- **Book Selector**: Choose a specific book or ask generically
- **AI Model**: Select between LM Studio, OpenAI, or Anthropic
- **RAG Toggle**: Enable/disable retrieval-augmented generation

#### Chat Interface
- **Question Input**: Type your question
- **Send Button**: Submit question
- **Sample Questions**: Quick-start prompts

#### Response Display
- **Answer**: AI-generated response
- **Sources**: Relevant passages with relevance scores
- **Metadata**: Model used, response time, chunks retrieved

**Example Questions:**
1. "What is the main theme of this book?"
2. "Give me a brief summary of the plot"
3. "Who would enjoy reading this book?"
4. "What are the key takeaways?"
5. "How does this compare to similar works?"

---

## Features Explained

### 1. Web Scraping

The scraper automatically collects book data from:
- **Goodreads**: Reviews, ratings, descriptions
- **Amazon**: Pricing, categories, metadata
- **Open Library**: Detailed bibliographic data

**Process:**
1. Selenium navigates to the target URL
2. BeautifulSoup parses HTML content
3. Data is cleaned and normalized
4. Books are saved to database
5. Optionally auto-generate embeddings

### 2. AI Insights Generation

When you click "Generate AI Insights", the system:

1. **Summary Generation**: Creates a concise summary
2. **Genre Classification**: Predicts primary and secondary genres
3. **Sentiment Analysis**: Analyzes review tone
4. **Content Chunking**: Creates searchable chunks

**Insight Types:**
| Type | Description |
|------|-------------|
| Summary | Brief overview of the book |
| Genre Analysis | Classification with confidence score |
| Sentiment | Review tone (positive/negative/neutral) |

### 3. RAG Pipeline

Retrieval-Augmented Generation combines:
1. **Embedding Generation**: Converting text to vectors
2. **Vector Storage**: ChromaDB for similarity search
3. **Context Retrieval**: Finding relevant passages
4. **Answer Generation**: LLM creates contextual answers

**Benefits:**
- Answers grounded in actual book content
- Source citations for verification
- Better accuracy than general LLM responses

### 4. Smart Chunking

Multiple chunking strategies:
- **Semantic**: Groups by paragraphs and sections
- **Recursive**: Multiple delimiter passes
- **Paragraph**: By line breaks
- **Sentence**: Sentence-by-sentence with overlap

---

## LM Studio Setup

For local AI processing (recommended for this assignment):

### 1. Download LM Studio
Visit https://lmstudio.ai/ and download the application.

### 2. Download a Model
1. Open LM Studio
2. Go to "Search" tab
3. Search for "Llama 2" or "Mistral"
4. Download a 7B or 13B parameter model
5. Adjust quantization (Q4_K_M recommended)

### 3. Start Local Server
1. Go to "Local Server" tab
2. Click "Start Server"
3. Server runs at `http://localhost:1234/v1`

### 4. Verify Connection
The backend will automatically detect LM Studio. Check the System Status on the dashboard - Vector DB and LLM should show as active.

---

## Troubleshooting

### Database Connection Error
```
MySQLdb.OperationalError: (2002, "Can't connect...")
```
**Solution:** The app now uses SQLite by default. Make sure `USE_MYSQL=False` in your `.env` file.

### ChromaDB Initialization Failed
```
'Settings' object has no attribute 'CHORMA_DB_PATH'
```
**Solution:** Run migrations again. The settings have been fixed.

### Frontend Not Loading
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### API Returns 404
Make sure the backend is running on port 8000:
```bash
cd backend
python manage.py runserver
```

### LM Studio Not Connecting
1. Ensure LM Studio server is running
2. Check the URL in `.env`: `LM_STUDIO_URL=http://localhost:1234/v1`
3. Verify no firewall blocking port 1234

### Scraping Fails
Selenium requires Chrome. On macOS:
```bash
brew install --cask google-chrome
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Books

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books/` | List all books |
| GET | `/books/{id}/` | Get book details |
| POST | `/books/` | Create book |
| POST | `/books/upload/` | Upload book file |
| POST | `/books/{id}/process/` | Generate AI insights |
| GET | `/books/{id}/recommendations/` | Similar books |
| GET | `/books/{id}/chunks/` | Get content chunks |
| GET | `/books/stats/` | Platform statistics |

### Q&A

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/qa/` | Ask a question |
| GET | `/conversations/{session_id}/` | Get chat history |

### Scraping

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scrape/` | Start scraping job |
| GET | `/scrape/` | Get job status |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Health check |
| GET | `/sources/` | Available sources |

### Example API Calls

**List Books:**
```bash
curl http://localhost:8000/api/books/
```

**Ask Question:**
```bash
curl -X POST http://localhost:8000/api/qa/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main theme?",
    "book_id": 1,
    "use_rag": true
  }'
```

**Upload Book:**
```bash
curl -X POST http://localhost:8000/api/books/upload/ \
  -F "file=@book.pdf" \
  -F "title=My Book"
```

**Scrape Books:**
```bash
curl -X POST http://localhost:8000/api/scrape/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "goodreads",
    "max_books": 20
  }'
```

---

## Project Structure

```
document-intelligence-platform/
├── backend/
│   ├── books/
│   │   ├── models.py       # Database models
│   │   ├── views.py        # API endpoints
│   │   ├── serializers.py  # DRF serializers
│   │   ├── ai_services.py  # LLM & embeddings
│   │   ├── rag_pipeline.py # RAG implementation
│   │   └── scraper.py      # Web scraping
│   ├── config/
│   │   └── settings.py     # Django settings
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   ├── lib/            # API client
│   │   └── store/          # Zustand stores
│   └── package.json
└── docker-compose.yml
```

---

## Color Theme

The application uses a professional **Gold, Cream, Black & White** theme:

| Color | Hex | Usage |
|-------|-----|-------|
| Gold 500 | `#d4821f` | Primary accent, buttons |
| Gold 400 | `#df9a4a` | Hover states, highlights |
| Cream 50 | `#fefef9` | Background |
| Cream 100 | `#fcf9ed` | Card backgrounds |
| Obsidian 800 | `#3d3d3d` | Primary text |
| Obsidian 900 | `#1a1a1a` | Dark backgrounds |
| White | `#ffffff` | Cards, inputs |

---

## Credits

Built for the Document Intelligence Platform assignment using:
- Django REST Framework
- Next.js 14
- Tailwind CSS
- ChromaDB
- Sentence Transformers
- LM Studio / OpenAI / Anthropic
