"""
Advanced RAG Pipelines & Intelligent Q&A Bot Studio AI - FastAPI Server (Port 8195)
Building RAG Pipelines, Advanced RAG Techniques, Re-Ranking, HyDE & Evaluation
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag_engine import (
    IngestionEngine,
    DocumentChunk,
    QueryTransformationEngine,
    HybridRetrieverEngine,
    CrossEncoderReranker,
    GroundedGeneratorEngine,
    RAGEvaluationEngine
)

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")

app = FastAPI(
    title="Advanced RAG Pipelines & Intelligent Q&A Bot Studio AI",
    description="Full-stack enterprise engineering studio for Advanced RAG, HyDE, Hybrid Search, Re-Ranking & Evaluation",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize algorithmic engines
ingestion_engine = IngestionEngine(chunk_size=500)
query_transform_engine = QueryTransformationEngine()
hybrid_retriever = HybridRetrieverEngine(model_name="sentence-transformers/all-MiniLM-L6-v2")
reranker_engine = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
generator_engine = GroundedGeneratorEngine()
evaluation_engine = RAGEvaluationEngine()

# Ingest and index existing corpus on boot
chunks_global, doc_catalog_global = ingestion_engine.load_directory(DATA_DIR)
index_info_global = hybrid_retriever.index_corpus(chunks_global)

print(f"🚀 Initialized Advanced RAG Studio: Indexed {len(chunks_global)} chunks from {len(doc_catalog_global)} documents.")

# Pydantic Request Models
class QARequest(BaseModel):
    query: str = Field(..., min_length=3)
    use_hyde: bool = Field(default=True)
    use_reranker: bool = Field(default=True)
    top_k: int = Field(default=3, ge=1, le=10)

class TransformRequest(BaseModel):
    query: str = Field(..., min_length=3)

class TraceRequest(BaseModel):
    query: str = Field(..., min_length=3)
    use_hyde: bool = Field(default=True)
    use_reranker: bool = Field(default=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Advanced RAG Studio</h1><p>Template loading...</p>")

@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": "Advanced RAG Pipelines & Intelligent Q&A Bot Studio AI",
        "port": 8195,
        "total_documents": len(doc_catalog_global),
        "total_chunks": len(chunks_global),
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2 (384-dim)",
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "vector_index": "FAISS IndexHNSWFlat (M=32, efSearch=32)"
    }

@app.get("/api/overview")
async def api_overview():
    return {
        "title": "Advanced RAG Pipelines & Intelligent Q&A Bot Studio AI",
        "competencies": [
            "End-to-End Pipeline (Ingest -> Chunk AST -> Embed -> Retrieve -> Re-Rank -> Generate)",
            "Query Transformation: Multi-Query Expansion, HyDE & Sub-Query Decomposition",
            "Hybrid Search: Dense Vector + Sparse BM25 via Reciprocal Rank Fusion (RRF, k=60)",
            "Cross-Encoder Re-Ranking: Joint Cross-Attention for Top-K Precision Lift",
            "Grounded Provenance: Context Assembly with Inline Bracketed Citations [Source X]",
            "Contrastive Hallucination Elimination: Parametric Fabrication vs Grounded Truth",
            "Automated RAG Triad Evaluation: Context Relevancy, Faithfulness, Answer Relevancy"
        ],
        "documents": doc_catalog_global,
        "index_info": index_info_global
    }

@app.get("/api/documents")
async def api_documents():
    return {
        "total_documents": len(doc_catalog_global),
        "documents": doc_catalog_global
    }

@app.post("/api/documents/upload")
async def api_upload_document(file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode("utf-8")
        filename = file.filename or "uploaded_doc.md"
        doc_id = filename.replace(".md", "").replace(" ", "_").lower()

        # Save to disk
        fpath = os.path.join(DATA_DIR, filename)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        # Parse & Re-index
        global chunks_global, doc_catalog_global, index_info_global
        new_chunks = ingestion_engine.parse_markdown_document(content, doc_id=doc_id, filename=filename)

        chunks_global, doc_catalog_global = ingestion_engine.load_directory(DATA_DIR)
        index_info_global = hybrid_retriever.index_corpus(chunks_global)

        return {
            "status": "success",
            "message": f"Successfully ingested '{filename}' and created {len(new_chunks)} chunks.",
            "total_documents": len(doc_catalog_global),
            "total_chunks": len(chunks_global)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/ask")
async def api_qa_ask(req: QARequest):
    try:
        t_start = time.perf_counter()

        # 1. Query Transformation (HyDE)
        hyde_passage = query_transform_engine.generate_hyde(req.query) if req.use_hyde else None

        # 2. Hybrid Retrieval
        hybrid_out = hybrid_retriever.search_hybrid(
            req.query, top_k=req.top_k * 3, rrf_k=60, hyde_text=hyde_passage
        )
        candidates = hybrid_out["fused_results"]

        # 3. Cross-Encoder Re-Ranking
        if req.use_reranker:
            rerank_out = reranker_engine.rerank(req.query, candidates, top_k=req.top_k)
            final_chunks = rerank_out["reranked"]
            rerank_latency = rerank_out["latency_ms"]
        else:
            final_chunks = candidates[:req.top_k]
            rerank_latency = 0.0

        # 4. Context Assembly & Grounded Generation
        context_str, citations_meta = generator_engine.assemble_context(final_chunks)
        gen_out = generator_engine.generate_grounded_answer(req.query, context_str, citations_meta)

        # 5. Automated Evaluation
        eval_metrics = evaluation_engine.evaluate_response(
            req.query, gen_out["grounded_answer"], final_chunks, gen_out["unique_citations_used"]
        )

        total_latency = (time.perf_counter() - t_start) * 1000

        return {
            "query": req.query,
            "answer": gen_out["grounded_answer"],
            "hallucinated_answer": gen_out["hallucinated_answer"],
            "citations": citations_meta,
            "unique_citations_used": gen_out["unique_citations_used"],
            "evaluation": eval_metrics,
            "latency": {
                "total_ms": round(total_latency, 2),
                "retrieval_ms": hybrid_out["latency_ms"],
                "rerank_ms": rerank_latency,
                "generation_ms": gen_out["latency_ms"]
            },
            "retrieved_chunks": [
                {
                    "chunk_id": c.get("chunk_id", ""),
                    "doc_title": c.get("doc_title", ""),
                    "breadcrumbs": c.get("breadcrumbs", ""),
                    "text": c.get("text", ""),
                    "cross_score": c.get("cross_score", 0.0),
                    "rrf_score": c.get("rrf_score", 0.0)
                }
                for c in final_chunks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipeline/trace")
async def api_pipeline_trace(req: TraceRequest):
    try:
        # Step 1: Input
        step1 = {"step": 1, "name": "User Query Input", "data": {"raw_query": req.query}}

        # Step 2: Transformations
        expansions = query_transform_engine.multi_query_expansion(req.query)
        hyde_doc = query_transform_engine.generate_hyde(req.query) if req.use_hyde else None
        sub_queries = query_transform_engine.decompose_sub_queries(req.query)

        step2 = {
            "step": 2,
            "name": "Query Transformation & Expansion",
            "data": {
                "multi_queries": expansions,
                "hyde_synthesized_passage": hyde_doc,
                "sub_queries": sub_queries
            }
        }

        # Step 3: Hybrid Retrieval
        hybrid_out = hybrid_retriever.search_hybrid(
            req.query, top_k=6, rrf_k=60, hyde_text=hyde_doc
        )
        step3 = {
            "step": 3,
            "name": "Hybrid Retrieval (Dense HNSW + Sparse BM25 + RRF)",
            "data": {
                "dense_top3": hybrid_out["raw_dense_top3"],
                "sparse_top3": hybrid_out["raw_sparse_top3"],
                "fused_rrf_candidates": hybrid_out["fused_results"][:6],
                "retrieval_latency_ms": hybrid_out["latency_ms"]
            }
        }

        # Step 4: Re-Ranking
        rerank_out = reranker_engine.rerank(req.query, hybrid_out["fused_results"], top_k=3)
        step4 = {
            "step": 4,
            "name": "Cross-Encoder Re-Ranking (MS-MARCO MiniLM)",
            "data": {
                "reranked_chunks": rerank_out["reranked"],
                "rerank_latency_ms": rerank_out["latency_ms"]
            }
        }

        # Step 5: Grounded Generation
        context_str, citations_meta = generator_engine.assemble_context(rerank_out["reranked"])
        gen_out = generator_engine.generate_grounded_answer(req.query, context_str, citations_meta)
        eval_metrics = evaluation_engine.evaluate_response(
            req.query, gen_out["grounded_answer"], rerank_out["reranked"], gen_out["unique_citations_used"]
        )

        step5 = {
            "step": 5,
            "name": "Grounded Context Assembly & Attributed Synthesis",
            "data": {
                "grounded_answer": gen_out["grounded_answer"],
                "hallucinated_answer": gen_out["hallucinated_answer"],
                "citations": citations_meta,
                "evaluation_triad": eval_metrics
            }
        }

        return {
            "query": req.query,
            "pipeline_trace": [step1, step2, step3, step4, step5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transform/preview")
async def api_transform_preview(req: TransformRequest):
    return {
        "original_query": req.query,
        "multi_queries": query_transform_engine.multi_query_expansion(req.query),
        "hyde_passage": query_transform_engine.generate_hyde(req.query),
        "sub_queries": query_transform_engine.decompose_sub_queries(req.query)
    }

@app.get("/api/evaluation/benchmark")
async def api_evaluation_benchmark():
    return evaluation_engine.benchmark_naive_vs_advanced()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8195, reload=True)
