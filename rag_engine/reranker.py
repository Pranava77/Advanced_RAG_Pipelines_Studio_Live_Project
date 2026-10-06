"""
Cross-Encoder Re-Ranking Engine: Deep Transformer Joint Attention Scoring
Building Advanced RAG Pipelines & Intelligent Q&A Bot
"""

import time
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
        """
        Re-ranks hybrid RRF candidates using joint query-document cross-attention.
        Tracks initial rank vs post-reranking rank to measure rank shifts.
        """
        if not candidates:
            return {"reranked": [], "latency_ms": 0.0}

        t0 = time.perf_counter()
        pairs = [[query, c["text"]] for c in candidates]
        cross_scores = self.model.predict(pairs)

        for i, c in enumerate(candidates):
            c["initial_rank"] = c.get("rank", i + 1)
            c["cross_score"] = float(cross_scores[i])

        reranked = sorted(candidates, key=lambda x: x["cross_score"], reverse=True)[:top_k]

        for final_rank, c in enumerate(reranked, start=1):
            c["final_rank"] = final_rank
            c["rank_shift"] = c["initial_rank"] - final_rank  # positive means moved up!

        duration_ms = (time.perf_counter() - t0) * 1000

        return {
            "reranked": reranked,
            "latency_ms": round(duration_ms, 2),
            "top_score": round(reranked[0]["cross_score"], 4) if reranked else 0.0,
            "candidates_evaluated": len(candidates)
        }
