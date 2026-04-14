"""
Background tasks for Document Intelligence Platform
Handles async processing for AI insights, scraping, and recommendations.
"""
import logging
from typing import List, Dict, Any, Optional
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_book_insights(self, book_id: int) -> Dict[str, Any]:
    """
    Generate AI insights for a single book in the background.
    
    Args:
        book_id: The ID of the book to process
        
    Returns:
        Dict containing the generated insights
    """
    from .models import Book
    from .ai_services import insights_service
    
    try:
        book = Book.objects.get(id=book_id)
        
        if book.is_processed:
            return {'status': 'already_processed', 'book_id': book_id}
        
        # Generate content from description if no full content
        content = book.content_text or book.description or ""
        
        if not content:
            return {'status': 'no_content', 'book_id': book_id}
        
        # Generate insights
        insights = insights_service.generate_all_insights(book)
        
        # Update book with insights
        book.ai_insights = insights
        book.is_processed = True
        book.processed_at = timezone.now()
        book.save()
        
        logger.info(f"Generated insights for book {book_id}: {book.title}")
        
        return {
            'status': 'success',
            'book_id': book_id,
            'insights': insights
        }
        
    except Book.DoesNotExist:
        logger.error(f"Book {book_id} not found")
        return {'status': 'error', 'message': 'Book not found'}
        
    except Exception as e:
        logger.error(f"Error generating insights for book {book_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def bulk_generate_insights(
    self, 
    book_ids: List[int],
    regenerate: bool = False
) -> Dict[str, Any]:
    """
    Generate AI insights for multiple books in the background.
    
    Args:
        book_ids: List of book IDs to process
        regenerate: If True, regenerate even for already processed books
        
    Returns:
        Dict containing processing results
    """
    from .models import Book
    from .ai_services import insights_service
    
    results = {
        'total': len(book_ids),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    for i, book_id in enumerate(book_ids):
        try:
            book = Book.objects.get(id=book_id)
            
            if book.is_processed and not regenerate:
                results['skipped'] += 1
                continue
            
            content = book.content_text or book.description or ""
            
            if not content:
                results['skipped'] += 1
                continue
            
            insights = insights_service.generate_all_insights(book)
            
            book.ai_insights = insights
            book.is_processed = True
            book.processed_at = timezone.now()
            book.save()
            
            results['success'] += 1
            
            # Update progress every 10 books
            if (i + 1) % 10 == 0:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i + 1,
                        'total': len(book_ids),
                        'percent': int((i + 1) / len(book_ids) * 100)
                    }
                )
                
            logger.info(f"Processed book {i+1}/{len(book_ids)}: {book.title}")
            
        except Book.DoesNotExist:
            results['failed'] += 1
            results['errors'].append(f"Book {book_id} not found")
            
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Book {book_id}: {str(e)}")
            logger.error(f"Error processing book {book_id}: {e}")
    
    return results


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_books_task(
    self,
    source: str,
    url: str,
    max_books: int = 50,
    query: str = None
) -> Dict[str, Any]:
    """
    Scrape books from a web source in the background.
    
    Args:
        source: The scraping source (goodreads, amazon, openlibrary)
        url: The URL to scrape from
        max_books: Maximum number of books to scrape
        query: Search query for the scraping
        
    Returns:
        Dict containing scraping results
    """
    from .models import ScrapingJob, Book
    from .scraper import BookScraperFactory
    
    try:
        # Create scraping job
        job = ScrapingJob.objects.create(
            source=source,
            url=url,
            status='running',
            started_at=timezone.now()
        )
        
        # Create scraper
        scraper = BookScraperFactory.create_scraper(source)
        
        if not scraper:
            job.status = 'failed'
            job.error_message = f"Unknown source: {source}"
            job.save()
            return {'status': 'error', 'message': f"Unknown source: {source}"}
        
        # Scrape books
        books_data = scraper.scrape(url, max_books=max_books, query=query)
        
        # Save books
        saved_count = 0
        for book_data in books_data:
            try:
                Book.objects.get_or_create(
                    title=book_data.get('title', 'Unknown'),
                    defaults={
                        'author': book_data.get('author', 'Unknown'),
                        'description': book_data.get('description', ''),
                        'rating': book_data.get('rating', 0),
                        'num_ratings': book_data.get('num_ratings', 0),
                        'cover_image_url': book_data.get('cover_image_url'),
                        'book_url': book_data.get('book_url'),
                        'source': source,
                        'price': book_data.get('price'),
                    }
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving book: {e}")
        
        # Update job status
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.books_found = len(books_data)
        job.books_saved = saved_count
        job.save()
        
        # Queue insights generation for new books
        if saved_count > 0:
            new_books = Book.objects.filter(
                source=source,
                is_processed=False
            ).values_list('id', flat=True)[:50]
            
            if new_books:
                bulk_generate_insights.delay(list(new_books))
        
        return {
            'status': 'success',
            'job_id': job.id,
            'books_found': len(books_data),
            'books_saved': saved_count
        }
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(bind=True)
def process_book_chunks(self, book_id: int) -> Dict[str, Any]:
    """
    Process a book's content into chunks and store embeddings.
    
    Args:
        book_id: The ID of the book to process
        
    Returns:
        Dict containing processing results
    """
    from .models import Book
    from .rag_pipeline import rag_pipeline
    
    try:
        book = Book.objects.get(id=book_id)
        
        content = book.content_text or book.description or ""
        
        if not content:
            return {'status': 'no_content', 'book_id': book_id}
        
        # Process document into chunks
        chunk_count, chunk_ids = rag_pipeline.process_document(
            content=content,
            book_id=book.id,
            book_title=book.title,
            metadata={
                'author': book.author,
                'genre': book.genre or 'Fiction',
            }
        )
        
        return {
            'status': 'success',
            'book_id': book_id,
            'chunks_created': chunk_count
        }
        
    except Book.DoesNotExist:
        return {'status': 'error', 'message': 'Book not found'}
        
    except Exception as e:
        logger.error(f"Error processing chunks for book {book_id}: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_conversations(days: int = 30) -> Dict[str, int]:
    """
    Clean up old conversation history.
    
    Args:
        days: Number of days to keep conversations
        
    Returns:
        Dict with cleanup results
    """
    from .models import QAConversation
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = QAConversation.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old conversations")
    
    return {'deleted_count': deleted_count}


@shared_task
def refresh_recommendations(book_ids: List[int] = None) -> Dict[str, Any]:
    """
    Refresh recommendations for books.
    
    Args:
        book_ids: List of book IDs to refresh, or None for all
        
    Returns:
        Dict with refresh results
    """
    from .models import Book
    from .ai_services import insights_service
    
    if book_ids:
        books = Book.objects.filter(id__in=book_ids, is_processed=True)
    else:
        books = Book.objects.filter(is_processed=True)
    
    results = {'total': books.count(), 'updated': 0}
    
    for book in books:
        try:
            recommendations = insights_service._generate_recommendations(book)
            
            if book.ai_insights:
                book.ai_insights['recommendations'] = recommendations
            else:
                book.ai_insights = {'recommendations': recommendations}
            
            book.save()
            results['updated'] += 1
            
        except Exception as e:
            logger.error(f"Error refreshing recommendations for book {book.id}: {e}")
    
    return results


@shared_task(bind=True)
def generate_embedding(self, chunk_id: int) -> Dict[str, Any]:
    """
    Generate embedding for a single chunk.
    
    Args:
        chunk_id: The ID of the chunk to embed
        
    Returns:
        Dict with embedding results
    """
    from .models import BookChunk
    from .ai_services import embedding_service
    from .rag_pipeline import chroma_store
    
    try:
        chunk = BookChunk.objects.get(id=chunk_id)
        
        if chunk.embedding:
            return {'status': 'already_embedded', 'chunk_id': chunk_id}
        
        # Generate embedding
        embedding = embedding_service.generate_embeddings([chunk.content_text])[0]
        
        # Store in vector database
        chroma_store.add_chunks(
            chunks=[],
            book_id=chunk.book_id,
            book_title=chunk.book.title if chunk.book else None,
            custom_embeddings=[embedding.tolist()],
            custom_contents=[chunk.content_text],
            custom_metadata=[{
                'chunk_index': chunk.chunk_index,
                'chunk_type': chunk.chunk_type,
            }]
        )
        
        # Update chunk
        chunk.embedding = embedding.tolist()
        chunk.save()
        
        return {'status': 'success', 'chunk_id': chunk_id}
        
    except BookChunk.DoesNotExist:
        return {'status': 'error', 'message': 'Chunk not found'}
        
    except Exception as e:
        logger.error(f"Error generating embedding for chunk {chunk_id}: {e}")
        return {'status': 'error', 'message': str(e)}
