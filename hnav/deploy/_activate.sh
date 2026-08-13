#!/usr/bin/env bash
# Shared activation for every H-Nav script that runs on the lab GPU boxes.
#   source hnav/deploy/_activate.sh
#
# Lab policy: do NOT install your own conda. A system-wide install lives at
# /opt/anaconda3. `conda init` is deliberately not run at login (it slows bash
# down), so `conda` is not on PATH until you source the lab's helper —
# `source activate_conda`. Every script that needs python must do this itself;
# inheriting it from an interactive shell is not reliable under nohup/tmux.
#
# Override the env name with HNAV_CONDA_ENV. Set HNAV_NO_ACTIVATE=1 to skip
# entirely (useful if you have already activated something by hand).

HNAV_CONDA_ENV="${HNAV_CONDA_ENV:-hnav}"

if [ "${HNAV_NO_ACTIVATE:-0}" = "1" ]; then
    return 0 2>/dev/null || exit 0
fi

# ── make `conda` available ───────────────────────────────────────────────────
if ! command -v conda >/dev/null 2>&1; then
    _activated=0
    # The lab's helper. `source` searches PATH, so the bare name works if it is
    # on PATH; the explicit paths cover the case where it is not.
    for _c in activate_conda "$HOME/activate_conda" /opt/activate_conda; do
        # shellcheck disable=SC1090
        if source "$_c" >/dev/null 2>&1; then _activated=1; break; fi
    done
    if [ "$_activated" -eq 0 ]; then
        # Fall back to conda's own hook under the system-wide install.
        for _h in /opt/anaconda3/etc/profile.d/conda.sh \
                  /opt/miniconda3/etc/profile.d/conda.sh; do
            # shellcheck disable=SC1090
            if [ -f "$_h" ]; then source "$_h"; _activated=1; break; fi
        done
    fi
    if [ "$_activated" -eq 0 ] || ! command -v conda >/dev/null 2>&1; then
        echo "!! conda not available."
        echo "   Expected the system-wide install at /opt/anaconda3 and the lab helper:"
        echo "       source activate_conda"
        echo "   Do NOT install your own conda. Ask the admin if the helper has moved."
        return 1 2>/dev/null || exit 1
    fi
fi

# ── activate the H-Nav env ───────────────────────────────────────────────────
if ! conda activate "$HNAV_CONDA_ENV" 2>/dev/null; then
    echo "!! conda env '$HNAV_CONDA_ENV' not found."
    echo "   Create it once with:  bash hnav/deploy/setup_ozonderlab2.sh"
    return 1 2>/dev/null || exit 1
fi

# ── caches on the nvme, not the home dir (weights are ~8 GB) ─────────────────
NVME="${HNAV_NVME:-/mnt/nvmes/nvme1/egekutlu}"
export HF_HOME="${HF_HOME:-$NVME/hf_cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
