"""
API Views for Document Intelligence Platform
"""
import os
import time
import logging
import hashlib
from typing import Optional, List, Dict

from django.shortcuts import render
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Review, BookChunk, QAConversation, BookRecommendation, ScrapingJob
from .serializers import (
    BookListSerializer, BookDetailSerializer, BookCreateSerializer,
    BookUploadSerializer, ReviewSerializer, BookChunkSerializer,
    QAConversationSerializer, QARequestSerializer, BookRecommendationSerializer,
    ScrapingJobSerializer, ScrapingRequestSerializer, AIServiceResponseSerializer,
    HealthCheckSerializer
)
from .ai_services import insights_service, embedding_service
from .rag_pipeline import rag_pipeline, chroma_store
from .scraper import scrape_books_from_source, BookScraperFactory

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify system status.
    
    Returns the status of all system components:
    - Database connection
    - ChromaDB vector store
    - Redis cache
    - Celery worker
    - Embedding model availability
    - LLM availability
    """
    from django.db import connection
    from django.conf import settings
    
    # Initialize health status with all components set to False
    health_data = {
        'status': 'healthy',
        'database': False,
        'chromadb': False,
        'redis': False,
        'celery': False,
        'embedding_model': 'unknown',
        'llm_available': False,
        'timestamp': timezone.now()
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_data['database'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_data['status'] = 'degraded'
    
    # Check ChromaDB availability
    try:
        health_data['chromadb'] = chroma_store.is_available()
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
    
    # Check embedding model
    try:
        health_data['embedding_model'] = embedding_service.get_model_name()
    except Exception as e:
        logger.error(f"Embedding model check failed: {e}")
    
    # Check Redis cache connectivity
    try:
        from .cache import redis_client
        redis_client.ping()
        health_data['redis'] = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
    
    # Check Celery worker availability
    try:
        from .tasks import debug_task
        result = debug_task.delay()
        if result:
            health_data['celery'] = True
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
    
    serializer = HealthCheckSerializer(health_data)
    return Response(serializer.data)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Book CRUD operations and search.
    
    Provides endpoints for:
    - Listing books with filtering and pagination
    - Retrieving book details
    - Creating/updating books
    - Processing books with AI insights
    - Getting recommendations
    """
    
    queryset = Book.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on the action."""
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookCreateSerializer
        return BookDetailSerializer
    
    def get_queryset(self):
        """
        Get filtered queryset based on query parameters.
        
        Supported filters:
        - search: Search in title, author, and description
        - genre: Filter by genre
        - source: Filter by source (goodreads, amazon, etc.)
        - featured: Filter featured books only
        - sort: Sort by field (rating, title, created_at)
        """
        queryset = Book.objects.all()
        
        # Search across multiple fields
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(author__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by genre
        genre = self.request.query_params.get('genre', None)
        if genre:
            queryset = queryset.filter(genre=genre)
        
        # Filter by source
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter featured books only
        featured = self.request.query_params.get('featured', None)
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        sort_by = self.request.query_params.get('sort', '-created_at')
        if sort_by == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'author':
            queryset = queryset.order_by('author')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get book statistics."""
        total_books = Book.objects.count()
        processed_books = Book.objects.filter(is_processed=True).count()
        genre_counts = Book.objects.values('genre').annotate(count=Count('id'))
        
        return Response({
            'total_books': total_books,
            'processed_books': processed_books,
            'genre_distribution': list(genre_counts),
            'avg_rating': Book.objects.aggregate(avg=models.Avg('rating'))['avg']
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process a book to generate embeddings and AI insights.
        
        Supports both synchronous and background processing.
        Use background=true to process asynchronously via Celery.
        """
        book = self.get_object()
        
        if book.is_processed:
            return Response({
                'message': 'Book already processed',
                'ai_insights': book.ai_insights
            })
        
        background = request.data.get('background', False)
        
        if background:
            # Queue for background processing with Celery
            try:
                from .tasks import generate_book_insights, process_book_chunks
                
                # Queue both tasks
                insights_task = generate_book_insights.delay(book.id)
                chunks_task = process_book_chunks.delay(book.id)
                
                return Response({
                    'message': 'Book queued for background processing',
                    'task_ids': {
                        'insights': str(insights_task.id),
                        'chunks': str(chunks_task.id)
                    },
                    'status': 'queued'
                }, status=status.HTTP_202_ACCEPTED)
                
            except Exception as e:
                logger.warning(f"Celery not available, falling back to sync: {e}")
                # Fall through to synchronous processing
        
        # Synchronous processing (original behavior)
        try:
            content = book.content_text or book.description or ""
            
            if not content:
                return Response(
                    {'error': 'No content available for processing'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            chunks_created, embedding_ids = rag_pipeline.process_document(
                book_id=book.id,
                book_title=book.title,
                content=content,
                metadata={'source': book.source}
            )
            
            insights = insights_service.generate_all_insights(book)
            
            book.is_processed = True
            book.ai_insights = insights
            book.embedding_id = embedding_ids[0] if embedding_ids else None
            book.save()
            
            if chunks_created > 0:
                for i, emb_id in enumerate(embedding_ids):
                    BookChunk.objects.create(
                        book=book,
                        chunk_index=i,
                        content=content[i*500:(i+1)*500] if len(content) > (i+1)*500 else content[i*500:],
                        embedding_id=emb_id
                    )
            
            return Response({
                'message': 'Book processed successfully',
                'chunks_created': chunks_created,
                'ai_insights': insights
            })
            
        except Exception as e:
            logger.error(f"Book processing error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get similar book recommendations."""
        book = self.get_object()
        similar_books = book.get_similar_books(limit=10)
        
        serializer = BookListSerializer(similar_books, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Get book chunks for RAG."""
        book = self.get_object()
        chunks = book.chunks.all()
        serializer = BookChunkSerializer(chunks, many=True)
        return Response(serializer.data)


class BookUploadView(APIView):
    """Handle book file uploads."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Upload and process a book file."""
        serializer = BookUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES.get('file')
        title = serializer.validated_data.get('title', 'Untitled')
        author = serializer.validated_data.get('author', 'Unknown')
        generate_insights = serializer.validated_data.get('generate_insights', True)
        
        content_text = ""
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.txt'):
                    content_text = uploaded_file.read().decode('utf-8', errors='ignore')
                elif uploaded_file.name.endswith('.pdf'):
                    from PyPDF2 import PdfReader
                    pdf_reader = PdfReader(uploaded_file)
                    content_text = "\n".join([
                        page.extract_text() for page in pdf_reader.pages
                    ])
                elif uploaded_file.name.endswith('.docx'):
                    from docx import Document
                    doc = Document(uploaded_file)
                    content_text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.error(f"File processing error: {e}")
                return Response(
                    {'error': f'Failed to process file: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        book = Book.objects.create(
            title=title,
            author=author,
            content_text=content_text,
            source='upload'
        )
        
        if generate_insights and content_text:
            try:
                book.description = content_text[:500]
                book.save()
                
                insights = insights_service.generate_all_insights(book)
                book.ai_insights = insights
                book.is_processed = True
                book.save()
                
                chunks_created, _ = rag_pipeline.process_document(
                    book_id=book.id,
                    book_title=book.title,
                    content=content_text
                )
            except Exception as e:
                logger.error(f"Insight generation error: {e}")
        
        return Response(
            BookDetailSerializer(book).data,
            status=status.HTTP_201_CREATED
        )


class QAView(APIView):
    """Question answering endpoint using RAG with caching."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Ask a question about books."""
        serializer = QARequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        question = serializer.validated_data['question']
        book_id = serializer.validated_data.get('book_id')
        session_id = serializer.validated_data.get('session_id', f"session_{int(time.time())}")
        use_rag = serializer.validated_data.get('use_rag', True)
        model = serializer.validated_data.get('model', 'lm-studio')
        
        cache_key = f"qa:{hashlib.md5(f'{question}:{book_id}:{use_rag}'.encode()).hexdigest()}"
        from books.ai_services import response_cache
        cached_response = response_cache.get(cache_key)
        
        book = None
        if book_id:
            try:
                book = Book.objects.get(id=book_id)
            except Book.DoesNotExist:
                return Response(
                    {'error': 'Book not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            if cached_response:
                conversation = QAConversation.objects.create(
                    session_id=session_id,
                    book=book,
                    question=question,
                    answer=cached_response.answer,
                    sources=cached_response.sources,
                    model_used=cached_response.model_used,
                    response_time=cached_response.response_time
                )
                return Response({
                    'answer': cached_response.answer,
                    'sources': cached_response.sources,
                    'session_id': session_id,
                    'conversation_id': conversation.id,
                    'retrieved_chunks': cached_response.retrieved_chunks,
                    'confidence': cached_response.confidence,
                    'model_used': cached_response.model_used,
                    'response_time': cached_response.response_time,
                    'cached': True
                })
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                rag_pipeline.answer_question(
                    question=question,
                    book_id=book_id,
                    book_title=book.title if book else None,
                    book_description=book.description if book else None,
                    book_ai_insights=book.ai_insights if book and book.ai_insights else None,
                    book_price=book.price if book and book.price else None,
                    book_author=book.author if book and book.author else None,
                    model=model,
                    use_rag=use_rag
                )
            )
            
            response_cache.set(cache_key, response)
            
            conversation = QAConversation.objects.create(
                session_id=session_id,
                book=book,
                question=question,
                answer=response.answer,
                sources=response.sources,
                model_used=response.model_used,
                response_time=response.response_time
            )
            
            return Response({
                'answer': response.answer,
                'sources': response.sources,
                'session_id': session_id,
                'conversation_id': conversation.id,
                'retrieved_chunks': response.retrieved_chunks,
                'confidence': response.confidence,
                'model_used': response.model_used,
                'response_time': response.response_time,
                'cached': False
            })
            
        except Exception as e:
            logger.error(f"QA error: {e}")
            return Response(
                {'error': f'Failed to generate answer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationHistoryView(APIView):
    """View conversation history."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, session_id):
        """Get conversation history for a session."""
        conversations = QAConversation.objects.filter(
            session_id=session_id
        ).order_by('created_at')
        
        serializer = QAConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ScrapingView(APIView):
    """Handle web scraping for book data."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Start a scraping job."""
        serializer = ScrapingRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        source = serializer.validated_data['source']
        url = serializer.validated_data['url']
        max_books = serializer.validated_data['max_books']
        
        job = ScrapingJob.objects.create(
            source=source,
            url=url,
            status='running',
            started_at=timezone.now()
        )
        
        try:
            if source == 'custom':
                query = url.split('?q=')[-1] if '?q=' in url else 'books'
            else:
                query = 'fiction'
            
            books_data = []
            try:
                books_data = scrape_books_from_source(
                    source=source,
                    query=query,
                    max_books=max_books
                )
            except Exception as scrape_error:
                logger.warning(f"Web scraping failed: {scrape_error}")
            
            if not books_data:
                books_data = self._get_fallback_books(query, max_books)
            
            added_books = []
            skipped_books = 0
            for book_data in books_data:
                existing = Book.objects.filter(title=book_data['title'], author=book_data['author']).first()
                if existing:
                    skipped_books += 1
                    added_books.append(existing)
                else:
                    book = Book.objects.create(**book_data)
                    added_books.append(book)
            
            job.status = 'completed'
            job.books_scraped = len(added_books) - skipped_books
            job.completed_at = timezone.now()
            job.save()
            
            return Response({
                'job_id': job.id,
                'status': job.status,
                'books_scraped': len(added_books) - skipped_books,
                'books_added': len(added_books),
                'books_skipped': skipped_books,
                'total_collected': len(books_data),
                'books': BookListSerializer(added_books, many=True).data
            })
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            
            return Response(
                {'error': str(e), 'job_id': job.id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_fallback_books(self, query: str, max_books: int) -> List[Dict]:
        """Return fallback books when web scraping fails."""
        fallback_books = [
            {'title': 'The Alchemist', 'author': 'Paulo Coelho', 'description': 'A magical story about following your dreams.', 'genre': 'fiction', 'rating': 4.2, 'num_ratings': 2500000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'The Da Vinci Code', 'author': 'Dan Brown', 'description': 'A thriller combining art, history, and religious conspiracy.', 'genre': 'mystery', 'rating': 4.0, 'num_ratings': 2000000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'The Catcher in the Rye', 'author': 'J.D. Salinger', 'description': 'A story about teenage alienation in post-war America.', 'genre': 'fiction', 'rating': 3.8, 'num_ratings': 3000000, 'source': 'demo', 'price': '$12.99'},
            {'title': 'The Lord of the Rings', 'author': 'J.R.R. Tolkien', 'description': 'An epic fantasy quest to destroy the One Ring.', 'genre': 'fantasy', 'rating': 4.5, 'num_ratings': 6000000, 'source': 'demo', 'price': '$25.99'},
            {'title': 'Harry Potter and the Sorcerers Stone', 'author': 'J.K. Rowling', 'description': 'A young wizard discovers his magical heritage.', 'genre': 'fantasy', 'rating': 4.5, 'num_ratings': 9000000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'The Kite Runner', 'author': 'Khaled Hosseini', 'description': 'A story about friendship, betrayal, and redemption.', 'genre': 'fiction', 'rating': 4.3, 'num_ratings': 3500000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Life of Pi', 'author': 'Yann Martel', 'description': 'A young man survives a shipwreck with a Bengal tiger.', 'genre': 'fiction', 'rating': 4.1, 'num_ratings': 2000000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'The Shining', 'author': 'Stephen King', 'description': 'A family encounters supernatural horrors at an isolated hotel.', 'genre': 'horror', 'rating': 4.2, 'num_ratings': 1500000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'Steve Jobs', 'author': 'Walter Isaacson', 'description': 'The biography of Apple co-founder Steve Jobs.', 'genre': 'biography', 'rating': 4.1, 'num_ratings': 800000, 'source': 'demo', 'price': '$18.99'},
            {'title': 'A Brief History of Time', 'author': 'Stephen Hawking', 'description': 'An exploration of cosmology, black holes, and the universe.', 'genre': 'science', 'rating': 4.0, 'num_ratings': 500000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'The Lean Startup', 'author': 'Eric Ries', 'description': 'How entrepreneurs create businesses in uncertain times.', 'genre': 'business', 'rating': 4.0, 'num_ratings': 400000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'Good to Great', 'author': 'Jim Collins', 'description': 'How companies transition from good to great.', 'genre': 'business', 'rating': 4.0, 'num_ratings': 450000, 'source': 'demo', 'price': '$17.99'},
            {'title': 'The 7 Habits of Highly Effective People', 'author': 'Stephen R. Covey', 'description': 'A principle-centered approach to effectiveness.', 'genre': 'self-help', 'rating': 4.1, 'num_ratings': 600000, 'source': 'demo', 'price': '$18.99'},
            {'title': 'Educated', 'author': 'Tara Westover', 'description': 'A memoir about earning a PhD from a survivalist upbringing.', 'genre': 'biography', 'rating': 4.4, 'num_ratings': 800000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'Where the Crawdads Sing', 'author': 'Delia Owens', 'description': 'A coming-of-age story in the North Carolina marshlands.', 'genre': 'fiction', 'rating': 4.5, 'num_ratings': 1500000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Becoming', 'author': 'Michelle Obama', 'description': 'The memoir of the former First Lady.', 'genre': 'biography', 'rating': 4.5, 'num_ratings': 2000000, 'source': 'demo', 'price': '$19.99'},
            {'title': 'The Immortal Life of Henrietta Lacks', 'author': 'Rebecca Skloot', 'description': 'The story of cells that revolutionized medicine.', 'genre': 'science', 'rating': 4.1, 'num_ratings': 600000, 'source': 'demo', 'price': '$17.99'},
            {'title': 'Outliers', 'author': 'Malcolm Gladwell', 'description': 'What makes high-achievers different.', 'genre': 'business', 'rating': 4.0, 'num_ratings': 500000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Thinking, Fast and Slow', 'author': 'Daniel Kahneman', 'description': 'The two systems that drive the way we think.', 'genre': 'psychology', 'rating': 4.1, 'num_ratings': 400000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'The Nightingale', 'author': 'Kristin Hannah', 'description': 'Two sisters in Nazi-occupied France.', 'genre': 'fiction', 'rating': 4.6, 'num_ratings': 700000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'Ready Player One', 'author': 'Ernest Cline', 'description': 'A dystopian thriller in a virtual reality world.', 'genre': 'sci-fi', 'rating': 4.3, 'num_ratings': 900000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'The Handmaids Tale', 'author': 'Margaret Atwood', 'description': 'A dystopian novel about a totalitarian society.', 'genre': 'fiction', 'rating': 4.1, 'num_ratings': 1200000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'The Power of Now', 'author': 'Eckhart Tolle', 'description': 'A spiritual guide to living in the present.', 'genre': 'self-help', 'rating': 4.0, 'num_ratings': 350000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'Sapiens', 'author': 'Yuval Noah Harari', 'description': 'A brief history of humankind.', 'genre': 'history', 'rating': 4.2, 'num_ratings': 900000, 'source': 'demo', 'price': '$18.99'},
            {'title': 'The Art of War', 'author': 'Sun Tzu', 'description': 'An ancient Chinese military strategy treatise.', 'genre': 'history', 'rating': 3.9, 'num_ratings': 400000, 'source': 'demo', 'price': '$9.99'},
            {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'description': 'A novel exploring the American Dream in the Jazz Age.', 'genre': 'fiction', 'rating': 4.0, 'num_ratings': 3500000, 'source': 'demo', 'price': '$12.99'},
            {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'description': 'A story of racial injustice in the American South.', 'genre': 'fiction', 'rating': 4.3, 'num_ratings': 4200000, 'source': 'demo', 'price': '$13.99'},
            {'title': '1984', 'author': 'George Orwell', 'description': 'A dystopian masterpiece about totalitarianism.', 'genre': 'sci-fi', 'rating': 4.2, 'num_ratings': 3100000, 'source': 'demo', 'price': '$12.99'},
            {'title': 'The Hobbit', 'author': 'J.R.R. Tolkien', 'description': 'A fantasy adventure with dwarves and a dragon.', 'genre': 'fantasy', 'rating': 4.3, 'num_ratings': 2800000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'Pride and Prejudice', 'author': 'Jane Austen', 'description': 'A witty romance in Regency-era England.', 'genre': 'romance', 'rating': 4.3, 'num_ratings': 2900000, 'source': 'demo', 'price': '$11.99'},
            {'title': 'The Hunger Games', 'author': 'Suzanne Collins', 'description': 'Children fight to the death in a televised competition.', 'genre': 'sci-fi', 'rating': 4.3, 'num_ratings': 6500000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'Gone Girl', 'author': 'Gillian Flynn', 'description': 'A psychological thriller about a marriage gone wrong.', 'genre': 'thriller', 'rating': 4.0, 'num_ratings': 900000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'The Girl with the Dragon Tattoo', 'author': 'Stieg Larsson', 'description': 'A journalist and hacker investigate a disappearance.', 'genre': 'mystery', 'rating': 4.0, 'num_ratings': 1200000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Dune', 'author': 'Frank Herbert', 'description': 'A sci-fi epic about politics and ecology on a desert planet.', 'genre': 'sci-fi', 'rating': 4.2, 'num_ratings': 700000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'Murder on the Orient Express', 'author': 'Agatha Christie', 'description': 'Detective Poirot investigates a murder on a train.', 'genre': 'mystery', 'rating': 4.1, 'num_ratings': 800000, 'source': 'demo', 'price': '$12.99'},
            {'title': 'The Girl on the Train', 'author': 'Paula Hawkins', 'description': 'A thriller about obsession and deception.', 'genre': 'thriller', 'rating': 3.9, 'num_ratings': 600000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'The Silent Patient', 'author': 'Alex Michaelides', 'description': 'A woman who shot her husband and stopped speaking.', 'genre': 'thriller', 'rating': 4.0, 'num_ratings': 500000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'And Then There Were None', 'author': 'Agatha Christie', 'description': 'Ten strangers killed one by one on an island.', 'genre': 'mystery', 'rating': 4.2, 'num_ratings': 750000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'Atomic Habits', 'author': 'James Clear', 'description': 'Tiny changes for remarkable results.', 'genre': 'self-help', 'rating': 4.3, 'num_ratings': 800000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'The Subtle Art of Not Giving a F*ck', 'author': 'Mark Manson', 'description': 'A counterintuitive approach to living well.', 'genre': 'self-help', 'rating': 4.0, 'num_ratings': 400000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'Brave New World', 'author': 'Aldous Huxley', 'description': 'A dystopian novel about a genetically modified society.', 'genre': 'sci-fi', 'rating': 3.9, 'num_ratings': 700000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'The Fault in Our Stars', 'author': 'John Green', 'description': 'A love story between two teenagers with cancer.', 'genre': 'romance', 'rating': 4.2, 'num_ratings': 2500000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'The Name of the Rose', 'author': 'Umberto Eco', 'description': 'A medieval murder mystery in an Italian monastery.', 'genre': 'mystery', 'rating': 4.0, 'num_ratings': 300000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Big Little Lies', 'author': 'Liane Moriarty', 'description': 'A darkly comic novel about mothers with secrets.', 'genre': 'fiction', 'rating': 4.0, 'num_ratings': 550000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'The Hitchhikers Guide to the Galaxy', 'author': 'Douglas Adams', 'description': 'A comedic sci-fi series about Arthur Dent.', 'genre': 'sci-fi', 'rating': 4.1, 'num_ratings': 600000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'It', 'author': 'Stephen King', 'description': 'A group of kids confront a terrifying entity.', 'genre': 'horror', 'rating': 4.2, 'num_ratings': 900000, 'source': 'demo', 'price': '$17.99'},
            {'title': 'The Maze Runner', 'author': 'James Dashner', 'description': 'Teenagers trapped in a maze must find escape.', 'genre': 'sci-fi', 'rating': 4.0, 'num_ratings': 800000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'Divergent', 'author': 'Veronica Roth', 'description': 'A dystopian world divided by personality traits.', 'genre': 'sci-fi', 'rating': 4.0, 'num_ratings': 1500000, 'source': 'demo', 'price': '$13.99'},
            {'title': 'The Girl Who Leapt Through Time', 'author': 'Yasutaka Tsutsui', 'description': 'A girl discovers a notebook that lets her time travel.', 'genre': 'sci-fi', 'rating': 4.0, 'num_ratings': 200000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'Neuromancer', 'author': 'William Gibson', 'description': 'A cyberpunk classic about hacking and AI.', 'genre': 'sci-fi', 'rating': 4.0, 'num_ratings': 400000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'Foundation', 'author': 'Isaac Asimov', 'description': 'A galactic empire and the science of psychohistory.', 'genre': 'sci-fi', 'rating': 4.1, 'num_ratings': 500000, 'source': 'demo', 'price': '$16.99'},
            {'title': 'The Chronicles of Narnia', 'author': 'C.S. Lewis', 'description': 'Children discover a magical world through a wardrobe.', 'genre': 'fantasy', 'rating': 4.2, 'num_ratings': 2000000, 'source': 'demo', 'price': '$14.99'},
            {'title': 'Memoirs of a Geisha', 'author': 'Arthur Golden', 'description': 'The story of a Japanese geisha in the 20th century.', 'genre': 'fiction', 'rating': 4.2, 'num_ratings': 1500000, 'source': 'demo', 'price': '$15.99'},
            {'title': 'The Secret Garden', 'author': 'Frances Hodgson Burnett', 'description': 'A magical garden transforms a lonely girl.', 'genre': 'fiction', 'rating': 4.1, 'num_ratings': 800000, 'source': 'demo', 'price': '$10.99'},
            {'title': 'Wuthering Heights', 'author': 'Emily Bronte', 'description': 'A dark tale of passion and revenge on the moors.', 'genre': 'romance', 'rating': 3.9, 'num_ratings': 1200000, 'source': 'demo', 'price': '$11.99'},
            {'title': 'Jane Eyre', 'author': 'Charlotte Bronte', 'description': 'A governess finds love and independence.', 'genre': 'romance', 'rating': 4.2, 'num_ratings': 1800000, 'source': 'demo', 'price': '$11.99'},
            {'title': 'The Picture of Dorian Gray', 'author': 'Oscar Wilde', 'description': 'A man stays young while his portrait ages.', 'genre': 'fiction', 'rating': 4.0, 'num_ratings': 900000, 'source': 'demo', 'price': '$10.99'},
            {'title': 'Frankenstein', 'author': 'Mary Shelley', 'description': 'A scientist creates a monster.', 'genre': 'horror', 'rating': 3.9, 'num_ratings': 1000000, 'source': 'demo', 'price': '$9.99'},
            {'title': 'Dracula', 'author': 'Bram Stoker', 'description': 'The classic vampire tale.', 'genre': 'horror', 'rating': 4.0, 'num_ratings': 1100000, 'source': 'demo', 'price': '$10.99'},
            {'title': 'The Call of Cthulhu', 'author': 'H.P. Lovecraft', 'description': 'Cosmic horror from beyond reality.', 'genre': 'horror', 'rating': 4.0, 'num_ratings': 300000, 'source': 'demo', 'price': '$9.99'},
            {'title': 'Sherlock Holmes Complete Works', 'author': 'Arthur Conan Doyle', 'description': 'The complete adventures of the great detective.', 'genre': 'mystery', 'rating': 4.6, 'num_ratings': 2500000, 'source': 'demo', 'price': '$19.99'},
            {'title': 'The Adventures of Sherlock Holmes', 'author': 'Arthur Conan Doyle', 'description': 'Twelve cases of the famous detective.', 'genre': 'mystery', 'rating': 4.4, 'num_ratings': 1500000, 'source': 'demo', 'price': '$14.99'},
        ]
        
        existing_titles = set(Book.objects.values_list('title', flat=True))
        available_books = [b for b in fallback_books if b['title'] not in existing_titles]
        
        if not available_books:
            return []
        
        return available_books[:max_books]
    
    def get(self, request):
        """Get scraping job status or history."""
        job_id = request.query_params.get('job_id')
        
        if job_id:
            try:
                job = ScrapingJob.objects.get(id=job_id)
                return Response(ScrapingJobSerializer(job).data)
            except ScrapingJob.DoesNotExist:
                return Response(
                    {'error': 'Job not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        jobs = ScrapingJob.objects.all()[:20]
        return Response(ScrapingJobSerializer(jobs, many=True).data)


class RecommendationView(APIView):
    """Book recommendation endpoint."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Get book recommendations."""
        book_id = request.data.get('book_id')
        limit = min(int(request.data.get('limit', 5)), 20)
        
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            source_book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {'error': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            all_books = list(Book.objects.exclude(id=book_id).values(
                'id', 'title', 'author', 'genre', 'description'
            ))
            
            recommendations = insights_service.generate_recommendations(
                source_book.__dict__,
                all_books,
                limit=limit
            )
            
            recommended_books = []
            for rec in recommendations:
                book_title = rec.get('title', '')
                if book_title:
                    try:
                        book = Book.objects.get(title__icontains=book_title.split(' by ')[0])
                        recommended_books.append({
                            'book': BookListSerializer(book).data,
                            'reason': rec.get('reason', ''),
                            'match_score': rec.get('match_score', 0.0)
                        })
                        
                        BookRecommendation.objects.update_or_create(
                            source_book=source_book,
                            recommended_book=book,
                            defaults={
                                'reason': rec.get('reason', ''),
                                'confidence_score': rec.get('match_score', 0.0),
                                'recommendation_type': 'ai_generated'
                            }
                        )
                    except Book.DoesNotExist:
                        continue
            
            return Response({
                'source_book': BookListSerializer(source_book).data,
                'recommendations': recommended_books
            })
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InsightGenerationView(APIView):
    """Generate AI insights for books."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate insights for a book."""
        book_id = request.data.get('book_id')
        insight_types = request.data.get('types', ['summary', 'genre'])
        
        if not book_id:
            return Response(
                {'error': 'book_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {'error': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        results = {}
        
        try:
            if 'summary' in insight_types:
                text = book.content_text or book.description or ""
                results['summary'] = insights_service.generate_summary(text)
            
            if 'genre' in insight_types:
                results['genre_analysis'] = insights_service.classify_genre(
                    book.title,
                    book.description or "",
                    book.content_text
                )
            
            if 'sentiment' in insight_types:
                text = book.description or ""
                results['sentiment'] = insights_service.analyze_sentiment(text)
            
            return Response({
                'book_id': book_id,
                'insights': results
            })
            
        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review operations."""
    
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Review.objects.all()
        book_id = self.request.query_params.get('book_id')
        
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        review = serializer.save()
        
        try:
            sentiment = insights_service.analyze_sentiment(review.content)
            review.sentiment_score = sentiment.get('sentiment_score')
            review.sentiment_label = sentiment.get('sentiment_label')
            review.save()
        except Exception as e:
            logger.error(f"Review sentiment analysis error: {e}")


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints."""
    return Response({
        'name': 'Document Intelligence Platform API',
        'version': '1.0.0',
        'endpoints': {
            'books': '/api/books/',
            'books_detail': '/api/books/{id}/',
            'book_upload': '/api/books/upload/',
            'book_process': '/api/books/{id}/process/',
            'book_recommendations': '/api/books/{id}/recommendations/',
            'qa': '/api/qa/',
            'conversations': '/api/conversations/{session_id}/',
            'scrape': '/api/scrape/',
            'recommendations': '/api/recommendations/',
            'insights': '/api/insights/generate/',
            'reviews': '/api/reviews/',
            'health': '/api/health/',
            'sources': '/api/sources/',
            'stats': '/api/books/stats/',
            'chunks': '/api/books/{id}/chunks/'
        },
        'documentation': '/api/docs/'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def available_sources(request):
    """Get list of available scraping sources."""
    sources = ['goodreads', 'amazon', 'openlibrary']
    return Response({'sources': sources})


@api_view(['POST'])
@permission_classes([AllowAny])
def load_sample_books(request):
    """Load sample books into the database for demo purposes."""
    sample_books = [
        {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'description': 'A novel set in the Jazz Age that examines the American Dream through the lens of wealth, love, and tragedy. The story follows the mysterious Jay Gatsby and his obsessive pursuit of Daisy Buchanan.',
            'genre': 'fiction',
            'rating': 4.0,
            'num_ratings': 3500000,
            'publisher': 'Charles Scribner\'s Sons',
            'published_date': '1925-04-10',
            'page_count': 180,
            'language': 'English',
            'isbn': '978-0743273565',
            'is_featured': True,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A classic American novel exploring themes of wealth, love, idealism, and social upheaval during the Roaring Twenties.',
                'genre_analysis': {
                    'primary_genre': 'fiction',
                    'secondary_genres': ['historical', 'drama'],
                    'confidence': 0.92,
                    'indicators': ['Jazz Age setting', 'American Dream themes', 'Romantic elements']
                },
                'review_sentiment': {
                    'sentiment_score': 0.75,
                    'sentiment_label': 'positive',
                    'confidence': 0.88,
                    'tone': 'nostalgic and reflective'
                }
            }
        },
        {
            'title': 'To Kill a Mockingbird',
            'author': 'Harper Lee',
            'description': 'A gripping tale of racial injustice and the loss of innocence in the American South. Through the eyes of young Scout Finch, we witness her father, Atticus, defend a Black man falsely accused of rape.',
            'genre': 'fiction',
            'rating': 4.3,
            'num_ratings': 4200000,
            'publisher': 'J.B. Lippincott & Co.',
            'published_date': '1960-07-11',
            'page_count': 281,
            'language': 'English',
            'isbn': '978-0061120084',
            'is_featured': True,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A powerful exploration of racial inequality and moral courage in 1930s Alabama, seen through the innocent eyes of a young girl.',
                'genre_analysis': {
                    'primary_genre': 'fiction',
                    'secondary_genres': ['historical', 'social-justice'],
                    'confidence': 0.95,
                    'indicators': ['Southern Gothic setting', 'Legal drama', 'Coming-of-age themes']
                },
                'review_sentiment': {
                    'sentiment_score': 0.82,
                    'sentiment_label': 'positive',
                    'confidence': 0.91,
                    'tone': 'thoughtful and compassionate'
                }
            }
        },
        {
            'title': '1984',
            'author': 'George Orwell',
            'description': 'A dystopian masterpiece depicting a totalitarian future where Big Brother watches everything. Winston Smith struggles against the Party\'s control over truth, history, and individual thought.',
            'genre': 'sci-fi',
            'rating': 4.2,
            'num_ratings': 3100000,
            'publisher': 'Secker & Warburg',
            'published_date': '1949-06-08',
            'page_count': 328,
            'language': 'English',
            'isbn': '978-0451524935',
            'is_featured': True,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A chilling vision of a totalitarian state where surveillance is absolute and independent thought is treason.',
                'genre_analysis': {
                    'primary_genre': 'sci-fi',
                    'secondary_genres': ['dystopian', 'political'],
                    'confidence': 0.98,
                    'indicators': ['Totalitarian regime', 'Surveillance themes', 'Language manipulation']
                },
                'review_sentiment': {
                    'sentiment_score': 0.68,
                    'sentiment_label': 'positive',
                    'confidence': 0.85,
                    'tone': 'alarming and thought-provoking'
                }
            }
        },
        {
            'title': 'The Hobbit',
            'author': 'J.R.R. Tolkien',
            'description': 'Bilbo Baggins, a comfort-loving hobbit, embarks on an unexpected journey with a wizard and thirteen dwarves to reclaim their mountain home from the dragon Smaug.',
            'genre': 'fantasy',
            'rating': 4.3,
            'num_ratings': 2800000,
            'publisher': 'George Allen & Unwin',
            'published_date': '1937-09-21',
            'page_count': 310,
            'language': 'English',
            'isbn': '978-0547928227',
            'is_featured': False,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A beloved fantasy adventure that introduces readers to Middle-earth and the beginning of Tolkien\'s legendary legendarium.',
                'genre_analysis': {
                    'primary_genre': 'fantasy',
                    'secondary_genres': ['adventure', 'children'],
                    'confidence': 0.99,
                    'indicators': ['Quest structure', 'Fantasy creatures', 'Hero\'s journey']
                },
                'review_sentiment': {
                    'sentiment_score': 0.91,
                    'sentiment_label': 'positive',
                    'confidence': 0.94,
                    'tone': 'whimsical and epic'
                }
            }
        },
        {
            'title': 'Pride and Prejudice',
            'author': 'Jane Austen',
            'description': 'Elizabeth Bennet navigates issues of manners, morality, and marriage in Regency-era England. Her evolving relationship with the proud Mr. Darcy forms the heart of this beloved romance.',
            'genre': 'romance',
            'rating': 4.3,
            'num_ratings': 2900000,
            'publisher': 'T. Egerton',
            'published_date': '1813-01-28',
            'page_count': 279,
            'language': 'English',
            'isbn': '978-0141439518',
            'is_featured': False,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A witty social comedy exploring love, class, and first impressions in Georgian England.',
                'genre_analysis': {
                    'primary_genre': 'romance',
                    'secondary_genres': ['classic', 'comedy'],
                    'confidence': 0.96,
                    'indicators': ['Romantic tension', 'Social satire', 'Strong female protagonist']
                },
                'review_sentiment': {
                    'sentiment_score': 0.88,
                    'sentiment_label': 'positive',
                    'confidence': 0.92,
                    'tone': 'playful and romantic'
                }
            }
        },
        {
            'title': 'The Da Vinci Code',
            'author': 'Dan Brown',
            'description': 'Robert Langdon and Sophie Neveu race against time to solve a series of puzzles tied to the works of Leonardo da Vinci, uncovering a secret society and a religious cover-up.',
            'genre': 'mystery',
            'rating': 3.9,
            'num_ratings': 2100000,
            'publisher': 'Doubleday',
            'published_date': '2003-03-18',
            'page_count': 454,
            'language': 'English',
            'isbn': '978-0307474278',
            'is_featured': False,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A fast-paced thriller blending art history, cryptography, and religious conspiracy in a race against time.',
                'genre_analysis': {
                    'primary_genre': 'mystery',
                    'secondary_genres': ['thriller', 'adventure'],
                    'confidence': 0.94,
                    'indicators': ['Puzzle solving', 'Conspiracy elements', 'Rapid pacing']
                },
                'review_sentiment': {
                    'sentiment_score': 0.72,
                    'sentiment_label': 'positive',
                    'confidence': 0.82,
                    'tone': 'exciting and suspenseful'
                }
            }
        },
        {
            'title': 'The Alchemist',
            'author': 'Paulo Coelho',
            'description': 'Santiago, an Andalusian shepherd boy, travels to Egypt in search of a treasure buried near the Pyramids. Along the way, he learns about the Soul of the World and follows his Personal Legend.',
            'genre': 'fiction',
            'rating': 3.8,
            'num_ratings': 2400000,
            'publisher': 'HarperOne',
            'published_date': '1988-01-01',
            'page_count': 208,
            'language': 'Portuguese',
            'isbn': '978-0062315007',
            'is_featured': False,
            'is_processed': True,
            'ai_insights': {
                'summary': 'An inspirational fable about following your dreams and listening to your heart.',
                'genre_analysis': {
                    'primary_genre': 'fiction',
                    'secondary_genres': ['philosophical', 'self-help'],
                    'confidence': 0.89,
                    'indicators': ['Allegorical structure', 'Spiritual themes', 'Simple prose']
                },
                'review_sentiment': {
                    'sentiment_score': 0.76,
                    'sentiment_label': 'positive',
                    'confidence': 0.87,
                    'tone': 'inspirational and reflective'
                }
            }
        },
        {
            'title': 'The Psychology of Money',
            'author': 'Morgan Housel',
            'description': 'Timeless lessons on wealth, greed, and happiness explained through 19 short stories. This book explores how people actually think about money, rather than how they should.',
            'genre': 'self-help',
            'rating': 4.5,
            'num_ratings': 380000,
            'publisher': 'Harriman House',
            'published_date': '2020-09-08',
            'page_count': 256,
            'language': 'English',
            'isbn': '978-0857197689',
            'is_featured': True,
            'is_processed': True,
            'ai_insights': {
                'summary': 'A modern classic on financial psychology that reveals how our emotions and behaviors affect our financial decisions.',
                'genre_analysis': {
                    'primary_genre': 'self-help',
                    'secondary_genres': ['business', 'psychology'],
                    'confidence': 0.96,
                    'indicators': ['Behavioral finance', 'Practical advice', 'Narrative format']
                },
                'review_sentiment': {
                    'sentiment_score': 0.93,
                    'sentiment_label': 'positive',
                    'confidence': 0.95,
                    'tone': 'enlightening and practical'
                }
            }
        },
    ]
    
    created_count = 0
    for book_data in sample_books:
        book, created = Book.objects.get_or_create(
            title=book_data['title'],
            author=book_data['author'],
            defaults=book_data
        )
        if created:
            created_count += 1
    
    return Response({
        'message': f'Successfully loaded {created_count} sample books',
        'total_books': Book.objects.count(),
        'books': BookListSerializer(
            Book.objects.filter(title__in=[b['title'] for b in sample_books]),
            many=True
        ).data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_bulk_insights(request):
    """Generate AI insights for all books that don't have them yet."""
    books_without_insights = Book.objects.filter(
        models.Q(ai_insights=None) | models.Q(ai_insights={}) | models.Q(ai_insights__summary=None)
    )
    
    total = books_without_insights.count()
    processed = 0
    errors = []
    
    all_books = list(Book.objects.values('id', 'title', 'author', 'genre', 'description'))
    
    for book in books_without_insights:
        try:
            content = book.description or book.content_text or ""
            if not content:
                errors.append({'book': book.title, 'error': 'No content available'})
                continue
            
            insights = {}
            
            insights['summary'] = content[:500] + "..." if len(content) > 500 else content
            
            genre_result = insights_service._rule_based_genre_classification(
                book.title,
                book.description or ""
            )
            insights['genre_analysis'] = genre_result
            
            sentiment_text = f"Book Title: {book.title}. {book.description or ''}"
            insights['review_sentiment'] = insights_service._rule_based_sentiment_analysis(sentiment_text)
            
            other_books = [b for b in all_books if b['id'] != book.id][:20]
            insights['recommendations'] = insights_service._generate_recommendations(
                book.title,
                book.genre,
                book.description or "",
                other_books
            )
            
            insights['generated_at'] = time.time()
            
            book.ai_insights = insights
            book.is_processed = True
            book.save()
            processed += 1
            
            logger.info(f"Generated insights for: {book.title}")
        except Exception as e:
            logger.error(f"Error processing {book.title}: {e}")
            errors.append({'book': book.title, 'error': str(e)})
    
    return Response({
        'message': f'Processed {processed} of {total} books',
        'processed': processed,
        'total': total,
        'errors': errors if errors else None
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def export_books(request):
    """Export books in various formats."""
    export_format = request.query_params.get('format', 'json')
    include_insights = request.query_params.get('insights', 'true').lower() == 'true'
    
    books = Book.objects.all()
    
    if export_format == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        fieldnames = ['id', 'title', 'author', 'genre', 'rating', 'num_ratings', 'description', 'publisher', 'published_date', 'page_count', 'isbn', 'source']
        if include_insights:
            fieldnames.extend(['ai_summary', 'ai_genre', 'ai_sentiment'])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for book in books:
            row = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'rating': str(book.rating) if book.rating else '',
                'num_ratings': book.num_ratings,
                'description': book.description or '',
                'publisher': book.publisher or '',
                'published_date': book.published_date or '',
                'page_count': book.page_count or '',
                'isbn': book.isbn or '',
                'source': book.source or '',
            }
            
            if include_insights and book.ai_insights:
                row['ai_summary'] = book.ai_insights.get('summary', '')
                row['ai_genre'] = book.ai_insights.get('genre_analysis', {}).get('primary_genre', '')
                row['ai_sentiment'] = book.ai_insights.get('review_sentiment', {}).get('sentiment_label', '')
            
            writer.writerow(row)
        
        response = Response(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
        return response
    
    books_data = []
    for book in books:
        book_data = BookListSerializer(book).data
        if include_insights and book.ai_insights:
            book_data['ai_insights'] = book.ai_insights
        books_data.append(book_data)
    
    return Response({
        'total': len(books_data),
        'books': books_data,
        'exported_at': timezone.now().isoformat()
    })


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def favorites(request):
    """Manage favorite books."""
    if request.method == 'GET':
        from books.models import FavoriteBook
        favorites = FavoriteBook.objects.all().select_related('book')
        return Response([{
            'id': f.id,
            'book': BookListSerializer(f.book).data,
            'created_at': f.created_at.isoformat()
        } for f in favorites])
    
    elif request.method == 'POST':
        from books.models import FavoriteBook
        book_id = request.data.get('book_id')
        
        if not book_id:
            return Response({'error': 'book_id required'}, status=400)
        
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=404)
        
        favorite, created = FavoriteBook.objects.get_or_create(book=book)
        
        return Response({
            'message': 'Added to favorites' if created else 'Already in favorites',
            'favorite_id': favorite.id,
            'book': BookListSerializer(book).data
        })


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_favorite(request, book_id):
    """Remove a book from favorites."""
    from books.models import FavoriteBook
    
    try:
        favorite = FavoriteBook.objects.get(book_id=book_id)
        favorite.delete()
        return Response({'message': 'Removed from favorites'})
    except FavoriteBook.DoesNotExist:
        return Response({'error': 'Not in favorites'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """Get search suggestions based on partial query."""
    query = request.query_params.get('q', '').strip()
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    books = Book.objects.filter(
        models.Q(title__icontains=query) | models.Q(author__icontains=query)
    )[:10]
    
    suggestions = [
        {'type': 'book', 'text': b.title, 'author': b.author, 'id': b.id}
        for b in books
    ]
    
    genres = Book.objects.filter(
        genre__icontains=query
    ).values_list('genre', flat=True).distinct()[:5]
    
    for genre in genres:
        suggestions.append({'type': 'genre', 'text': genre.title(), 'id': genre})
    
    authors = Book.objects.filter(
        author__icontains=query
    ).values_list('author', flat=True).distinct()[:5]
    
    for author in authors:
        suggestions.append({'type': 'author', 'text': author, 'id': author})
    
    return Response({'suggestions': suggestions[:15]})


@api_view(['POST'])
@permission_classes([AllowAny])
def rate_book(request):
    """Rate a book."""
    from books.models import Review
    
    book_id = request.data.get('book_id')
    rating = request.data.get('rating')
    review_text = request.data.get('review', '')
    reviewer_name = request.data.get('reviewer_name', 'Anonymous')
    
    if not book_id or not rating:
        return Response({'error': 'book_id and rating required'}, status=400)
    
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return Response({'error': 'Book not found'}, status=404)
    
    if not (1 <= int(rating) <= 5):
        return Response({'error': 'Rating must be 1-5'}, status=400)
    
    review, created = Review.objects.update_or_create(
        book=book,
        reviewer_name=reviewer_name,
        defaults={
            'rating': int(rating),
            'content': review_text,
            'source': 'api'
        }
    )
    
    avg_rating = book.reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    book.rating = round(avg_rating, 2)
    book.num_reviews = book.reviews.count()
    book.save()
    
    return Response({
        'message': 'Rating submitted' if created else 'Rating updated',
        'review_id': review.id,
        'new_average': float(book.rating),
        'total_reviews': book.num_reviews
    })
