"""
Books app initialization with Celery support.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
