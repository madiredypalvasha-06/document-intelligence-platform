from rest_framework import serializers
from .models import Book, Review, BookChunk, QAConversation, BookRecommendation, ScrapingJob


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer_name', 'rating', 'title', 'content',
            'sentiment_score', 'sentiment_label', 'created_at', 'source'
        ]
        read_only_fields = ['sentiment_score', 'sentiment_label']


class BookChunkSerializer(serializers.ModelSerializer):
    """Serializer for BookChunk model."""
    
    class Meta:
        model = BookChunk
        fields = ['id', 'chunk_index', 'content', 'chunk_type', 'metadata', 'created_at']


class BookListSerializer(serializers.ModelSerializer):
    """Serializer for listing books with all required fields."""
    
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'genre', 'rating', 
            'num_ratings', 'num_reviews', 'cover_image_url', 'book_url', 
            'is_processed', 'is_featured', 'source', 'price', 'reviews_count', 'created_at'
        ]
    
    def get_reviews_count(self, obj):
        return obj.reviews.count()


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer for book details (full data)."""
    
    reviews = ReviewSerializer(many=True, read_only=True)
    similar_books = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'summary', 'genre',
            'isbn', 'publisher', 'published_date', 'page_count', 'rating',
            'num_ratings', 'num_reviews', 'cover_image_url', 'book_url',
            'source', 'price', 'language', 'tags', 'ai_insights',
            'is_processed', 'is_featured', 'reviews', 'similar_books',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['ai_insights', 'embedding_id', 'is_processed']
    
    def get_similar_books(self, obj):
        similar = obj.get_similar_books(limit=5)
        return BookListSerializer(similar, many=True).data


class BookCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating books."""
    
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'description', 'genre', 'isbn',
            'publisher', 'published_date', 'page_count', 'rating',
            'num_ratings', 'cover_image_url', 'book_url', 'source',
            'content_text', 'price', 'language', 'tags'
        ]


class BookUploadSerializer(serializers.Serializer):
    """Serializer for file upload."""
    
    file = serializers.FileField()
    title = serializers.CharField(max_length=500, required=False)
    author = serializers.CharField(max_length=300, required=False)
    generate_insights = serializers.BooleanField(default=True)


class QAConversationSerializer(serializers.ModelSerializer):
    """Serializer for Q&A conversations."""
    
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = QAConversation
        fields = [
            'id', 'session_id', 'book', 'book_title', 'question',
            'answer', 'sources', 'model_used', 'response_time', 'created_at'
        ]
        read_only_fields = ['answer', 'sources', 'model_used', 'response_time']


class QARequestSerializer(serializers.Serializer):
    """Serializer for Q&A requests."""
    
    question = serializers.CharField(max_length=2000)
    book_id = serializers.IntegerField(required=False, allow_null=True)
    session_id = serializers.CharField(max_length=100, required=False)
    use_rag = serializers.BooleanField(default=True)
    model = serializers.ChoiceField(
        choices=['openai', 'anthropic', 'lm-studio'],
        default='lm-studio'
    )


class BookRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for book recommendations."""
    
    source_book_title = serializers.CharField(source='source_book.title', read_only=True)
    recommended_book_details = BookListSerializer(source='recommended_book', read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'source_book', 'source_book_title', 'recommended_book',
            'recommended_book_details', 'reason', 'confidence_score',
            'recommendation_type', 'created_at'
        ]


class ScrapingJobSerializer(serializers.ModelSerializer):
    """Serializer for scraping jobs."""
    
    class Meta:
        model = ScrapingJob
        fields = [
            'id', 'source', 'url', 'status', 'books_scraped',
            'error_message', 'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['status', 'books_scraped', 'error_message', 'started_at', 'completed_at']


class ScrapingRequestSerializer(serializers.Serializer):
    """Serializer for scraping requests."""
    
    source = serializers.ChoiceField(choices=['goodreads', 'amazon', 'openlibrary', 'custom'])
    url = serializers.URLField(max_length=500)
    max_books = serializers.IntegerField(default=20, min_value=1, max_value=100)
    async_mode = serializers.BooleanField(default=True)


class AIServiceResponseSerializer(serializers.Serializer):
    """Serializer for AI service responses."""
    
    success = serializers.BooleanField()
    summary = serializers.CharField(allow_null=True)
    genre = serializers.CharField(allow_null=True)
    recommendations = serializers.ListField(child=serializers.DictField(), allow_empty=True)
    sentiment = serializers.DictField(allow_null=True)
    embeddings_generated = serializers.IntegerField()
    chunks_created = serializers.IntegerField()
    error = serializers.CharField(allow_null=True)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response."""
    
    status = serializers.CharField()
    database = serializers.BooleanField()
    chromadb = serializers.BooleanField()
    embedding_model = serializers.CharField()
    llm_available = serializers.BooleanField()
    timestamp = serializers.DateTimeField()
