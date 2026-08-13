#!/usr/bin/env bash
# Serve Qwen3-Embedding-4B on :8001, pinned to GPU1.
#
# NOT needed for T1/T2/T5/T7 — those embed in-process via hnav/core/embedding.py,
# so the Stage-0 gate is reachable without any serving infrastructure.
#
# REQUIRED for M0 (hnav/stage0/m0_live_fidelity.py) and T4, where the benchmark's
# own code path runs. NEXT_STEPS.md §6 "Correction 2" claims otherwise — it says
# TextRetriever loads Qwen3-Embedding-4B in-process. That is wrong. The class
# Qwen3Embedding4BEmbeddings exists at methods/embedding_retriever.py:51 but
# TextRetriever.__init__ never selects it; line 176 routes
# "Qwen/Qwen3-Embedding-4B" to LangChain OpenAIEmbeddings against
# OPENAI_BASE_URL. See hnav/deploy/mab.env.template.
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
