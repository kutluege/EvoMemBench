#!/usr/bin/env bash
# E2E-3: the hnav_geo wet run (all three subsets) against the frozen
# Qwen3-4B-Instruct-2507 chat server on :8003. Launch under nohup from the
# repo root on the box:
#
#   nohup bash hnav/deploy/run_geo_arm.sh > hnav/_out/geo_arm_launch.log 2>&1 &
#
# Progress: hnav/_out/geo_arm_progress ; sentinel: hnav/_out/geo_arm.done
set -u
cd "$(dirname "$0")/../.."
source hnav/deploy/_activate.sh
PROG=hnav/_out/geo_arm_progress
echo "start $(date -u +%FT%TZ)" >> "$PROG"

curl -sf http://localhost:8003/v1/models > /dev/null || {
  echo "FAILED no-chat-server $(date -u +%FT%TZ)" >> "$PROG"; exit 3; }

python pipelines/hnav_geo/run.py --llm-model Qwen/Qwen3-4B-Instruct-2507 --dry-run \
  && echo "ok dry-run $(date -u +%FT%TZ)" >> "$PROG" \
  || { echo "FAILED dry-run $(date -u +%FT%TZ)" >> "$PROG"; exit 4; }

python pipelines/hnav_geo/run.py --llm-model Qwen/Qwen3-4B-Instruct-2507 \
  --llm-base-url http://localhost:8003/v1 \
  && echo "ok wet $(date -u +%FT%TZ)" >> "$PROG" \
  || { echo "FAILED wet $(date -u +%FT%TZ)" >> "$PROG"; exit 5; }

touch hnav/_out/geo_arm.done
echo "done $(date -u +%FT%TZ)" >> "$PROG"
