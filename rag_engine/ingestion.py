"""
Ingestion Engine: Structural Parsing, Markdown AST Chunking & Metadata Enrichment
Building Advanced RAG Pipelines & Intelligent Q&A Bot
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    category: str
    breadcrumbs: str
    text: str
    char_length: int
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionEngine:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_markdown_document(self, content: str, doc_id: str, filename: str) -> List[DocumentChunk]:
        """
        Parses Markdown hierarchy (#, ##, ###) into contextual chunks enriched with header breadcrumbs.
        """
        lines = content.splitlines()
        chunks = []
        breadcrumbs = []
        current_lines = []

        # Extract title from first H1 if present
        doc_title = filename.replace(".md", "").replace("_", " ").title()
        category = "General"
        if "cloud" in filename:
            category = "Cloud Infrastructure"
        elif "fintech" in filename or "pci" in filename:
            category = "Fintech & Security"
        elif "clinical" in filename or "triage" in filename:
            category = "Healthcare & Medicine"
        elif "transformer" in filename or "rag" in filename:
            category = "Machine Learning AI"

        for line in lines:
            if line.startswith("#"):
                header_text = line.lstrip("#").strip()
                if not doc_title or doc_title == filename:
                    doc_title = header_text

                if current_lines:
                    chunk_body = "\n".join(current_lines).strip()
                    if chunk_body:
                        bcrumb_str = " > ".join(breadcrumbs) if breadcrumbs else doc_title
                        annotated_text = f"[{bcrumb_str}]\n{chunk_body}"
                        chunks.append(DocumentChunk(
                            chunk_id=f"{doc_id}_chunk_{len(chunks)}",
                            doc_id=doc_id,
                            doc_title=doc_title,
                            category=category,
                            breadcrumbs=bcrumb_str,
                            text=annotated_text,
                            char_length=len(annotated_text),
                            token_count=len(annotated_text.split()),
                            metadata={"filename": filename, "header": breadcrumbs[-1] if breadcrumbs else "Root"}
                        ))
                    current_lines = []

                level = len(line) - len(line.lstrip("#"))
                while len(breadcrumbs) >= level:
                    breadcrumbs.pop()
                breadcrumbs.append(header_text)
            else:
                current_lines.append(line)

        if current_lines:
            chunk_body = "\n".join(current_lines).strip()
            if chunk_body:
                bcrumb_str = " > ".join(breadcrumbs) if breadcrumbs else doc_title
                annotated_text = f"[{bcrumb_str}]\n{chunk_body}"
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_id}_chunk_{len(chunks)}",
                    doc_id=doc_id,
                    doc_title=doc_title,
                    category=category,
                    breadcrumbs=bcrumb_str,
                    text=annotated_text,
                    char_length=len(annotated_text),
                    token_count=len(annotated_text.split()),
                    metadata={"filename": filename, "header": breadcrumbs[-1] if breadcrumbs else "Root"}
                ))

        return chunks

    def load_directory(self, data_dir: str) -> Tuple[List[DocumentChunk], List[Dict[str, Any]]]:
        all_chunks = []
        doc_catalog = []

        if not os.path.exists(data_dir):
            return all_chunks, doc_catalog

        for fname in sorted(os.listdir(data_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(data_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()

                doc_id = fname.replace(".md", "")
                chunks = self.parse_markdown_document(content, doc_id=doc_id, filename=fname)
                all_chunks.extend(chunks)

                doc_catalog.append({
                    "doc_id": doc_id,
                    "filename": fname,
                    "title": chunks[0].doc_title if chunks else doc_id,
                    "category": chunks[0].category if chunks else "General",
                    "total_chunks": len(chunks),
                    "total_chars": len(content),
                    "total_words": len(content.split())
                })

        return all_chunks, doc_catalog
