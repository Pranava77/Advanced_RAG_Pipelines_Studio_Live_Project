"""
Hybrid Retriever Engine: Dense FAISS HNSW + Sparse BM25 Okapi + Reciprocal Rank Fusion
Building Advanced RAG Pipelines & Intelligent Q&A Bot
"""

import re
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from .ingestion import DocumentChunk

class ScoredChunk:
    def __init__(self, chunk: DocumentChunk, dense_score: float = 0.0, sparse_score: float = 0.0, rrf_score: float = 0.0, cross_score: float = 0.0):
        self.chunk = chunk
        self.dense_score = dense_score
        self.sparse_score = sparse_score
        self.rrf_score = rrf_score
        self.cross_score = cross_score
        self.rank = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "doc_id": self.chunk.doc_id,
            "doc_title": self.chunk.doc_title,
            "category": self.chunk.category,
            "breadcrumbs": self.chunk.breadcrumbs,
            "text": self.chunk.text,
            "dense_score": round(self.dense_score, 4),
            "sparse_score": round(self.sparse_score, 4),
            "rrf_score": round(self.rrf_score, 5),
            "cross_score": round(self.cross_score, 4),
            "rank": self.rank
        }

class HybridRetrieverEngine:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_name)
        self.embedding_dim = 384
        self.chunks: List[DocumentChunk] = []
        self.chunk_embeddings: Optional[np.ndarray] = None
        self.faiss_index: Optional[faiss.IndexHNSWFlat] = None
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

    def index_corpus(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        self.chunks = chunks

        # 1. Compute Dense Normalized Embeddings
        texts = [c.text for c in chunks]
        self.chunk_embeddings = self.embedder.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        )

        # 2. Build FAISS HNSW Index
        M = 32
        self.faiss_index = faiss.IndexHNSWFlat(self.embedding_dim, M, faiss.METRIC_INNER_PRODUCT)
        self.faiss_index.hnsw.efConstruction = 64
        self.faiss_index.hnsw.efSearch = 32
        self.faiss_index.add(self.chunk_embeddings)

        # 3. Build Sparse BM25 Index
        self.tokenized_corpus = [re.findall(r'\w+', t.lower()) for t in texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        index_time_ms = (time.perf_counter() - t0) * 1000

        return {
            "total_chunks": len(chunks),
            "embedding_dimension": self.embedding_dim,
            "indexing_time_ms": round(index_time_ms, 2),
            "faiss_total_vectors": self.faiss_index.ntotal
        }

    def search_dense(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        q_emb = self.embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.faiss_index.search(q_emb, top_k)
        return list(zip(indices[0], scores[0]))

    def search_sparse(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        tokens = re.findall(r'\w+', query.lower())
        bm25_scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]
        return [(idx, float(bm25_scores[idx])) for idx in top_indices if bm25_scores[idx] > 0]

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        rrf_k: int = 60,
        hyde_text: str = None
    ) -> Dict[str, Any]:
        """
        Executes Reciprocal Rank Fusion over Dense and Sparse candidate lists.
        If hyde_text is provided, uses the hypothetical document for dense vector search.
        """
        t0 = time.perf_counter()

        # Step 1: Dense Retrieval
        dense_query = hyde_text if hyde_text else query
        dense_hits = self.search_dense(dense_query, top_k=top_k * 2)

        # Step 2: Sparse Lexical Retrieval
        sparse_hits = self.search_sparse(query, top_k=top_k * 2)

        # Step 3: Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}
        dense_map: Dict[int, float] = {}
        sparse_map: Dict[int, float] = {}

        for rank, (idx, score) in enumerate(dense_hits, start=1):
            dense_map[idx] = float(score)
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank))

        for rank, (idx, score) in enumerate(sparse_hits, start=1):
            sparse_map[idx] = float(score)
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (rrf_k + rank))

        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        fused_chunks = []
        for rank, (idx, score) in enumerate(sorted_candidates, start=1):
            chunk = self.chunks[idx]
            sc = ScoredChunk(
                chunk=chunk,
                dense_score=dense_map.get(idx, 0.0),
                sparse_score=sparse_map.get(idx, 0.0),
                rrf_score=score
            )
            sc.rank = rank
            fused_chunks.append(sc)

        latency_ms = (time.perf_counter() - t0) * 1000

        # Raw Top-3 dense & sparse for inspection
        raw_dense = [
            {"chunk_id": self.chunks[i].chunk_id, "score": round(float(s), 4), "text": self.chunks[i].text[:140] + "..."}
            for i, s in dense_hits[:3]
        ]
        raw_sparse = [
            {"chunk_id": self.chunks[i].chunk_id, "score": round(float(s), 4), "text": self.chunks[i].text[:140] + "..."}
            for i, s in sparse_hits[:3]
        ]

        return {
            "query": query,
            "latency_ms": round(latency_ms, 2),
            "dense_candidate_count": len(dense_hits),
            "sparse_candidate_count": len(sparse_hits),
            "fused_results": [c.to_dict() for c in fused_chunks],
            "raw_dense_top3": raw_dense,
            "raw_sparse_top3": raw_sparse
        }
