# Next goal — a geometry+NLI conflict detector, benchmarked like H-Nav

*(User directive, 2026-08-26: if a truly promising method emerges from the
geometry-filter experiments — "like hnav but without hnav's cosine and
parser" — build a conflict detector by running NLI on top of it, benchmark it
exactly the way H-Nav was benchmarked, and compare the results.)*

## What the experiments say the candidate is

Two screens survived the evidence in `REPORT.md`; they answer the directive
differently and both should be carried into the benchmark:

1. **RCESP screen** — the genuinely *non-cosine* method: per-relation edit
   subspaces (k=20, fit on the 989 calibration gold edits), score
   `||U_r^T d|| / ||d||`. It beats the mandated cosine baseline on the
   balanced sh_64k set (0.930 vs 0.893) and orders 89.6% of the comparisons
   raw cosine gets exactly wrong. Caveats to design around: it currently
   takes relation identity from the parser (the parser-free fallbacks
   `rced_max` 0.837 / `rcesp_global` 0.768 are weaker), its transfer to
   unseen transitions is 0.768, and its frozen threshold trades recall
   (0.67) for precision (0.97).
2. **ABTT(D=128)-cosine screen** — still cosine-family, but parser-free and
   the strongest, most transferable pairwise signal measured (0.999 hard-task
   AUROC, 0.952 band AUROC, robust frozen operating point P0.85/R0.98). Its
   NLI pipeline **already exists and is benchmarked** (`pipelines/hnav_abtt`),
   which is precisely what makes the comparison meaningful.

## The pipeline to build: `pipelines/hnav_rcesp/`

Same shape as the two committed pipelines (`pipelines/_shared/runner.py`
conventions), so results are comparable row-for-row:

- **Stage 1 (replaces the cosine screen and the parser key-check):** RCESP
  pair score with a frozen calibration-fit operating point. Ship the fitted
  subspaces as a committed artifact
  (`stage0_results/geometry_filter/rcesp_subspaces_k20.json`, sha256
  fingerprint, same pattern as `abtt_whitening_D128.json` /
  `ABTTWhitening.to_dict`). Two arms:
  - `rcesp_global` — fully parser-free (the honest "no cosine, no parser" arm);
  - `rcesp` with relation identity — an upper-bound arm; if relation identity
    must come from the parser, say so in the arm name rather than hiding it.
- **Stage 2 (unchanged):** the existing bidirectional-NLI verification from
  `hnav/core/read_gate.py` — a pair is a verified conflict only if
  contradiction clears the threshold in both directions. Reuse the committed
  NLI model and thresholds; do not retune them, or the comparison stops being
  about the screen.
- **Operating point:** fit on sh_6k + sh_32k only (best-F1 or the
  coverage-balanced criterion the other pipelines used), freeze, commit as
  `rcesp_operating_point.json`. Never touched after the first confirmatory run.

## Benchmark protocol (identical to the committed runs)

- Subsets: `sh_6k + sh_32k + sh_64k`, never sh_262k (`ALLOWED_SUBSETS` in
  `pipelines/_shared/runner.py`; user decision 2026-08-24).
- One shot per answering model, same models as the existing series; embedder
  frozen (Qwen3-Embedding-4B float32 L8192, the campaign cache).
- Report stratified per subset, never pooled; same question-level scoring as
  the committed arms so the numbers line up with `pipelines/README.md`
  (hnav_raw 17/66 → hnav_abtt 37/66 on the recorded comparison).
- Compare four arms: `hnav_raw` (committed), `hnav_abtt` (committed),
  `hnav_rcesp_global` (new, parser-free), `hnav_rcesp` (new, relation-aware
  upper bound). Paired per-question comparison, McNemar or paired bootstrap.

## Honest expectations, written down before running

- ABTT-cosine dominated RCESP on every held-out slice at the pair level, so
  the likely outcome is `hnav_abtt ≥ hnav_rcesp`. The scientific value of the
  run is (a) whether a *non-cosine* geometric screen can carry an end-to-end
  benchmark at all, and (b) whether RCESP's high-precision/low-recall profile
  interacts differently with the NLI stage than cosine's (NLI wastes calls on
  screen false positives; a precision-first screen may spend the NLI budget
  better). A negative result is reportable per the decision rules.
- If a combined screen is tried (ABTT-cos OR RCESP above their thresholds),
  it is a fifth arm, preregistered as such — not a post-hoc rescue.

## Guard rails that still bind

- Read-path only. `hnav/core/write_policy.py` must not exist (T8 NO_GO is
  permanent). `read_policy.py`/`read_gate.py` stay barred from `H_raw`.
- The subspace artifact is calibration-fit; sh_64k stays confirmatory.
- No BFCL suites (`In-Episode-Execution/`, `Cross-Episode-Execution/`).
- New `.gz` files under `stage0_results/` need `!name.gz` gitignore lines.
