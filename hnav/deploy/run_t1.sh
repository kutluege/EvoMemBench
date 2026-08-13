#!/usr/bin/env bash
# Run M1 (the Stage-0 gate) under nohup so it survives the SSH session dropping.
#
#   bash hnav/deploy/run_t1.sh              # all single-hop subsets
#   bash hnav/deploy/run_t1.sh --subsets sh_6k --max-pairs 50   # 2-minute smoke
#
# Watch:  tail -f hnav/_out/m1.log
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

VENV="${HNAV_VENV:-$REPO_ROOT/.venv-hnav}"
[ -d "$VENV" ] && source "$VENV/bin/activate"

mkdir -p hnav/_out
LOG="hnav/_out/m1.log"

echo "Pre-flight ..."
python hnav/deploy/check_env.py || { echo "check_env failed — fix before running M1."; exit 1; }

echo
echo "Launching M1 (nohup). Log: $LOG"
nohup python hnav/stage0/m1_geometry_calibration.py "$@" > "$LOG" 2>&1 &
PID=$!
echo "  pid=$PID"
echo
echo "  tail -f $LOG"
echo "  results land in hnav/_out/m1_geometry_calibration.json"
echo
echo "Exit codes: 0 = gate PASSED, 2 = GATE S3 FIRED (stop, report to a human)."
