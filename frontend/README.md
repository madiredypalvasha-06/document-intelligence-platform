# Document Intelligence Platform - Frontend

Next.js 14 frontend for the Document Intelligence Platform.

## Features

- Responsive UI with Tailwind CSS
- Book listing and search
- AI-powered Q&A interface
- Book detail pages with AI insights
- Real-time chat interface
- State management with Zustand

## Getting Started

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm start
```

## Configuration

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Project Structure

```
frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utilities and API client
│   ├── store/         # Zustand state stores
│   └── types/         # TypeScript types
├── public/            # Static assets
└── package.json
```

## Pages

- `/` - Dashboard with featured books and statistics
- `/books` - Book library with search and filters
- `/books/[id]` - Book detail page with AI insights
- `/qa` - Q&A chat interface
