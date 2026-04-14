from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('books/load-samples/', views.load_sample_books, name='load-sample-books'),
    path('books/generate-insights/', views.generate_bulk_insights, name='generate-bulk-insights'),
    path('books/upload/', views.BookUploadView.as_view(), name='book-upload'),
    path('books/export/', views.export_books, name='export-books'),
    path('books/favorites/', views.favorites, name='favorites'),
    path('books/favorites/<int:book_id>/', views.remove_favorite, name='remove-favorite'),
    path('books/rate/', views.rate_book, name='rate-book'),
    path('books/search-suggestions/', views.search_suggestions, name='search-suggestions'),
    path('health/', views.health_check, name='health-check'),
    path('qa/', views.QAView.as_view(), name='qa'),
    path('conversations/<str:session_id>/', views.ConversationHistoryView.as_view(), name='conversation-history'),
    path('scrape/', views.ScrapingView.as_view(), name='scrape'),
    path('recommendations/', views.RecommendationView.as_view(), name='recommendations'),
    path('insights/generate/', views.InsightGenerationView.as_view(), name='insights-generate'),
    path('sources/', views.available_sources, name='available-sources'),
    path('', include(router.urls)),
    path('', views.api_root, name='api-root'),
]
