# Document Intelligence Platform Backend

Django REST Framework backend for the Document Intelligence Platform with AI/RAG integration.

## Features

- Book management (CRUD operations)
- AI-powered insights (summary, genre classification, sentiment analysis)
- RAG pipeline for question answering
- Web scraping automation with Selenium
- ChromaDB vector database integration
- Multiple LLM provider support (OpenAI, Anthropic, LM Studio)

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database and API settings
```

### 4. Set Up Database

Create a MySQL database:

```sql
CREATE DATABASE document_intelligence CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Start Server

```bash
python manage.py runserver
```

## API Endpoints

- `GET /api/books/` - List all books
- `GET /api/books/{id}/` - Get book details
- `POST /api/books/upload/` - Upload a book
- `POST /api/books/{id}/process/` - Generate AI insights
- `GET /api/books/{id}/recommendations/` - Get similar books
- `POST /api/qa/` - Ask a question
- `GET /api/conversations/{session_id}/` - Get chat history
- `POST /api/scrape/` - Scrape books from web
- `GET /api/health/` - Health check

## Configuration

Set the following environment variables in `.env`:

- `DEBUG` - Enable debug mode
- `SECRET_KEY` - Django secret key
- `DB_HOST` - MySQL host
- `DB_NAME` - MySQL database name
- `DB_USER` - MySQL user
- `DB_PASSWORD` - MySQL password
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `ANTHROPIC_API_KEY` - Anthropic API key (optional)
- `LM_STUDIO_URL` - LM Studio URL (default: http://localhost:1234/v1)
- `USE_LM_STUDIO` - Use LM Studio (default: True)

## LM Studio Setup

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Llama 2, Mistral)
3. Start the local server (click "Start Server" button)
4. The API will be available at `http://localhost:1234/v1`
