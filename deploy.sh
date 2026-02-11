#!/bin/bash
set -e

HOMELAB_HOST="${HOMELAB_HOST:-homelab}"
REPO_PATH="${REPO_PATH:-/home/gaze/projects/github-GabrielDCelery/shadowrun-lore-rag}"

echo "=== Deploying Shadowrun RAG to $HOMELAB_HOST ==="

echo "Pulling latest code..."
ssh "$HOMELAB_HOST" "cd $REPO_PATH && git pull"

echo "Building container..."
ssh "$HOMELAB_HOST" "cd $REPO_PATH && docker compose build"

echo "Restarting container..."
ssh "$HOMELAB_HOST" "cd $REPO_PATH && docker compose down && docker compose up -d"

echo "=== Deployment complete ==="
echo ""
echo "To run ingestion:"
echo "  ssh $HOMELAB_HOST docker exec -it shadowrun-rag uv run python src/ingest.py"
echo ""
echo "To query:"
echo "  ssh $HOMELAB_HOST docker exec -it shadowrun-rag uv run python src/query.py \"your question\""
