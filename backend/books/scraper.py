"""
Book Scraper Module
Uses Selenium for automated book data collection from various sources.
"""
import os
import re
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedBook:
    """Container for scraped book data."""
    title: str
    author: str
    description: Optional[str] = None
    rating: Optional[float] = None
    num_ratings: Optional[int] = None
    num_reviews: Optional[int] = None
    cover_url: Optional[str] = None
    book_url: Optional[str] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    page_count: Optional[int] = None
    price: Optional[str] = None
    language: Optional[str] = None
    source: str = 'unknown'


class SeleniumScraper:
    """Base scraper class using Selenium."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_options.page_load_strategy = 'normal'
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            driver.set_page_load_timeout(self.timeout)
            driver.implicitly_wait(5)
            
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def _safe_find_element(self, by: By, value: str, parent=None, multiple: bool = False):
        """Safely find element(s) with error handling."""
        try:
            element = (parent or self.driver).find_element(by, value) if not multiple else (parent or self.driver).find_elements(by, value)
            return element
        except (NoSuchElementException, StaleElementReferenceException):
            return None if not multiple else []
    
    def scroll_page(self, scrolls: int = 3, delay: float = 1.0):
        """Scroll the page to load dynamic content."""
        for _ in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(delay)
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None


class GoodreadsScraper(SeleniumScraper):
    """Scraper for Goodreads website with multi-page support."""
    
    BASE_URL = "https://www.goodreads.com"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
    
    def scrape_books(
        self,
        query: str = "fiction",
        max_books: int = 20
    ) -> List[ScrapedBook]:
        """Scrape books from Goodreads search results with multi-page support."""
        books = []
        books_per_page = 20
        pages_needed = (max_books + books_per_page - 1) // books_per_page
        
        try:
            self.driver = self._setup_driver()
            
            for page in range(1, pages_needed + 1):
                if len(books) >= max_books:
                    break
                
                if page == 1:
                    search_url = f"{self.BASE_URL}/search?q={query}"
                else:
                    search_url = f"{self.BASE_URL}/search?q={query}&page={page}"
                
                logger.info(f"Scraping page {page}: {search_url}")
                self.driver.get(search_url)
                time.sleep(2)
                self.scroll_page(scrolls=2)
                
                try:
                    book_elements = self.driver.find_elements(By.CSS_SELECTOR, "table.detailed > tbody > tr")
                    
                    for i, row in enumerate(book_elements):
                        if len(books) >= max_books:
                            break
                        try:
                            book = self._parse_book_row(row)
                            if book and book.title:
                                books.append(book)
                                logger.info(f"Scraped: {book.title}")
                        except Exception as e:
                            logger.warning(f"Failed to parse book row {i}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Failed to load page {page}: {e}")
                    break
                
        except Exception as e:
            logger.error(f"Goodreads scraping error: {e}")
        finally:
            self.close()
        
        return books[:max_books]
    
    def _parse_book_row(self, row) -> Optional[ScrapedBook]:
        """Parse a book row element."""
        try:
            title_elem = row.find_element(By.CSS_SELECTOR, "a.bookTitle")
            title = title_elem.text.strip()
            book_url = title_elem.get_attribute('href')
            if book_url and not book_url.startswith('http'):
                book_url = urljoin(self.BASE_URL, book_url)
            
            author_elem = row.find_element(By.CSS_SELECTOR, "span.authorName > a")
            author = author_elem.text.strip()
            
            rating_text = row.find_element(By.CSS_SELECTOR, "span.minirating").text
            rating = self._parse_rating(rating_text)
            
            cover_elem = row.find_element(By.CSS_SELECTOR, "img.coverImage")
            cover_url = cover_elem.get_attribute('src')
            
            return ScrapedBook(
                title=title,
                author=author,
                rating=rating,
                book_url=book_url,
                cover_url=cover_url,
                source='goodreads'
            )
        except NoSuchElementException:
            return None
    
    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """Parse rating from text."""
        match = re.search(r'(\d+\.?\d*)', rating_text)
        return float(match.group(1)) if match else None
    
    def scrape_book_details(self, book_url: str) -> Optional[ScrapedBook]:
        """Scrape detailed information for a single book."""
        try:
            self.driver = self._setup_driver()
            self.driver.get(book_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            title_elem = soup.select_one('h1.BookPageTitle')
            title = title_elem.text.strip() if title_elem else ""
            
            author_elem = soup.select_one('span.ContributorLinkName')
            author = author_elem.text.strip() if author_elem else ""
            
            desc_elem = soup.select_one('div.BookPageBookDescription')
            description = desc_elem.text.strip()[:2000] if desc_elem else ""
            
            rating_match = re.search(r'(\d+\.?\d*) out of 5', soup.text)
            rating = float(rating_match.group(1)) if rating_match else None
            
            genre_elem = soup.select_one('a.BookPageMetadataSection-genreLink')
            genre = genre_elem.text.strip() if genre_elem else None
            
            return ScrapedBook(
                title=title,
                author=author,
                description=description,
                rating=rating,
                genre=genre,
                book_url=book_url,
                source='goodreads'
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape book details: {e}")
            return None
        finally:
            self.close()


class OpenLibraryScraper(SeleniumScraper):
    """Scraper for Open Library website."""
    
    BASE_URL = "https://openlibrary.org"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
    
    def scrape_books(
        self,
        query: str = "fiction",
        max_books: int = 20
    ) -> List[ScrapedBook]:
        """Scrape books from Open Library search."""
        books = []
        
        try:
            self.driver = self._setup_driver()
            
            search_url = f"{self.BASE_URL}/search?q={query}"
            logger.info(f"Navigating to: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)
            
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.searchResultItem"))
            )
            
            self.scroll_page(scrolls=2)
            
            book_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.searchResultItem")
            
            for i, card in enumerate(book_cards[:max_books]):
                try:
                    book = self._parse_book_card(card)
                    if book and book.title:
                        books.append(book)
                        logger.info(f"Scraped: {book.title}")
                except Exception as e:
                    logger.warning(f"Failed to parse book card {i}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Open Library scraping error: {e}")
        finally:
            self.close()
        
        return books
    
    def _parse_book_card(self, card) -> Optional[ScrapedBook]:
        """Parse a book card element."""
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, "h3.booktitle a")
            title = title_elem.text.strip()
            book_url = title_elem.get_attribute('href')
            if book_url and not book_url.startswith('http'):
                book_url = urljoin(self.BASE_URL, book_url)
            
            author_elem = card.find_element(By.CSS_SELECTOR, "span.bookauthor a")
            author = author_elem.text.strip()
            
            cover_elem = card.find_element(By.CSS_SELECTOR, "img.cover")
            cover_url = cover_elem.get_attribute('src')
            
            return ScrapedBook(
                title=title,
                author=author,
                book_url=book_url,
                cover_url=cover_url,
                source='openlibrary'
            )
        except NoSuchElementException:
            return None


class AmazonScraper(SeleniumScraper):
    """Scraper for Amazon Books."""
    
    BASE_URL = "https://www.amazon.com"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
    
    def scrape_books(
        self,
        query: str = "bestsellers books",
        max_books: int = 20
    ) -> List[ScrapedBook]:
        """Scrape books from Amazon search."""
        books = []
        
        try:
            self.driver = self._setup_driver()
            
            search_url = f"{self.BASE_URL}/s?k={query.replace(' ', '+')}&i=stripbooks"
            logger.info(f"Navigating to: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(3)
            
            self.scroll_page(scrolls=3)
            
            book_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "div.s-result-item[data-component-type='s-search-result']"
            )
            
            for i, element in enumerate(book_elements[:max_books]):
                try:
                    book = self._parse_book_element(element)
                    if book and book.title:
                        books.append(book)
                        logger.info(f"Scraped: {book.title}")
                except Exception as e:
                    logger.warning(f"Failed to parse Amazon book {i}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Amazon scraping error: {e}")
        finally:
            self.close()
        
        return books
    
    def _parse_book_element(self, element) -> Optional[ScrapedBook]:
        """Parse an Amazon book search result element."""
        try:
            title_elem = element.find_element(By.CSS_SELECTOR, "h2 a span")
            title = title_elem.text.strip()
            
            book_url = element.find_element(By.CSS_SELECTOR, "h2 a").get_attribute('href')
            
            try:
                author = element.find_element(By.CSS_SELECTOR, "span.a-size-medium").text
            except NoSuchElementException:
                author = "Unknown"
            
            try:
                rating_text = element.find_element(By.CSS_SELECTOR, "span.a-icon-alt").text
                rating = float(re.search(r'(\d+\.?\d*)', rating_text).group(1))
            except NoSuchElementException:
                rating = None
            
            try:
                cover_elem = element.find_element(By.CSS_SELECTOR, "img.s-image")
                cover_url = cover_elem.get_attribute('src')
            except NoSuchElementException:
                cover_url = None
            
            return ScrapedBook(
                title=title,
                author=author,
                rating=rating,
                book_url=book_url,
                cover_url=cover_url,
                source='amazon'
            )
        except NoSuchElementException:
            return None


class BookScraperFactory:
    """Factory for creating book scrapers."""
    
    SCRAPERS = {
        'goodreads': GoodreadsScraper,
        'openlibrary': OpenLibraryScraper,
        'amazon': AmazonScraper,
    }
    
    @classmethod
    def create_scraper(cls, source: str, headless: bool = True) -> SeleniumScraper:
        """Create a scraper for the specified source."""
        scraper_class = cls.SCRAPERS.get(source.lower())
        if not scraper_class:
            raise ValueError(f"Unknown scraper source: {source}")
        return scraper_class(headless=headless)
    
    @classmethod
    def get_available_sources(cls) -> List[str]:
        """Get list of available scraper sources."""
        return list(cls.SCRAPERS.keys())


def scrape_books_from_source(
    source: str = 'goodreads',
    query: str = 'fiction',
    max_books: int = 20,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """Scrape books from a specified source and return as dictionaries."""
    scraper = BookScraperFactory.create_scraper(source, headless=headless)
    scraped_books = scraper.scrape_books(query=query, max_books=max_books)
    
    books_data = []
    for book in scraped_books:
        books_data.append({
            'title': book.title,
            'author': book.author,
            'description': book.description,
            'rating': book.rating,
            'num_ratings': book.num_ratings,
            'num_reviews': book.num_reviews,
            'cover_image_url': book.cover_url,
            'book_url': book.book_url,
            'genre': book.genre,
            'isbn': book.isbn,
            'publisher': book.publisher,
            'published_date': book.published_date,
            'page_count': book.page_count,
            'price': book.price,
            'language': book.language,
            'source': book.source,
        })
    
    return books_data
