from django.db import models
from django.utils import timezone


class Book(models.Model):
    """Model representing a book in the system."""
    
    GENRE_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('mystery', 'Mystery'),
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('horror', 'Horror'),
        ('biography', 'Biography'),
        ('self-help', 'Self-Help'),
        ('business', 'Business'),
        ('history', 'History'),
        ('science', 'Science'),
        ('technology', 'Technology'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=500, db_index=True)
    author = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='other', db_index=True)
    isbn = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    publisher = models.CharField(max_length=300, blank=True, null=True)
    published_date = models.CharField(max_length=50, blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    num_ratings = models.IntegerField(default=0)
    num_reviews = models.IntegerField(default=0)
    cover_image_url = models.URLField(max_length=500, blank=True, null=True)
    book_url = models.URLField(max_length=500, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True, help_text="Source website")
    content_text = models.TextField(blank=True, null=True, help_text="Full text content for RAG")
    price = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    tags = models.JSONField(default=list, blank=True)
    ai_insights = models.JSONField(default=dict, blank=True, help_text="AI-generated insights")
    embedding_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    is_processed = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'books'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'author']),
            models.Index(fields=['-rating']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def get_similar_books(self, limit=5):
        """Get similar books based on genre and tags."""
        similar = Book.objects.filter(
            models.Q(genre=self.genre) | models.Q(tags__overlap=self.tags),
            is_processed=True
        ).exclude(pk=self.pk).exclude(rating=None).order_by('-rating')[:limit]
        return similar


class Review(models.Model):
    """Model representing a book review."""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=200, blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=300, blank=True, null=True)
    content = models.TextField()
    sentiment_score = models.FloatField(blank=True, null=True)
    sentiment_label = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.book.title} by {self.reviewer_name}"


class BookChunk(models.Model):
    """Model representing text chunks from books for RAG processing."""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    content = models.TextField()
    embedding_id = models.CharField(max_length=100, db_index=True)
    chunk_type = models.CharField(max_length=50, default='text', help_text="chapter, paragraph, section, etc.")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'book_chunks'
        ordering = ['book', 'chunk_index']
        unique_together = ['book', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.book.title}"


class QAConversation(models.Model):
    """Model for storing Q&A conversations."""
    
    session_id = models.CharField(max_length=100, db_index=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    model_used = models.CharField(max_length=100, blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'qa_conversations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q&A session {self.session_id}"


class ScrapingJob(models.Model):
    """Model for tracking scraping jobs."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    SOURCE_CHOICES = [
        ('goodreads', 'Goodreads'),
        ('amazon', 'Amazon'),
        ('openlibrary', 'Open Library'),
        ('custom', 'Custom URL'),
    ]
    
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    books_scraped = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scraping_jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Scraping job {self.id} - {self.source}"


class BookRecommendation(models.Model):
    """Model for storing AI-generated book recommendations."""
    
    source_book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='recommendations_made')
    recommended_book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='recommended_from')
    reason = models.TextField()
    confidence_score = models.FloatField()
    recommendation_type = models.CharField(max_length=50, default='similar')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'book_recommendations'
        unique_together = ['source_book', 'recommended_book']
    
    def __str__(self):
        return f"{self.source_book.title} -> {self.recommended_book.title}"


class FavoriteBook(models.Model):
    """Model for storing user favorites."""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorite_books'
        unique_together = ['book']
    
    def __str__(self):
        return f"Favorite: {self.book.title}"
