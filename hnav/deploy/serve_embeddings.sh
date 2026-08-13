#!/usr/bin/env bash
# Serve Qwen3-Embedding-4B on :8001, pinned to GPU1.
#
# NOT needed for T1 — M1 loads the embedder in-process, so the Stage-0 gate is
# reachable without any serving infrastructure. You need this from T4 onward,
# when the actual benchmark code path runs and expects an OpenAI-compatible
# /v1/embeddings endpoint.
#
#   tmux new -s embed
#   bash hnav/deploy/serve_embeddings.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

VENV="${HNAV_VENV:-$REPO_ROOT/.venv-hnav}"
[ -d "$VENV" ] && source "$VENV/bin/activate"

MODEL="${HNAV_EMBED_MODEL:-Qwen/Qwen3-Embedding-4B}"
PORT="${HNAV_EMBED_PORT:-8001}"
DEV="${HNAV_EMBED_DEVICE:-1}"

if ! python -c "import vllm" 2>/dev/null; then
    echo "vllm not installed. Install it into this venv:"
    echo "    python -m pip install vllm"
    echo
    echo "Note: GPU0 already runs your Qwen3-4B-Instruct LLM server. This script"
    echo "pins the embedder to GPU${DEV} via CUDA_VISIBLE_DEVICES so the two never"
    echo "contend. Do not remove that pin."
    exit 1
fi

echo "Serving $MODEL on :$PORT (GPU$DEV) ..."
# --task embed is the flag on vLLM >=0.6; older builds use --task embedding and
# newer ones --runner pooling. If this errors, check `vllm serve --help`.
CUDA_VISIBLE_DEVICES="$DEV" exec vllm serve "$MODEL" \
    --task embed \
    --port "$PORT" \
    --gpu-memory-utilization 0.85 \
    --served-model-name "$MODEL"
