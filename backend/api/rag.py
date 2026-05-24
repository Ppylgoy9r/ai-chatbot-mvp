"""
RAG Engine — PDF processing, embeddings, retrieval, and query pipeline.
All AI calls go through Ollama (on-premises, no external APIs).
"""

import re
import json
import time
import logging
from pathlib import Path

import fitz  # PyMuPDF
import requests
from django.conf import settings
from django.db import connection

from .models import (
    KnowledgeDocument, KnowledgeChunk,
    FAQ, NavigationGuide, AIConfig,
)

logger = logging.getLogger(__name__)


# ============================================================
#  Ollama Client
# ============================================================

class OllamaClient:
    """Lightweight client for Ollama REST API (chat + embeddings)."""

    def __init__(self, base_url=None, llm_model=None, embedding_model=None,
                 temperature=None, max_tokens=None):
        # Try DB config first, fall back to Django settings
        try:
            config = AIConfig.get_active()
            self.base_url = (base_url or config.api_base_url).rstrip("/")
            self.llm_model = llm_model or config.model_name
            self.embedding_model = embedding_model or config.embedding_model
            self.temperature = temperature if temperature is not None else config.temperature
            self.max_tokens = max_tokens or config.max_tokens
        except Exception:
            # Fallback to settings.py / .env values
            self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
            self.llm_model = llm_model or settings.OLLAMA_LLM_MODEL
            self.embedding_model = embedding_model or settings.OLLAMA_EMBEDDING_MODEL
            self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
            self.max_tokens = max_tokens or settings.OLLAMA_MAX_TOKENS

    # ---------- Chat (non-streaming) ----------
    def chat(self, messages: list, temperature=None, max_tokens=None) -> str:
        """Single-shot chat completion. Returns full text."""
        payload = {
            "model": self.llm_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    # ---------- Streaming Chat ----------
    def chat_stream(self, messages: list, temperature=None, max_tokens=None):
        """Yield token strings as they arrive from Ollama."""
        payload = {
            "model": self.llm_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        with requests.post(f"{self.base_url}/api/chat", json=payload,
                           stream=True, timeout=180) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    # ---------- Embeddings ----------
    def embed(self, text: str) -> list[float]:
        """Get embedding vector for a single text string."""
        payload = {
            "model": self.embedding_model,
            "prompt": text,
        }
        resp = requests.post(f"{self.base_url}/api/embeddings", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. Ollama doesn't have a native batch endpoint,
        so we call one-by-one (fast enough for MVP document ingestion)."""
        return [self.embed(t) for t in texts]


# ============================================================
#  PDF Processor
# ============================================================

class PDFProcessor:
    """Extract, chunk, embed, and store a PDF document."""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from a PDF file."""
        doc = fitz.open(pdf_path)
        pages = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(f"[Page {page_num + 1}]\n{text}")
        doc.close()
        return "\n\n".join(pages)

    def chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def process_pdf(self, pdf_path: str, title: str, uploaded_by=None) -> KnowledgeDocument:
        """Full pipeline: extract → chunk → embed → store."""
        logger.info(f"Processing PDF: {title}")

        # 1. Extract text
        full_text = self.extract_text(pdf_path)
        if not full_text.strip():
            raise ValueError("PDF appears to be empty or image-only (no extractable text).")

        # 2. Create document record
        doc = KnowledgeDocument.objects.create(
            title=title,
            file=pdf_path if not isinstance(pdf_path, Path) else str(pdf_path),
            uploaded_by=uploaded_by,
        )

        # 3. Chunk
        chunks = self.chunk_text(full_text)
        logger.info(f"Created {len(chunks)} chunks from '{title}'")

        # 4. Embed and store chunks
        client = OllamaClient()
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            try:
                embedding = client.embed(chunk_text)
            except Exception as e:
                logger.warning(f"Embedding failed for chunk {i}: {e}")
                embedding = None

            chunk_obj = KnowledgeChunk(
                document=doc,
                content=chunk_text,
                embedding=embedding,
                chunk_index=i,
                metadata={"page_hint": self._guess_page(chunk_text)},
            )
            chunk_objects.append(chunk_obj)

        KnowledgeChunk.objects.bulk_create(chunk_objects, batch_size=50)
        doc.chunk_count = len(chunk_objects)
        doc.save()

        logger.info(f"Stored {doc.chunk_count} chunks for '{title}'")
        return doc

    @staticmethod
    def _guess_page(chunk: str) -> int:
        """Try to extract page number from chunk header like [Page 5]."""
        match = re.match(r"\[Page (\d+)\]", chunk)
        return int(match.group(1)) if match else 0


# ============================================================
#  Retriever
# ============================================================

class Retriever:
    """Hybrid retriever: FAQ → Navigation → Vector Search."""

    def __init__(self, top_k=None):
        self.top_k = top_k or settings.VECTOR_SEARCH_TOP_K

    def search_faqs(self, query: str) -> list[dict]:
        """Case-insensitive keyword match against FAQ questions."""
        results = []
        for faq in FAQ.objects.all():
            # Simple keyword overlap scoring
            query_words = set(query.lower().split())
            faq_words = set(faq.question.lower().split())
            overlap = len(query_words & faq_words)
            if overlap >= 1:
                results.append({
                    "type": "faq",
                    "score": overlap / max(len(query_words), 1),
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:3]

    def search_navigation(self, query: str) -> list[dict]:
        """Match user question to navigation guides by intent/keyword."""
        results = []
        query_lower = query.lower()
        for guide in NavigationGuide.objects.all():
            # Check if any intent keyword appears in the query
            intent_words = guide.intent.lower().replace("_", " ").split()
            question_words = guide.question.lower().split()
            all_words = set(intent_words + question_words)
            query_words = set(query_lower.split())
            overlap = len(query_words & all_words)
            if overlap >= 1:
                results.append({
                    "type": "navigation",
                    "score": overlap / max(len(query_words), 1),
                    "intent": guide.intent,
                    "question": guide.question,
                    "answer": guide.answer,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:3]

    def search_vectors(self, query: str, top_k=None) -> list[dict]:
        """Semantic vector search using pgvector cosine distance."""
        client = OllamaClient()
        try:
            query_embedding = client.embed(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []

        k = top_k or self.top_k
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kc.id, kc.content, kc.chunk_index, kc.metadata,
                       kd.title AS doc_title,
                       1 - (kc.embedding <=> %s::vector) AS similarity
                FROM knowledge_chunks kc
                JOIN knowledge_documents kd ON kc.document_id = kd.id
                WHERE kc.embedding IS NOT NULL
                ORDER BY kc.embedding <=> %s::vector
                LIMIT %s
                """,
                [str(query_embedding), str(query_embedding), k],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = []
        for row in rows:
            data = dict(zip(columns, row))
            results.append({
                "type": "pdf_chunk",
                "score": float(data["similarity"]) if data["similarity"] else 0.0,
                "content": data["content"],
                "chunk_index": data["chunk_index"],
                "document_title": data["doc_title"],
                "metadata": data["metadata"],
            })
        return results

    def hybrid_search(self, query: str) -> list[dict]:
        """
        Full retrieval pipeline:
        1. Check FAQs for direct match
        2. Check navigation guides
        3. Fall back to vector search on PDF chunks
        """
        # Step 1: FAQ check
        faq_results = self.search_faqs(query)
        if faq_results and faq_results[0]["score"] >= 0.4:
            return faq_results

        # Step 2: Navigation check
        nav_results = self.search_navigation(query)
        if nav_results and nav_results[0]["score"] >= 0.4:
            return nav_results

        # Step 3: Vector search
        vector_results = self.search_vectors(query)

        # Merge all results for context richness
        all_results = faq_results + nav_results + vector_results
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:self.top_k]


# ============================================================
#  Query Pipeline
# ============================================================

RAG_SYSTEM_PROMPT = """You are a helpful AI assistant for a software system. Answer the user's question based on the provided context.

Rules:
- Use ONLY the information from the context below to answer.
- If the context doesn't contain enough information, say so honestly.
- For navigation questions, give step-by-step instructions.
- Be concise but thorough.
- If referencing a document, mention the document name if available.

Context:
{context}
"""


class QueryPipeline:
    """End-to-end query pipeline: retrieve → build prompt → stream response."""

    def __init__(self):
        self.retriever = Retriever()
        self.client = OllamaClient()

    def build_context(self, search_results: list[dict]) -> str:
        """Format search results into a context string for the LLM."""
        context_parts = []
        for i, result in enumerate(search_results, 1):
            if result["type"] == "faq":
                context_parts.append(
                    f"[FAQ] Q: {result['question']}\nA: {result['answer']}"
                )
            elif result["type"] == "navigation":
                context_parts.append(
                    f"[Navigation - {result['intent']}] Q: {result['question']}\nA: {result['answer']}"
                )
            elif result["type"] == "pdf_chunk":
                source = result.get("document_title", "Unknown Document")
                context_parts.append(
                    f"[From: {source}, Chunk {result['chunk_index']}]\n{result['content']}"
                )
        return "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."

    def query(self, user_message: str, chat_history: list[dict] = None) -> dict:
        """Non-streaming query. Returns full response with metadata."""
        start = time.time()

        # Retrieve
        search_results = self.retriever.hybrid_search(user_message)
        context = self.build_context(search_results)

        # Build messages
        messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT.format(context=context)}]
        if chat_history:
            messages.extend(chat_history[-6:])  # Last 3 exchanges (6 messages)
        messages.append({"role": "user", "content": user_message})

        # Generate
        response_text = self.client.chat(messages)
        elapsed = time.time() - start

        return {
            "response": response_text,
            "sources": search_results,
            "response_time": round(elapsed, 2),
        }

    def query_stream(self, user_message: str, chat_history: list[dict] = None, session_id: int = None):
        """Streaming query. Yields SSE-formatted data chunks."""
        start = time.time()

        # Retrieve (synchronous — fast for small datasets)
        search_results = self.retriever.hybrid_search(user_message)
        context = self.build_context(search_results)

        # Build messages
        messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT.format(context=context)}]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_message})

        # Stream
        full_response = []
        for token in self.client.chat_stream(messages):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        elapsed = time.time() - start

        # Send final metadata
        yield f"data: {json.dumps({'done': True, 'response_time': round(elapsed, 2), 'sources': search_results, 'session_id': session_id})}\n\n"
