"""
RAG (Retrieval-Augmented Generation) Pipeline for Document Intelligence Platform
Handles document chunking, vector storage, and contextual answer generation.
"""
import os
import re
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.conf import settings

import numpy as np

from .ai_services import embedding_service, llm_service, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk from a document."""
    content: str
    chunk_index: int
    chunk_type: str
    metadata: Dict[str, Any]
    embedding_id: str


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with similarity score."""
    chunk: Chunk
    similarity_score: float
    book_id: Optional[int] = None
    book_title: Optional[str] = None


@dataclass
class RAGResponse:
    """Container for RAG pipeline response."""
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    response_time: float
    retrieved_chunks: int
    confidence: float


class TextChunker:
    """Handles intelligent text chunking with various strategies."""
    
    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100,
        strategy: str = 'semantic'
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """Split text into chunks using the specified strategy."""
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        if self.strategy == 'semantic':
            return self._semantic_chunking(text, metadata)
        elif self.strategy == 'recursive':
            return self._recursive_chunking(text, metadata)
        elif self.strategy == 'paragraph':
            return self._paragraph_chunking(text, metadata)
        elif self.strategy == 'sentence':
            return self._sentence_chunking(text, metadata)
        else:
            return self._fixed_size_chunking(text, metadata)
    
    def _semantic_chunking(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text based on semantic boundaries (paragraphs, sections)."""
        chunks = []
        
        sections = re.split(r'\n\s*\n', text)
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            section_length = len(section.split())
            
            if current_length + section_length > self.chunk_size and current_chunk:
                chunk_content = ' '.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    chunk_type='section',
                    metadata={**metadata, 'type': 'semantic'},
                    embedding_id=self._generate_embedding_id(chunk_content)
                ))
                chunk_index += 1
                current_chunk = []
                current_length = 0
            
            current_chunk.append(section)
            current_length += section_length
        
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                chunk_type='section',
                metadata={**metadata, 'type': 'semantic'},
                embedding_id=self._generate_embedding_id(chunk_content)
            ))
        
        return chunks
    
    def _recursive_chunking(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text recursively using multiple delimiters."""
        separators = ['\n\n', '\n', '. ', ' ']
        chunks = []
        
        def split_text(text: str, sep_idx: int = 0) -> List[str]:
            if sep_idx >= len(separators):
                return [text] if text.strip() else []
            
            separator = separators[sep_idx]
            parts = text.split(separator)
            
            current_part = []
            current_length = 0
            result = []
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                part_length = len(part.split())
                
                if current_length + part_length > self.chunk_size and current_part:
                    result.append(separator.join(current_part))
                    overlap_parts = separator.join(current_part).split()[-self.overlap:]
                    current_part = [' '.join(overlap_parts), part]
                    current_length = len(current_part)
                else:
                    current_part.append(part)
                    current_length += part_length
            
            if current_part:
                result.append(separator.join(current_part))
            
            if any(len(p.split()) > self.chunk_size for p in result) and sep_idx < len(separators) - 1:
                return split_text(text, sep_idx + 1)
            
            return result
        
        split_texts = split_text(text)
        
        for i, chunk_text in enumerate(split_texts):
            if chunk_text.strip():
                chunks.append(Chunk(
                    content=chunk_text.strip(),
                    chunk_index=i,
                    chunk_type='recursive',
                    metadata={**metadata, 'separator_used': separators[min(i % 4, 3)]},
                    embedding_id=self._generate_embedding_id(chunk_text)
                ))
        
        return chunks
    
    def _paragraph_chunking(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text by paragraphs."""
        paragraphs = text.split('\n')
        chunks = []
        current_paragraphs = []
        current_length = 0
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para.split())
            
            if current_length + para_length > self.chunk_size and current_paragraphs:
                chunks.append(Chunk(
                    content='\n'.join(current_paragraphs),
                    chunk_index=chunk_index,
                    chunk_type='paragraph',
                    metadata=metadata,
                    embedding_id=self._generate_embedding_id('\n'.join(current_paragraphs))
                ))
                chunk_index += 1
                current_paragraphs = []
                current_length = 0
            
            current_paragraphs.append(para)
            current_length += para_length
        
        if current_paragraphs:
            chunks.append(Chunk(
                content='\n'.join(current_paragraphs),
                chunk_index=chunk_index,
                chunk_type='paragraph',
                metadata=metadata,
                embedding_id=self._generate_embedding_id('\n'.join(current_paragraphs))
            ))
        
        return chunks
    
    def _sentence_chunking(self, text: str, metadata: Dict) -> List[Chunk]:
        """Split text by sentences with overlapping windows."""
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(sentences):
            end_idx = start_idx
            current_sentences = []
            current_length = 0
            
            while end_idx < len(sentences) and current_length < self.chunk_size:
                current_sentences.append(sentences[end_idx])
                current_length += len(sentences[end_idx].split())
                end_idx += 1
            
            if current_sentences:
                chunks.append(Chunk(
                    content=' '.join(current_sentences),
                    chunk_index=len(chunks),
                    chunk_type='sentence',
                    metadata={**metadata, 'sentence_range': (start_idx, end_idx)},
                    embedding_id=self._generate_embedding_id(' '.join(current_sentences))
                ))
            
            start_idx = max(start_idx + 1, end_idx - self.overlap)
        
        return chunks
    
    def _fixed_size_chunking(self, text: str, metadata: Dict) -> List[Chunk]:
        """Simple fixed-size chunking with overlap."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            if chunk_words:
                chunks.append(Chunk(
                    content=' '.join(chunk_words),
                    chunk_index=len(chunks),
                    chunk_type='fixed',
                    metadata={**metadata, 'word_range': (i, i + len(chunk_words))},
                    embedding_id=self._generate_embedding_id(' '.join(chunk_words))
                ))
        
        return chunks
    
    def _generate_embedding_id(self, content: str) -> str:
        """Generate a unique ID for embedding."""
        return hashlib.md5(content.encode()).hexdigest()


class ChromaVectorStore:
    """Handles vector storage operations using ChromaDB."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client = None
        self._collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            
            chroma_path = getattr(settings, 'CHROMA_DB_PATH', str(settings.BASE_DIR / 'chroma_db' / 'data'))
            
            os.makedirs(chroma_path, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=chroma_path
            )
            
            self._collection = self._client.get_or_create_collection(
                name="book_chunks",
                metadata={"description": "Book content chunks for RAG"}
            )
            
            logger.info(f"ChromaDB initialized at {chroma_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self._client = None
            self._collection = None
    
    def is_available(self) -> bool:
        """Check if ChromaDB is available."""
        return self._collection is not None
    
    def add_chunks(
        self,
        chunks: List[Chunk],
        book_id: int,
        book_title: str
    ) -> bool:
        """Add document chunks to the vector store."""
        if not self._collection or not chunks:
            return False
        
        try:
            embeddings = embedding_service.generate_embeddings(
                [chunk.content for chunk in chunks]
            )
            
            ids = [f"book_{book_id}_chunk_{chunk.chunk_index}" for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "book_id": book_id,
                    "book_title": book_title,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    **chunk.metadata
                }
                for chunk in chunks
            ]
            
            self._collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks for book {book_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            return False
    
    def search(
        self,
        query: str,
        book_id: Optional[int] = None,
        limit: int = 5,
        threshold: float = 0.0
    ) -> List[RetrievedChunk]:
        """Search for relevant chunks using vector similarity."""
        if not self._collection:
            return []
        
        try:
            query_embedding = embedding_service.generate_embeddings([query])[0]
            
            where_filter = {"book_id": book_id} if book_id else None
            
            results = self._collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            retrieved_chunks = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0.0
                    similarity = 1.0 - distance if distance else 0.0
                    
                    if similarity >= threshold:
                        metadata = results['metadatas'][0][i] if 'metadatas' in results else {}
                        
                        chunk = Chunk(
                            content=doc,
                            chunk_index=metadata.get('chunk_index', i),
                            chunk_type=metadata.get('chunk_type', 'unknown'),
                            metadata=metadata,
                            embedding_id=f"book_{metadata.get('book_id', 0)}_chunk_{metadata.get('chunk_index', i)}"
                        )
                        
                        retrieved_chunks.append(RetrievedChunk(
                            chunk=chunk,
                            similarity_score=similarity,
                            book_id=metadata.get('book_id'),
                            book_title=metadata.get('book_title')
                        ))
            
            return retrieved_chunks
        
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []
    
    def delete_book_chunks(self, book_id: int) -> bool:
        """Delete all chunks for a specific book."""
        if not self._collection:
            return False
        
        try:
            self._collection.delete(where={"book_id": book_id})
            logger.info(f"Deleted chunks for book {book_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self._collection:
            return {"available": False}
        
        try:
            count = self._collection.count()
            return {
                "available": True,
                "total_chunks": count,
                "collection_name": self._collection.name
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


class RAGPipeline:
    """Complete RAG pipeline for question answering."""
    
    def __init__(self):
        self.chunker = TextChunker(
            chunk_size=500,
            overlap=50,
            strategy='semantic'
        )
        self.vector_store = ChromaVectorStore()
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    async def process_document(
        self,
        book_id: int,
        book_title: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[int, List[str]]:
        """Process a document and add its chunks to the vector store."""
        metadata = metadata or {}
        metadata['book_id'] = book_id
        metadata['book_title'] = book_title
        
        chunks = self.chunker.chunk_text(content, metadata)
        
        if chunks:
            self.vector_store.add_chunks(chunks, book_id, book_title)
        
        return len(chunks), [chunk.embedding_id for chunk in chunks]
    
    def construct_context(self, retrieved_chunks: List[RetrievedChunk]) -> str:
        """Construct a context string from retrieved chunks."""
        if not retrieved_chunks:
            return "No relevant context found."
        
        context_parts = []
        
        for i, rc in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Source {i}] From '{rc.book_title}' (relevance: {rc.similarity_score:.2f}):\n"
                f"{rc.chunk.content}"
            )
        
        return "\n\n".join(context_parts)
    
    def construct_prompt(
        self,
        question: str,
        context: str,
        book_title: Optional[str] = None
    ) -> Tuple[str, str]:
        """Construct the prompt for the LLM."""
        system_prompt = """You are a helpful AI assistant specialized in answering questions about books.
Your role is to provide accurate, detailed answers based ONLY on the provided context.

Guidelines:
1. Answer based strictly on the provided context
2. If the context doesn't contain enough information, say so
3. Cite your sources using [Source N] notation
4. Be helpful, informative, and conversational
5. If you're unsure about something, admit it
6. Format your response clearly with appropriate structure
"""
        
        if book_title:
            system_prompt += f"\nThe user is asking about the book: '{book_title}'"
        
        user_prompt = f"""Context from relevant book passages:

{context}

---

User Question: {question}

Please provide a comprehensive answer based on the context above. Include relevant citations."""
        
        return system_prompt, user_prompt
    
    async def answer_question(
        self,
        question: str,
        book_id: Optional[int] = None,
        book_title: Optional[str] = None,
        book_description: Optional[str] = None,
        book_ai_insights: Optional[Dict[str, Any]] = None,
        book_price: Optional[str] = None,
        book_author: Optional[str] = None,
        model: str = 'lm-studio',
        use_rag: bool = True,
        max_sources: int = 5
    ) -> RAGResponse:
        """Answer a question using the RAG pipeline."""
        start_time = time.time()
        
        sources = []
        retrieved_chunks = []
        context = ""
        
        has_insights = book_ai_insights and (book_ai_insights.get('summary') or book_ai_insights.get('genre_analysis'))
        
        if has_insights:
            context_parts = []
            if book_title:
                context_parts.append(f"Book Title: {book_title}")
            if book_author:
                context_parts.append(f"Book Author: {book_author}")
            if book_description:
                context_parts.append(f"Book Description: {book_description}")
            if book_price:
                context_parts.append(f"Book Price: {book_price}")
            if book_ai_insights:
                if 'summary' in book_ai_insights:
                    context_parts.append(f"Book Summary: {book_ai_insights['summary']}")
                if 'genre_analysis' in book_ai_insights:
                    ga = book_ai_insights['genre_analysis']
                    context_parts.append(f"Genre: {ga.get('primary_genre', 'Unknown').title()}")
                    if 'secondary_genres' in ga and ga['secondary_genres']:
                        context_parts.append(f"Related Genres: {', '.join(g.title() for g in ga['secondary_genres'])}")
                    if 'indicators' in ga and ga['indicators']:
                        context_parts.append(f"Key Themes: {', '.join(ga['indicators'])}")
                if 'review_sentiment' in book_ai_insights:
                    rs = book_ai_insights['review_sentiment']
                    context_parts.append(f"Reader Reception: {rs.get('sentiment_label', 'Unknown')} (positive score: {rs.get('sentiment_score', 0):.0%})")
                    if 'tone' in rs:
                        context_parts.append(f"Tone: {rs['tone']}")
            context = "\n".join(context_parts)
        elif use_rag and self.vector_store.is_available():
            retrieved_chunks = self.vector_store.search(
                query=question,
                book_id=book_id,
                limit=max_sources
            )
            
            context = self.construct_context(retrieved_chunks)
            
            for i, rc in enumerate(retrieved_chunks):
                sources.append({
                    'book_id': rc.book_id,
                    'book_title': rc.book_title,
                    'content_preview': rc.chunk.content[:200] + "...",
                    'relevance_score': rc.similarity_score,
                    'chunk_type': rc.chunk.chunk_type
                })
        
        if not context:
            if book_title:
                return RAGResponse(
                    answer=f"I don't have detailed information about '{book_title}' in my database. The book exists in our library but I don't have the full content or AI-generated insights yet. You can try uploading the full book content for a more detailed analysis.",
                    sources=[],
                    model_used="no-context",
                    response_time=time.time() - start_time,
                    retrieved_chunks=0,
                    confidence=0.0
                )
            else:
                return RAGResponse(
                    answer="I don't have enough context to answer this question. Please select a specific book first.",
                    sources=[],
                    model_used="no-context",
                    response_time=time.time() - start_time,
                    retrieved_chunks=0,
                    confidence=0.0
                )
        
        if has_insights:
            response = self._generate_answer_from_insights(question, book_title, book_ai_insights, book_price, book_author)
        else:
            system_prompt, user_prompt = self.construct_prompt(question, context, book_title)
            response = await self.llm_service.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model,
                max_tokens=1000,
                temperature=0.7
            )
            if response.model == "fallback":
                response = self._generate_answer_from_insights(question, book_title, book_ai_insights or {}, book_price, book_author)
        
        avg_relevance = (
            sum(rc.similarity_score for rc in retrieved_chunks) / len(retrieved_chunks)
            if retrieved_chunks else 0.0
        )
        
        return RAGResponse(
            answer=response.content,
            sources=sources,
            model_used=response.model,
            response_time=time.time() - start_time,
            retrieved_chunks=len(retrieved_chunks),
            confidence=avg_relevance if retrieved_chunks else 1.0
        )
    
    def _generate_answer_from_insights(
        self,
        question: str,
        book_title: Optional[str],
        ai_insights: Dict[str, Any],
        book_price: Optional[str] = None,
        book_author: Optional[str] = None
    ) -> LLMResponse:
        """Generate answer based on the specific question asked."""
        import time
        start_time = time.time()
        prompt_lower = question.lower()
        
        answer_parts = []
        
        if book_title:
            answer_parts.append(f"# {book_title}\n\n")
        
        # Price question
        if any(word in prompt_lower for word in ['price', 'cost', 'how much', 'expensive']):
            if book_price:
                answer_parts.append(f"## Price\n**Current Price: {book_price}**\n\n")
                answer_parts.append(f"This book is available for {book_price}. Prices may vary between retailers.\n\n")
            else:
                answer_parts.append("## Price\n")
                answer_parts.append("Price information is not available. Please check major retailers for current pricing.\n\n")
        
        # Author question
        elif any(word in prompt_lower for word in ['author', 'wrote', 'written', 'who wrote']):
            if book_author:
                answer_parts.append(f"## Author\n**{book_author}** is the author of this book.\n\n")
            else:
                answer_parts.append("## Author\n")
                answer_parts.append("Author information is not available in the database.\n\n")
        
        # Summary question
        elif any(word in prompt_lower for word in ['summary', 'about', 'what is', 'what\'s', 'tell me', 'gist', 'overview']):
            if 'summary' in ai_insights:
                answer_parts.append(f"## Summary\n{ai_insights['summary']}\n\n")
            else:
                answer_parts.append("No summary available for this book.\n\n")
        
        # Genre question
        elif any(word in prompt_lower for word in ['genre', 'type', 'category', 'kind']):
            if 'genre_analysis' in ai_insights:
                ga = ai_insights['genre_analysis']
                genre = ga.get('primary_genre', 'Fiction').title()
                answer_parts.append(f"## Genre\n**Primary Genre:** {genre}\n")
                if 'secondary_genres' in ga and ga['secondary_genres']:
                    answer_parts.append(f"**Related Genres:** {', '.join(g.title() for g in ga['secondary_genres'])}\n")
                if 'indicators' in ga and ga['indicators']:
                    answer_parts.append(f"**Key Themes:** {', '.join(ga['indicators'])}\n")
            answer_parts.append("\n")
        
        # Themes question
        elif any(word in prompt_lower for word in ['theme', 'themes', 'topic', 'topics', 'message', 'main', 'key']):
            answer_parts.append("## Main Themes\n")
            themes_found = []
            if 'summary' in ai_insights:
                summary_lower = ai_insights['summary'].lower()
                if any(w in summary_lower for w in ['love', 'relationship', 'romance']): themes_found.append("Love and Relationships")
                if any(w in summary_lower for w in ['death', 'die', 'loss', 'grief']): themes_found.append("Mortality and Loss")
                if any(w in summary_lower for w in ['society', 'social', 'class']): themes_found.append("Social Commentary")
                if any(w in summary_lower for w in ['power', 'control', 'government']): themes_found.append("Power and Control")
                if any(w in summary_lower for w in ['identity', 'self', 'discover']): themes_found.append("Identity and Self-Discovery")
                if any(w in summary_lower for w in ['adventure', 'journey', 'quest', 'travel']): themes_found.append("Adventure and Discovery")
                if any(w in summary_lower for w in ['dystopian', 'future', 'technology']): themes_found.append("Technology and Society")
            if themes_found:
                for theme in themes_found:
                    answer_parts.append(f"- **{theme}**\n")
            else:
                answer_parts.append("This book explores various themes that are revealed through its narrative.\n")
            answer_parts.append("\n")
        
        # Recommendations/Similar books
        elif any(word in prompt_lower for word in ['recommend', 'similar', 'like', 'also', 'other books', 'if you like']):
            if 'recommendations' in ai_insights and ai_insights['recommendations']:
                answer_parts.append("## Similar Books\n")
                answer_parts.append("If you enjoyed this book, you might also like:\n\n")
                for i, r in enumerate(ai_insights['recommendations'][:5], 1):
                    if 'title' in r:
                        author = r.get('author', 'Unknown Author')
                        reason = r.get('reason', '')
                        answer_parts.append(f"{i}. **{r['title']}** by {author}\n")
                        if reason:
                            answer_parts.append(f"   → {reason}\n")
            else:
                answer_parts.append("No similar book recommendations available.\n\n")
        
        # Sentiment/Reviews
        elif any(word in prompt_lower for word in ['sentiment', 'review', 'reviews', 'opinion', 'feel', 'reaction']):
            if 'review_sentiment' in ai_insights:
                rs = ai_insights['review_sentiment']
                sentiment = rs.get('sentiment_label', 'Mixed').title()
                score = rs.get('sentiment_score', 0)
                tone = rs.get('tone', 'neutral')
                answer_parts.append(f"## Reader Reception\n")
                answer_parts.append(f"**Overall Reception:** {sentiment} ({score:.0%} positive)\n")
                answer_parts.append(f"**Tone:** {tone.title()}\n")
                if 'key_phrases' in rs and rs['key_phrases']:
                    answer_parts.append(f"**Notable Phrases:** {', '.join(rs['key_phrases'])}\n")
            else:
                answer_parts.append("No review sentiment data available.\n\n")
        
        # Characters
        elif any(word in prompt_lower for word in ['character', 'characters', 'protagonist', 'hero', 'villain', 'cast', 'who are']):
            answer_parts.append("## Characters\n")
            answer_parts.append("This book features memorable characters that drive the narrative. ")
            if 'summary' in ai_insights:
                answer_parts.append("Each character brings unique perspectives that add depth to the story.\n")
            answer_parts.append("For detailed character analyses, explore the full book content.\n\n")
        
        # Rating
        elif any(word in prompt_lower for word in ['rating', 'rate', 'rated', 'score', 'stars']):
            if 'genre_analysis' in ai_insights:
                ga = ai_insights['genre_analysis']
                confidence = ga.get('confidence', 0)
                answer_parts.append(f"## Rating Information\n")
                answer_parts.append(f"**Genre Classification Confidence:** {confidence:.0%}\n")
                answer_parts.append(f"**Primary Genre:** {ga.get('primary_genre', 'Fiction').title()}\n\n")
            else:
                answer_parts.append("No rating information available.\n\n")
        
        # Ending/Conclusion
        elif any(word in prompt_lower for word in ['ending', 'final', 'conclusion', 'twist', 'resolution', 'how does it end']):
            answer_parts.append("## The Ending\n")
            if 'summary' in ai_insights:
                answer_parts.append("The conclusion brings together the narrative threads. ")
                answer_parts.append("Many readers find the ending thought-provoking and open to interpretation.\n\n")
            else:
                answer_parts.append("The ending details are not available. Read the full book to discover it!\n\n")
        
        # Author question
        elif any(word in prompt_lower for word in ['author', 'wrote', 'written', 'who wrote']):
            answer_parts.append("## Author\n")
            answer_parts.append("The author information is available in the book's metadata. ")
            answer_parts.append("Please check the book details page for the author's name.\n\n")
        
        # Catch all - general info
        else:
            if 'summary' in ai_insights:
                answer_parts.append(f"## Summary\n{ai_insights['summary']}\n\n")
            if 'genre_analysis' in ai_insights:
                ga = ai_insights['genre_analysis']
                answer_parts.append(f"## Genre\n**Primary Genre:** {ga.get('primary_genre', 'Fiction').title()}\n\n")
            if book_price:
                answer_parts.append(f"## Price\n**Current Price: {book_price}**\n\n")
        
        if not answer_parts or len(answer_parts) <= 2:
            answer_parts.append("## Quick Info\n")
            if 'summary' in ai_insights:
                answer_parts.append(f"{ai_insights['summary']}\n")
        
        return LLMResponse(
            content="".join(answer_parts).strip(),
            model="insights",
            usage={},
            response_time=time.time() - start_time,
            finish_reason="insights"
        )


rag_pipeline = RAGPipeline()
chroma_store = ChromaVectorStore()
