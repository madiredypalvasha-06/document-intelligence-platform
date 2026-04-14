"""
Celery configuration for Document Intelligence Platform
Handles background task processing for AI operations, scraping, and insights generation.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('document_intelligence')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure Celery Beat for periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-conversations': {
        'task': 'books.tasks.cleanup_old_conversations',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'refresh-book-recommendations': {
        'task': 'books.tasks.refresh_recommendations',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
}

# Task routing
app.conf.task_routes = {
    'books.tasks.generate_book_insights': {'queue': 'ai_tasks'},
    'books.tasks.scrape_books_task': {'queue': 'scraping'},
    'books.tasks.bulk_generate_insights': {'queue': 'ai_tasks'},
    'books.tasks.process_book_chunks': {'queue': 'ai_tasks'},
}

# Task result settings
app.conf.task_ignore_result = False
app.conf.task_track_started = True
app.conf.result_expires = 3600  # 1 hour

# Worker settings
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f'Request: {self.request!r}')
