#!/usr/bin/env bash
# ==============================================================================
# Advanced RAG Pipelines & Intelligent Q&A Bot — Launch Script
# Port: 8195
# Ingest, Embed, Retrieve, Re-Rank, HyDE, Grounded QA & Evaluation
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"

PORT=8195

echo "=================================================================="
echo "  🚀 Starting Advanced RAG Pipelines & Q&A Bot Studio (Port: ${PORT})"
echo "  Building RAG Pipelines, HyDE, Re-Ranking & Evaluation"
echo "  Python Environment: ${PYTHON_BIN}"
echo "=================================================================="

# Check if port 8195 is already occupied and terminate stale instance if needed
PID=$(lsof -ti :${PORT} || true)
if [ -n "$PID" ]; then
    echo "⚠️ Port ${PORT} occupied by PID ${PID}. Freeing port..."
    kill -9 "$PID" || true
    sleep 1
fi

exec "$PYTHON_BIN" -m uvicorn app:app --host 0.0.0.0 --port ${PORT} --reload
