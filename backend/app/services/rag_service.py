from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path

from app.config import settings
from app.models.session import JobRole


logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._fallback_docs: dict[str, list[str]] = {}
        self._chroma_client = None
        self._collections: dict[str, object] = {}
        self._embedder = None
        self._embedder_attempted = False
        self._ready = False
        self._warned_missing_embedder = False

        try:
            import chromadb

            self._chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        except Exception:
            self._chroma_client = None

    async def ensure_indexes(self) -> None:
        if self._ready:
            return

        async with self._lock:
            if self._ready:
                return
            await self._build_all_indexes()
            self._ready = True

    async def _build_all_indexes(self) -> None:
        for role in JobRole:
            docs = self._load_role_docs(role.value)
            self._fallback_docs[role.value] = docs
            embedder = self._load_embedder()
            if self._chroma_client is not None and docs and embedder is not None:
                await self._index_to_chroma(role.value, docs)

    async def _index_to_chroma(self, role: str, docs: list[str]) -> None:
        collection_name = f"knowledge_{role}"

        def _sync_index() -> None:
            collection = self._chroma_client.get_or_create_collection(
                name=collection_name
            )
            existing_count = collection.count()
            if existing_count > 0:
                self._collections[role] = collection
                return

            ids = [f"{role}-{idx}" for idx in range(len(docs))]
            kwargs: dict[str, object] = {"ids": ids, "documents": docs}
            embedder = self._load_embedder()
            if embedder is not None:
                embeddings = embedder.encode(docs, normalize_embeddings=True).tolist()
                kwargs["embeddings"] = embeddings
            collection.add(**kwargs)
            self._collections[role] = collection

        await asyncio.to_thread(_sync_index)

    def _load_role_docs(self, role: str) -> list[str]:
        role_dir = Path(settings.KNOWLEDGE_BASE_DIR) / role
        if not role_dir.exists():
            return []

        docs: list[str] = []
        for file_path in sorted(role_dir.glob("*.md")) + sorted(role_dir.glob("*.txt")):
            content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            if content:
                docs.append(content)
        return docs

    async def search(self, job_role: str, query: str, top_k: int = 3) -> list[str]:
        await self.ensure_indexes()

        if self._chroma_client is not None and job_role in self._collections:
            results = await self._search_chroma(job_role, query, top_k)
            if results:
                return results

        if self._embedder is None and not self._warned_missing_embedder:
            self._warned_missing_embedder = True
            logger.warning(
                "Embedding model unavailable. RAG search falls back to lexical matching. Set EMBEDDING_MODEL to a valid local path or HuggingFace model id."
            )

        return self._search_fallback(job_role, query, top_k)

    async def _search_chroma(self, job_role: str, query: str, top_k: int) -> list[str]:
        collection = self._collections.get(job_role)
        if collection is None:
            return []

        def _sync_query() -> list[str]:
            kwargs: dict[str, object] = {
                "query_texts": [query],
                "n_results": top_k,
            }
            embedder = self._load_embedder()
            if embedder is not None:
                embedding = embedder.encode([query], normalize_embeddings=True).tolist()
                kwargs = {
                    "query_embeddings": embedding,
                    "n_results": top_k,
                }

            raw = collection.query(**kwargs)
            documents = raw.get("documents") or []
            if not documents:
                return []
            first = documents[0]
            return [item for item in first if isinstance(item, str)]

        return await asyncio.to_thread(_sync_query)

    def _search_fallback(self, job_role: str, query: str, top_k: int) -> list[str]:
        docs = self._fallback_docs.get(job_role, [])
        if not docs:
            return []

        query_terms = [term for term in query.lower().split() if term]
        if not query_terms:
            return docs[:top_k]

        scored: list[tuple[float, str]] = []
        for doc in docs:
            lowered = doc.lower()
            score = sum(lowered.count(term) for term in query_terms)
            score = score / math.sqrt(max(len(lowered), 1))
            scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for score, doc in scored[:top_k] if score > 0] or docs[:top_k]

    def _load_embedder(self):
        if self._embedder_attempted:
            return self._embedder

        self._embedder_attempted = True
        model_ref = settings.EMBEDDING_MODEL.strip()
        if not model_ref:
            self._embedder = None
            return self._embedder

        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            self._embedder = None
            return self._embedder

        candidates: list[tuple[str, dict[str, object]]] = []
        model_path = Path(model_ref)
        if model_path.exists():
            candidates.append((str(model_path), {"local_files_only": True}))
        else:
            candidates.append((model_ref, {"local_files_only": False}))

        if model_ref != "BAAI/bge-small-zh-v1.5":
            candidates.append(("BAAI/bge-small-zh-v1.5", {"local_files_only": False}))

        for candidate, kwargs in candidates:
            try:
                self._embedder = SentenceTransformer(candidate, **kwargs)
                logger.info("RAG embedding model loaded: %s", candidate)
                return self._embedder
            except Exception as exc:
                logger.warning("Failed to load embedding model %s: %s", candidate, exc)

        self._embedder = None

        return self._embedder


rag_service = RAGService()
