#!/usr/bin/env bash
# Is the KV-cache dtype destroying this model's answers?            [E2E-5]
#
# gemma-3-4b-it scored 6-13/100 under the campaign's inherited
# `--kv-cache-dtype fp8`, including 4/26 on the UNIQUE stratum - single-fact
# retrieval, no conflict, nothing for H-Nav to do - where Phi-4-mini scores
# 26/26. Its outputs looped: "United States of United States of United States
# of United". That is a broken-numerics signature, but a signature is not
# evidence, so this measures it instead of assuming it.
#
# Serves the SAME weights with the SAME flags twice, varying only the KV dtype,
# and runs the identical ten-question accuracy probe against each.
#
#   bash hnav/deploy/diagnose_kv_dtype.sh hnav/deploy/models.d/02_gemma3_4b.env
#
# ~20 chat completions per dtype. Writes hnav/_out/campaign/<key>/kv_probe_*.json
# and prints the comparison. Changes nothing; decide from the numbers.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

CONF="${1:?usage: diagnose_kv_dtype.sh <models.d/*.env>}"
DTYPES="${2:-fp8 auto}"
# shellcheck disable=SC1090
source "$CONF"
: "${MODEL_KEY:?}" "${MODEL_PATH:?}" "${SERVED_NAME:?}"

OUTDIR="hnav/_out/campaign/${MODEL_KEY}"
PORT="${HNAV_STAGE1_CHAT_PORT:-8003}"
mkdir -p "$OUTDIR"
source hnav/deploy/_activate.sh || exit 2

if curl -sf --max-time 5 "http://localhost:${PORT}/v1/models" >/dev/null 2>&1; then
    echo "REFUSED: something is already serving :$PORT. Stop it first."
    exit 3
fi

for DT in $DTYPES; do
    echo
    echo "================ KV dtype: $DT ================"
    SRV_PID=""
    KV_CACHE_DTYPE="$DT" setsid bash hnav/deploy/serve_campaign_model.sh "$CONF" \
        > "$OUTDIR/kv_${DT}_server.log" 2>&1 < /dev/null &
    SRV_PID=$!
    ok=0
    for i in $(seq 1 120); do
        kill -0 "$SRV_PID" 2>/dev/null || break
        curl -sf --max-time 5 "http://localhost:${PORT}/v1/models" >/dev/null 2>&1 \
            && { ok=1; break; }
        sleep 10
    done
    if [ "$ok" != 1 ]; then
        echo "  server failed to start for dtype=$DT (this is itself a result)"
        tail -20 "$OUTDIR/kv_${DT}_server.log" | sed 's/^/    /'
    else
        echo "  ready; probing"
        HNAV_PREFLIGHT_ALLOW_LOW_ACCURACY=1 \
        python hnav/deploy/preflight_model.py --probe-only \
            --model-key "$MODEL_KEY" --model-path "$MODEL_PATH" \
            --served-name "$SERVED_NAME" \
            --out "$OUTDIR/kv_probe_${DT}.json" 2>&1 | sed 's/^/    /'
    fi
    kill -TERM -"$SRV_PID" 2>/dev/null || kill -TERM "$SRV_PID" 2>/dev/null
    for _ in $(seq 1 60); do
        kill -0 "$SRV_PID" 2>/dev/null || break
        sleep 2
    done
    kill -KILL -"$SRV_PID" 2>/dev/null
    for _ in $(seq 1 60); do
        n=$(nvidia-smi --id=1 --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c . || echo 0)
        [ "$n" = "0" ] && break
        sleep 5
    done
done

echo
echo "================ comparison ================"
python - "$OUTDIR" $DTYPES <<'PY'
import json, pathlib, sys
out = pathlib.Path(sys.argv[1])
for dt in sys.argv[2:]:
    p = out / f"kv_probe_{dt}.json"
    if not p.exists():
        print(f"  {dt:5s} no probe (server did not start)")
        continue
    r = json.loads(p.read_text(encoding="utf-8"))
    c = r["checks"]
    san = c.get("answer_sanity", {})
    print(f"  {dt:5s} unique-stratum {san.get('correct')}/{san.get('n')}"
          f"   degenerate={not c.get('no_degenerate', {}).get('ok')}"
          f"   repeats={c.get('no_degenerate', {}).get('repeats')}")
    for s in r.get("sanity_probe", [])[:4]:
        print(f"          q{s['index']:<3} {'OK ' if s['ok'] else '   '} "
              f"{s['out']!r} vs {s['truth']!r}")
PY
