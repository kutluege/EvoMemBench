#!/usr/bin/env bash
# H-Nav setup for ozonderlab2 — wraps setup_remote.sh with this box's specifics.
#
#   bash hnav/deploy/setup_ozonderlab2.sh
#
# Differences from the generic setup_remote.sh:
#   - HF_HOME is pinned to the nvme (/mnt/nvmes/nvme1/egekutlu/hf_cache), not
#     $HOME/.cache. The embedder weights are ~8 GB and home dirs are often small.
#   - Python 3.11 is discovered rather than assumed; the conda python3.11 that
#     ships inside the vllm_0.9.1 env is deliberately NOT reused (installing
#     torch into it could disturb the running server on GPU0).
#   - Both .env files are written from templates if absent.
# Idempotent: safe to re-run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# ── nvme-backed caches ───────────────────────────────────────────────────────
NVME="${HNAV_NVME:-/mnt/nvmes/nvme1/egekutlu}"
export HF_HOME="${HF_HOME:-$NVME/hf_cache}"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
mkdir -p "$HF_HOME"

echo "=============================================================="
echo " H-Nav setup — ozonderlab2"
echo "   repo    : $REPO_ROOT"
echo "   HF_HOME : $HF_HOME"
echo "=============================================================="

# ── pick a Python 3.11/3.12 that is NOT the vllm env's ───────────────────────
PY=""
for cand in python3.11 python3.12 python3.10; do
    if command -v "$cand" >/dev/null 2>&1; then
        case "$(command -v "$cand")" in
            *vllm*|*conda*/vllm*) continue ;;   # never touch the server's env
        esac
        PY="$cand"; break
    fi
done
if [ -z "$PY" ]; then
    echo "!! No standalone python3.10-3.12 found."
    echo "   Do NOT install into the vllm_0.9.1 conda env — that is what serves GPU0."
    echo "   Create a clean one:   conda create -y -n hnav python=3.11"
    echo "   then:                 conda activate hnav && HNAV_PYTHON=python bash $0"
    exit 1
fi
[ -n "${HNAV_PYTHON:-}" ] && PY="$HNAV_PYTHON"
echo "[1/3] Python: $PY -> $($PY -V 2>&1)"

# ── hand off to the generic installer, with HF_HOME exported ─────────────────
echo "[2/3] running setup_remote.sh ..."
HNAV_PYTHON="$PY" bash hnav/deploy/setup_remote.sh

# ── .env files ───────────────────────────────────────────────────────────────
echo "[3/3] .env files ..."
if [ ! -f "$REPO_ROOT/.env" ]; then
    cp hnav/deploy/ozonderlab2.env "$REPO_ROOT/.env"
    echo "   wrote .env (repo root) — CHECK HNAV_LLM_MODEL matches what :8000 serves"
else
    echo "   .env exists, left alone"
fi

MAB="$REPO_ROOT/In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench"
if [ ! -f "$MAB/.env" ]; then
    cp hnav/deploy/mab.env.template "$MAB/.env"
    echo "   wrote MemoryAgentBench/.env (embeddings -> :8001)"
else
    echo "   MemoryAgentBench/.env exists, left alone"
fi

cat <<'EOF'

==============================================================
 Setup complete. Next:

   source .venv-hnav/bin/activate
   export HF_HOME=/mnt/nvmes/nvme1/egekutlu/hf_cache
   python hnav/deploy/check_env.py     # must exit 0
   pytest hnav/tests/ -q               # must be 151 passed

 Then T1 — the kill switch. See RUNBOOK.md §4.
==============================================================
EOF
