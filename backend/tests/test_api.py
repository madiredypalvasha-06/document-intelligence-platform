"""
Tests for the Document Intelligence Platform API
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from books.models import Book


class BookModelTest(TestCase):
    """Test cases for Book model."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            description="A test book description",
            genre="fiction",
            rating=4.5,
            num_ratings=100
        )

    def test_book_creation(self):
        """Test that a book can be created."""
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.author, "Test Author")
        self.assertEqual(self.book.genre, "fiction")

    def test_book_str(self):
        """Test book string representation."""
        self.assertEqual(str(self.book), "Test Book by Test Author")

    def test_get_similar_books(self):
        """Test getting similar books."""
        similar_book = Book.objects.create(
            title="Another Book",
            author="Another Author",
            genre="fiction",
            rating=4.0
        )
        
        similar = self.book.get_similar_books(limit=5)
        self.assertEqual(len(similar), 1)
        self.assertEqual(similar[0].id, similar_book.id)


class BookAPITest(APITestCase):
    """Test cases for Book API endpoints."""

    def setUp(self):
        self.book = Book.objects.create(
            title="API Test Book",
            author="API Author",
            description="An API test book",
            genre="mystery",
            rating=4.2,
            num_ratings=50
        )

    def test_list_books(self):
        """Test listing all books."""
        url = reverse('book-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_book_detail(self):
        """Test getting book details."""
        url = reverse('book-detail', kwargs={'pk': self.book.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "API Test Book")

    def test_create_book(self):
        """Test creating a new book."""
        url = reverse('book-list')
        data = {
            'title': 'New Book',
            'author': 'New Author',
            'genre': 'sci-fi'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_search_books(self):
        """Test searching books."""
        url = reverse('book-list') + '?search=API'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_genre(self):
        """Test filtering books by genre."""
        url = reverse('book-list') + '?genre=mystery'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class HealthCheckTest(APITestCase):
    """Test cases for health check endpoint."""

    def test_health_check(self):
        """Test health check endpoint."""
        url = reverse('health-check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)


class ScrapingTest(APITestCase):
    """Test cases for scraping functionality."""

    def test_available_sources(self):
        """Test getting available scraping sources."""
        url = reverse('available-sources')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sources', response.data)
