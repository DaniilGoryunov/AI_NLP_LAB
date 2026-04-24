#!/bin/bash
set -e

echo "=== Starting Ollama server ==="
ollama serve &
OLLAMA_PID=$!

echo "=== Waiting for Ollama to be ready ==="
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "  Ollama not ready yet, waiting..."
    sleep 2
done
echo "=== Ollama is ready ==="

echo "=== Pulling Qwen2.5:0.5b model (if not cached) ==="
ollama pull qwen2.5:0.5b
echo "=== Model ready ==="

echo "=== Starting FastAPI service on port 8000 ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
