# hnav_geo — the fully parser-free geometric identity screen (E2E-3)

The question this arm answers: can the H-Nav read-time detector beat the
committed parser pipeline (hnav_raw, sh_64k **64/100**) end-to-end with an
identity screen that reads **embeddings only** — no parser field consulted at
inference anywhere in the detection path?

The screen (`hnav/geometry_filter/geo_artifact.py`):

    score(a,b) = min( (cos_w − T_w)/s_w , (probe − T_p)/s_p )

- `probe` — the slot probe: logistic regression on `|d_hat|`, the absolute
  axis profile of the unit difference vector. It answers "did the OBJECT
  slot change (candidate supersession) or the SUBJECT slot (the cross-key
  adversary the NLI rubber-stamps)?" — fit on the gold conflict dataset's
  calibration split (989 gold vs 8,716 hard-negative edits).
- `cos_w` — cosine under the frozen committed ABTT D=128 whitening (copied
  into the artifact; source fingerprint pinned).
- anchors/scales from calibration pool pairs; `pair_filter(tau)` accepts a
  float (diagonal family) or a `'tw:tp'` rectangle (per-axis offsets — the
  Amendment-1 grid; the diagonal couples the axes and misses the best
  zero-harm corner, a loose whitened-cos with a strict probe).

**Frozen operating point** (clean-cache selection 2026-08-29, sha pinned in
`pipeline.json`): `cos_pair 0.94, geo tau '-0.4:0.2', NLI 0.90, r_min 0.44`
— pair precision **1.000**, pool recall **0.7895**, **0 harmful**,
conflicted-question recall 104/139. Best committed parser-free point before
this arm: 0.4444 (abtt_noparser); CES with parser-relation: 0.7343.

Pair-level evidence (`stage0_results/geometry_filter/geo_pairlevel.json`):
balanced sh_64k AUROC 0.9716 (CES 0.9756, ABTT-cos 0.9648, raw cos 0.8930),
band 0.9657; confirmatory hard task 0.9984 / AUPRC 0.9784 (ABTT-cos level,
far above CES 0.8466); best unseen-transition tail in the repo
(TPR@FPR1e-4 = 0.481 vs ABTT-cos 0.404, CES 0.208) with seen-tail 0.720.

Preregistration: `stage0_results/geometry_filter/GEO_PREREG.md` (grids,
selection rule, wet-run gate GG1: pool recall must exceed the best committed
parser-free point 0.4444, endpoint GG2: sh_64k overall > 64/100 paired vs the
committed parser-arm records). Selection ran on sh_6k + sh_32k only;
sh_64k untouched until the single wet shot.

## Run against a new answering model

```bash
python pipelines/hnav_geo/run.py --llm-model <served-name> --dry-run   # always first
python pipelines/hnav_geo/run.py --llm-model <served-name> --llm-base-url http://localhost:8003/v1
```

Same frozen substrate as every arm: Qwen3-Embedding-4B fp32 L8192 prepasses
(base benchmarkpage, cos_loose 0.90 — the parser arm's own prepasses, reused),
`cross-encoder/nli-deberta-v3-large` bidirectional NLI replay, subsets
sh_6k + sh_32k + sh_64k, one shot per model, voids reported not re-rolled.
