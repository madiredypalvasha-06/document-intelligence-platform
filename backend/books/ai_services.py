"""
AI Services for Document Intelligence Platform
Handles embeddings, LLM integration, and AI insights generation.
"""
import os
import logging
import time
import hashlib
import asyncio
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
from django.conf import settings

import numpy as np
from sentence_transformers import SentenceTransformer
import httpx

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache for AI responses."""
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def clear(self) -> None:
        with self.lock:
            self.cache.clear()


response_cache = LRUCache(max_size=200)


@dataclass
class EmbeddingResult:
    """Container for embedding generation results."""
    embeddings: List[List[float]]
    chunks: List[str]
    embedding_ids: List[str]
    model_name: str
    generation_time: float


@dataclass
class LLMResponse:
    """Container for LLM response."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    finish_reason: str


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.
    
    Uses a singleton pattern to ensure only one model instance is loaded.
    Supports batch processing for efficient embedding generation.
    """
    
    _instance = None  # Singleton instance
    _model = None     # Cached model instance
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service and load the model if not already loaded."""
        if self._model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """
        Initialize the Sentence Transformer model.
        
        Loads the model specified in settings (default: all-MiniLM-L6-v2)
        which is a fast, lightweight model suitable for most use cases.
        """
        model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process at once
            
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        start_time = time.time()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        generation_time = time.time() - start_time
        
        logger.info(f"Generated {len(texts)} embeddings in {generation_time:.2f}s")
        return embeddings
    
    def generate_embedding_with_id(self, text: str) -> Tuple[np.ndarray, str]:
        """
        Generate embedding and return with unique ID.
        
        Args:
            text: Text to embed
            
        Returns:
            Tuple of (embedding array, unique ID hash)
        """
        embedding = self._model.encode([text], convert_to_numpy=True)[0]
        embedding_id = hashlib.md5(text.encode()).hexdigest()
        return embedding, embedding_id
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model."""
        if self._model is None:
            return getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        try:
            return self._model.name_or_path
        except Exception:
            return getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')


class LLMService:
    """
    Service for interacting with LLM APIs.
    
    Supports multiple LLM providers:
    - LM Studio (local, free)
    - OpenAI GPT
    - Anthropic Claude
    
    Automatically falls back to LM Studio if other APIs are unavailable.
    """
    
    def __init__(self):
        """Initialize LLM service with API keys from settings."""
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        self.lm_studio_url = getattr(settings, 'LM_STUDIO_URL', 'http://localhost:1234/v1')
        self.use_lm_studio = getattr(settings, 'USE_LM_STUDIO', True)
    
    async def generate_completion(
        self,
        prompt: str,
        model: str = 'lm-studio',
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate a completion from the LLM."""
        start_time = time.time()
        
        if model == 'openai' and self.openai_key:
            return await self._openai_completion(prompt, max_tokens, temperature, system_prompt, start_time)
        elif model == 'anthropic' and self.anthropic_key:
            return await self._anthropic_completion(prompt, max_tokens, temperature, system_prompt, start_time)
        else:
            return await self._lm_studio_completion(prompt, max_tokens, temperature, system_prompt, start_time)
    
    async def _openai_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        start_time: float
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return LLMResponse(
            content=data['choices'][0]['message']['content'],
            model="gpt-3.5-turbo",
            usage=data.get('usage', {}),
            response_time=time.time() - start_time,
            finish_reason=data['choices'][0].get('finish_reason', 'stop')
        )
    
    async def _anthropic_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        start_time: float
    ) -> LLMResponse:
        """Generate completion using Anthropic API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system_prompt or "You are a helpful assistant.",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return LLMResponse(
            content=data['content'][0]['text'],
            model="claude-3-haiku",
            usage=data.get('usage', {}),
            response_time=time.time() - start_time,
            finish_reason=data.get('stop_reason', 'stop')
        )
    
    async def _lm_studio_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
        start_time: float
    ) -> LLMResponse:
        """Generate completion using LM Studio."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.lm_studio_url}/chat/completions",
                    json={
                        "model": "local-model",
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            return LLMResponse(
                content=data['choices'][0]['message']['content'],
                model=data.get('model', 'local-model'),
                usage=data.get('usage', {}),
                response_time=time.time() - start_time,
                finish_reason=data['choices'][0].get('finish_reason', 'stop')
            )
        except Exception as e:
            logger.warning(f"LM Studio error: {e}")
            fallback_response = self._generate_fallback_response(prompt, system_prompt or "")
            return LLMResponse(
                content=fallback_response,
                model="fallback",
                usage={},
                response_time=time.time() - start_time,
                finish_reason="fallback"
            )
    
    def _generate_fallback_response(self, prompt: str, system_prompt: str) -> str:
        """Generate a helpful fallback response when LLM is unavailable."""
        prompt_lower = prompt.lower()
        
        if "theme" in prompt_lower or "main" in prompt_lower:
            return "Based on the available book information, this appears to explore themes related to human experience, personal growth, and societal dynamics. The specific themes would depend on the individual book's content and narrative."
        
        elif "summary" in prompt_lower or "plot" in prompt_lower:
            return "The book appears to have a compelling narrative structure with developed characters and an engaging storyline. For a detailed summary, please ensure the book content is uploaded or the book has been processed by the system."
        
        elif "recommend" in prompt_lower or "enjoy" in prompt_lower:
            return "This book would appeal to readers who enjoy thought-provoking narratives with well-developed characters. Similar books in the library include other classic fiction titles and contemporary works in the same genre."
        
        elif "character" in prompt_lower:
            return "The book features well-developed characters that drive the narrative forward. Character analysis would require processing the full book content through the AI system."
        
        elif "compare" in prompt_lower or "similar" in prompt_lower:
            return "This book shares similarities with other works in its genre. Similar books in the library include titles with comparable themes, writing styles, and narrative approaches. Check the 'Similar Books' section for recommendations."
        
        elif "takeaway" in prompt_lower or "key" in prompt_lower:
            return "Key takeaways from this book typically include insights into human nature, societal observations, and personal reflections. The specific lessons depend on the book's content and your interpretation."
        
        elif "writing" in prompt_lower or "style" in prompt_lower:
            return "The writing style is engaging and accessible, with descriptive prose that brings the narrative to life. The author employs various literary techniques to enhance the reader's experience."
        
        else:
            return """The AI assistant is currently operating in demo mode because the LLM service (LM Studio) is not available.

To get full AI-powered answers:

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Llama 2, Mistral)
3. Click "Start Server" in LM Studio
4. The system will automatically connect

With LM Studio running, you can ask detailed questions about book content and receive contextual answers with source citations."""


class AIInsightsService:
    """Service for generating AI insights about books."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
    
    def generate_summary(self, text: str, max_length: int = 300) -> str:
        """Generate a summary of the book text."""
        if not text or len(text) < 100:
            return text or ""
        
        prompt = f"""Analyze the following book content and provide a concise summary (maximum {max_length} characters).
        
Focus on:
- Main themes and topics
- Key plot points or arguments
- Target audience

Book Content:
{text[:3000]}

Provide a well-structured summary:"""
        
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.llm_service.generate_completion(
                    prompt,
                    system_prompt="You are an expert book analyst. Provide accurate, concise summaries.",
                    max_tokens=300,
                    temperature=0.5
                )
            )
            return response.content
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def classify_genre(self, title: str, description: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Classify the genre of a book based on its metadata."""
        combined_text = f"Title: {title}\nDescription: {description}"
        if content:
            combined_text += f"\nContent preview: {content[:1000]}"
        
        prompt = f"""Analyze this book and classify its genre. Consider the title, description, and content.

Book Information:
{combined_text}

Classify the book into ONE of these genres:
- fiction: General fiction
- non-fiction: Non-fiction works
- mystery: Mystery and detective stories
- sci-fi: Science fiction
- fantasy: Fantasy fiction
- romance: Romance novels
- thriller: Thriller and suspense
- horror: Horror fiction
- biography: Biographies and memoirs
- self-help: Self-help and personal development
- business: Business and economics
- history: Historical works
- science: Scientific works
- technology: Technology and computing
- other: Doesn't fit other categories

Also provide:
1. Primary genre (single word from the list above)
2. Secondary genres (up to 2 related genres)
3. Confidence score (0.0 to 1.0)
4. Key indicators that led to this classification

Format your response as JSON:"""
        
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                asyncio.wait_for(
                    self.llm_service.generate_completion(
                        prompt,
                        system_prompt="You are a literary genre classification expert. Always respond with valid JSON.",
                        max_tokens=500,
                        temperature=0.3
                    ),
                    timeout=5.0
                )
            )
            
            import json
            result = json.loads(response.content)
            return {
                'primary_genre': result.get('primary_genre', 'other'),
                'secondary_genres': result.get('secondary_genres', []),
                'confidence': result.get('confidence', 0.5),
                'indicators': result.get('indicators', [])
            }
        except asyncio.TimeoutError:
            logger.warning(f"Genre classification timed out for {title}, using rule-based")
            return self._rule_based_genre_classification(title, description)
        except Exception as e:
            logger.error(f"Genre classification error: {e}")
            return self._rule_based_genre_classification(title, description)
    
    def _rule_based_genre_classification(self, title: str, description: str) -> Dict[str, Any]:
        """Fallback rule-based genre classification when LLM is unavailable."""
        text = (title + " " + description).lower()
        
        genre_rules = {
            'sci-fi': {'keywords': ['dystopian', 'space', 'robot', 'future', 'alien', 'time travel', 'science fiction', 'sci-fi', 'virtual reality', 'cyberpunk'], 'weight': 3},
            'fantasy': {'keywords': ['magic', 'wizard', 'dragon', 'elf', 'kingdom', 'fantasy', 'mythical', 'sorcerer', 'hobbit', 'middle-earth', 'warcraft'], 'weight': 3},
            'mystery': {'keywords': ['murder', 'detective', 'investigation', 'crime', 'mystery', 'whodunit', 'clue', 'secret', 'disappearance'], 'weight': 3},
            'thriller': {'keywords': ['thriller', 'suspense', 'psycho', 'killer', 'danger', 'chase', 'terror', 'obsession', 'conspiracy'], 'weight': 2},
            'horror': {'keywords': ['horror', 'scary', 'ghost', 'haunted', 'monster', 'vampire', 'zombie', 'demon', 'supernatural'], 'weight': 3},
            'romance': {'keywords': ['love story', 'romance novel', 'falling in love', 'love affair', 'romantic'], 'weight': 2},
            'biography': {'keywords': ['biography', 'memoir', 'autobiography', 'life story', 'president', 'founder', 'ceo', 'first lady'], 'weight': 3},
            'self-help': {'keywords': ['self-help', 'self help', 'habits', 'happiness', 'motivation', 'productivity', 'mindset', 'effective'], 'weight': 2},
            'business': {'keywords': ['entrepreneur', 'startup', 'management', 'leadership', 'marketing', 'investment', 'ceo', 'business'], 'weight': 2},
            'history': {'keywords': ['history', 'historical', 'war', 'ancient', 'civilization', 'empire', 'world war', 'soldiers'], 'weight': 2},
            'science': {'keywords': ['science', 'physics', 'biology', 'cosmos', 'universe', 'evolution', 'genetic', 'cells', 'medicine'], 'weight': 2},
            'technology': {'keywords': ['technology', 'tech', 'computer', 'software', 'silicon valley', 'apple', 'jobs'], 'weight': 2},
        }
        
        genre_scores = {}
        for genre, data in genre_rules.items():
            for keyword in data['keywords']:
                if keyword in text:
                    genre_scores[genre] = genre_scores.get(genre, 0) + data['weight']
        
        if genre_scores:
            sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
            primary = sorted_genres[0][0]
            secondary = [g[0] for g in sorted_genres[1:3]] if len(sorted_genres) > 1 else []
            return {
                'primary_genre': primary,
                'secondary_genres': secondary,
                'confidence': 0.6,
                'indicators': [g[0] for g in sorted_genres[:3]],
                'method': 'rule-based'
            }
        
        return {
            'primary_genre': 'fiction',
            'secondary_genres': [],
            'confidence': 0.3,
            'indicators': ['default classification'],
            'method': 'rule-based'
        }
    
    def _rule_based_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Rule-based sentiment analysis when LLM is unavailable."""
        if not text:
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'confidence': 0.0, 'tone': 'neutral'}
        
        text_lower = text.lower()
        
        positive_words = ['excellent', 'amazing', 'great', 'wonderful', 'fantastic', 'brilliant', 'superb', 'outstanding', 'masterpiece', 'captivating', 'engaging', 'compelling', 'powerful', 'thought-provoking', 'beautifully', 'beauty', 'love', 'best', 'recommended', 'must-read', 'fascinating', 'insightful', 'profound', 'touching', 'emotional', 'inspiring', 'memorable', 'enjoyable', 'thrilling', 'suspenseful', ' gripping', 'unforgettable']
        negative_words = ['terrible', 'awful', 'horrible', 'boring', 'disappointing', 'poor', 'bad', 'waste', 'slow', 'confusing', 'weak', 'predictable', 'dull', 'tedious', 'painful', 'unbearable', 'nightmare', 'avoid', 'dislike']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            score = 0.3
            label = 'neutral'
            tone = 'neutral and informative'
        elif positive_count > negative_count:
            score = min(0.5 + (positive_count - negative_count) * 0.1, 0.95)
            label = 'positive'
            tone = 'enthusiastic and appreciative'
        else:
            score = max(0.3 - (negative_count - positive_count) * 0.1, 0.05)
            label = 'negative'
            tone = 'critical and disappointed'
        
        return {
            'sentiment_score': round(score, 2),
            'sentiment_label': label,
            'confidence': round(0.5 + total * 0.1, 2),
            'tone': tone,
            'key_phrases': [w for w in ['engaging', 'captivating', 'thought-provoking'] if w in text_lower][:3],
            'method': 'rule-based'
        }
    
    def _generate_recommendations(self, title: str, genre: str, description: str, all_books: List[Dict], limit: int = 5) -> List[Dict]:
        """Generate book recommendations based on genre and description similarity."""
        if not all_books:
            return []
        
        recommendations = []
        desc_lower = description.lower()
        
        genre_keywords = {
            'sci-fi': ['space', 'future', 'dystopian', 'robot', 'alien', 'technology', 'science'],
            'fantasy': ['magic', 'kingdom', 'adventure', 'dragon', 'wizard', 'epic', 'quest'],
            'mystery': ['murder', 'detective', 'crime', 'investigation', 'secret', 'mystery'],
            'thriller': ['suspense', 'danger', 'chase', 'conspiracy', 'obsession', 'twist'],
            'horror': ['horror', 'scary', 'ghost', 'haunted', 'monster', 'supernatural'],
            'romance': ['love', 'romance', 'relationship', 'heart', 'passion', 'wedding'],
            'fiction': ['story', 'life', 'family', 'society', 'human', 'world'],
            'biography': ['life', 'story', 'memoir', 'history', 'career', 'famous'],
            'self-help': ['habit', 'success', 'happiness', 'mindset', 'personal', 'growth'],
            'business': ['business', 'management', 'leadership', 'entrepreneur', 'strategy'],
            'history': ['history', 'war', 'ancient', 'historical', 'civilization', 'empire'],
            'science': ['science', 'discovery', 'research', 'experiment', 'theory', 'universe'],
        }
        
        for book in all_books:
            book_genre = book.get('genre', '').lower()
            book_desc = (book.get('description') or '').lower()
            book_title = book.get('title', '').lower()
            
            similarity_score = 0.0
            
            if book_genre == genre.lower():
                similarity_score += 0.5
            
            if book_genre in genre_keywords:
                for keyword in genre_keywords[book_genre]:
                    if keyword in desc_lower:
                        similarity_score += 0.1
                    if keyword in book_desc:
                        similarity_score += 0.1
            
            desc_words = set(desc_lower.split())
            book_desc_words = set(book_desc.split())
            common = desc_words & book_desc_words
            if len(common) > 3:
                similarity_score += min(len(common) * 0.02, 0.3)
            
            if similarity_score > 0.2:
                reason = self._get_recommendation_reason(genre, book_genre, title, book.get('title', ''))
                recommendations.append({
                    'title': book.get('title', 'Unknown'),
                    'author': book.get('author', 'Unknown Author'),
                    'genre': book_genre,
                    'reason': reason,
                    'match_score': round(similarity_score, 2)
                })
        
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:limit]
    
    def _get_recommendation_reason(self, source_genre: str, target_genre: str, source_title: str, target_title: str) -> str:
        """Generate a reason for why a book is recommended."""
        reasons = [
            f"Shares the {target_genre} genre with {source_title}",
            f"Similar themes to {source_title} will appeal to fans of {target_title}",
            f"If you enjoyed the {target_genre} elements in {source_title}, you'll love {target_title}",
            f"Fans of {source_title} often enjoy {target_title} for its {target_genre} storytelling",
            f"{target_title} offers a fresh take on themes similar to {source_title}",
        ]
        import random
        return random.choice(reasons)
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze the sentiment of text (reviews or description)."""
        if not text:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
        
        prompt = f"""Analyze the sentiment of the following text. Provide a detailed sentiment analysis.

Text:
{text[:2000]}

Return a JSON object with:
1. sentiment_score: A score from -1.0 (very negative) to 1.0 (very positive)
2. sentiment_label: "positive", "negative", or "neutral"
3. confidence: Your confidence in this assessment (0.0 to 1.0)
4. key_phrases: List of 3-5 key phrases that indicate sentiment
5. tone: Brief description of the overall tone (e.g., "enthusiastic", "critical", "mixed")

Format as JSON:"""
        
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.llm_service.generate_completion(
                    prompt,
                    system_prompt="You are a sentiment analysis expert. Always respond with valid JSON.",
                    max_tokens=400,
                    temperature=0.3
                )
            )
            
            import json
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'key_phrases': [],
                'tone': 'unknown',
                'error': str(e)
            }
    
    def generate_recommendations(self, book_data: Dict[str, Any], all_books: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Generate book recommendations based on similarity."""
        source_title = book_data.get('title', '')
        source_genre = book_data.get('genre', '')
        source_description = book_data.get('description', '')
        
        prompt = f"""Based on the following book, recommend similar books from the provided list.

Source Book:
- Title: {source_title}
- Genre: {source_genre}
- Description: {source_description[:500]}

Available Books:
{self._format_books_for_prompt(all_books[:20])}

For each recommended book, provide:
1. Title and Author
2. Reason for recommendation (what makes it similar)
3. Match score (0.0 to 1.0)

Return a JSON array of recommendations (max {limit}):"""
        
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.llm_service.generate_completion(
                    prompt,
                    system_prompt="You are a book recommendation expert. Always respond with valid JSON array.",
                    max_tokens=800,
                    temperature=0.7
                )
            )
            
            import json
            recommendations = json.loads(response.content)
            return recommendations[:limit]
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return []
    
    def _format_books_for_prompt(self, books: List[Dict[str, Any]]) -> str:
        """Format books list for prompt."""
        formatted = []
        for i, book in enumerate(books, 1):
            title = book.get('title', 'Unknown')
            author = book.get('author', 'Unknown')
            genre = book.get('genre', 'Unknown')
            desc = book.get('description', 'No description')[:200]
            formatted.append(f"{i}. {title} by {author} ({genre})\n   {desc}")
        return "\n\n".join(formatted)
    
    async def generate_all_insights(self, book: 'Book') -> Dict[str, Any]:
        """Generate all AI insights for a book."""
        insights = {}
        
        text_for_analysis = book.content_text or book.description or ""
        
        if text_for_analysis and len(text_for_analysis) > 50:
            insights['summary'] = self.generate_summary(text_for_analysis)
        
        insights['genre_analysis'] = self.classify_genre(
            book.title,
            book.description or "",
            book.content_text
        )
        
        if book.reviews.exists():
            reviews_text = "\n".join([r.content for r in book.reviews.all()[:10]])
            insights['review_sentiment'] = self.analyze_sentiment(reviews_text)
        
        insights['generated_at'] = time.time()
        
        return insights


embedding_service = EmbeddingService()
llm_service = LLMService()
insights_service = AIInsightsService()
