from django.contrib import admin
from .models import Book, Review, BookChunk, QAConversation, BookRecommendation, ScrapingJob


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'rating', 'is_processed', 'created_at']
    list_filter = ['genre', 'is_processed', 'source', 'is_featured']
    search_fields = ['title', 'author', 'description']
    readonly_fields = ['embedding_id', 'ai_insights', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'genre', 'description', 'summary')
        }),
        ('Publication Details', {
            'fields': ('isbn', 'publisher', 'published_date', 'page_count', 'language')
        }),
        ('Ratings & Reviews', {
            'fields': ('rating', 'num_ratings', 'num_reviews')
        }),
        ('Media & Links', {
            'fields': ('cover_image_url', 'book_url')
        }),
        ('Content & Metadata', {
            'fields': ('content_text', 'source', 'price', 'tags')
        }),
        ('AI Processing', {
            'fields': ('is_processed', 'embedding_id', 'ai_insights', 'is_featured'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'reviewer_name', 'rating', 'sentiment_label', 'created_at']
    list_filter = ['rating', 'sentiment_label', 'source']
    search_fields = ['book__title', 'reviewer_name', 'content']


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    list_display = ['book', 'chunk_index', 'chunk_type', 'embedding_id']
    list_filter = ['chunk_type']
    search_fields = ['book__title']


@admin.register(QAConversation)
class QAConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'book', 'model_used', 'response_time', 'created_at']
    list_filter = ['model_used']
    search_fields = ['session_id', 'question', 'answer']


@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ['source_book', 'recommended_book', 'confidence_score', 'created_at']
    search_fields = ['source_book__title', 'recommended_book__title']


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = ['source', 'status', 'books_scraped', 'started_at', 'completed_at']
    list_filter = ['status', 'source']
    readonly_fields = ['started_at', 'completed_at']
