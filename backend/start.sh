#!/bin/bash

# Download model if not exists
if [ ! -f models/codellama-nl2sql.Q4_K_M.gguf ]; then
  echo "🔽 Downloading GGUF model..."
  mkdir -p models
  curl -L -o models/codellama-nl2sql.Q4_K_M.gguf "https://huggingface.co/HritvijaSsingh/codellama-nl2sql/resolve/main/codellama-nl2sql.Q4_K_M.gguf"
fi

# Run the app
uvicorn app:app --host 0.0.0.0 --port 8000
