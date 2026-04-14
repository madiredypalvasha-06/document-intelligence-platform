from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book, BookChunk
from .rag_pipeline import chroma_store
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BookChunk)
def add_chunk_to_vector_store(sender, instance, created, **kwargs):
    """Add new book chunks to the vector store."""
    if created and instance.embedding_id:
        try:
            from .ai_services import embedding_service
            
            embedding = embedding_service.generate_embeddings([instance.content])[0]
            
            chroma_store._collection.add(
                ids=[instance.embedding_id],
                embeddings=[embedding.tolist()],
                documents=[instance.content],
                metadatas=[{
                    'book_id': instance.book_id,
                    'book_title': instance.book.title,
                    'chunk_index': instance.chunk_index,
                    'chunk_type': instance.chunk_type,
                    **instance.metadata
                }]
            )
            
            logger.info(f"Added chunk {instance.chunk_index} to vector store")
        except Exception as e:
            logger.error(f"Failed to add chunk to vector store: {e}")
