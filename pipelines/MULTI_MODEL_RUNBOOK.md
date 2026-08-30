# Multi-model campaign runbook

Everything needed to run the frozen H-Nav arms against a **new answering
model**. Only the answering LLM varies; the embedder, thresholds, artifacts
and prepasses are frozen and LLM-independent.

## The three arms to run per model

| arm | identity screen | semantic gate | why it is in the campaign |
| --- | --- | --- | --- |
| **`hnav_raw`** | parser same-key | NLI ≥ 0.90 | the shipped reference; the +19 result to replicate |
| **`hnav_idonly`** | parser same-key | **waived** | tests whether the semantic gate was the binding constraint; zero harm by construction |
| **`hnav_geo`** | geometry only | NLI ≥ 0.90 | the parser-free contrast — **report its void condition 4**, see below |

`hnav_abtt` is answer-identical to `hnav_raw` on the committed model (0
disagreements) and can be skipped unless a per-model geometry check is
wanted. `hnav_ces` and `hnav_fusion` are closed (superseded / failed gate).

> **Void-condition warning.** `hnav_geo` and `hnav_abtt_noparser` produced
> harmful suppressions on sh_64k (8 and 5) and their runs are **void by
> preregistered condition 4**. This is structural: only a `same_key`-based
> screen has zero harm by construction. Expect the same on other models, and
> report it rather than quoting the accuracy alone. `pipelines/_shared/runner.py`
> now fails a subset on any run-voiding condition, so new runs surface it.

## Preconditions (verified 2026-08-30)

- All 7 arms' operating points match their pinned sha256 (`git`-normalized
  blobs — the form the Linux box checks out). `pytest hnav/tests/test_pipelines.py`
  asserts this.
- Prepasses required, **per subset**, already built on the box and reusable
  for every model:
  - `hnav_raw`, `hnav_idonly`, `hnav_geo` → `stage1_prepass_<subset>_benchmarkpage.json`
  - `hnav_abtt`, `hnav_abtt_noparser` → `…_benchmarkpage_abtt.json`
  - `hnav_ces`, `hnav_fusion` → `…_benchmarkpage_ces.json`
- Subsets are fixed at `sh_6k, sh_32k, sh_64k` (`ALLOWED_SUBSETS`; sh_262k
  permanently excluded).

## Per-model sequence

```bash
# ── on the box, repo root ───────────────────────────────────────────────
git pull
source hnav/deploy/_activate.sh

# 1. serve the answering model on GPU1 (frozen flags for Qwen3-4B; adapt
#    ONLY the model path/name and, if the model needs it, --max-model-len)
nohup bash hnav/deploy/serve_stage1_chat.sh > hnav/_out/pipeline/chat.log 2>&1 &
until curl -sf http://localhost:8003/v1/models >/dev/null; do sleep 10; done

# 2. pre-flight per arm — sends nothing, prints the budget and guards
python pipelines/hnav_raw/run.py     --llm-model <served-name> --dry-run
python pipelines/hnav_idonly/run.py  --llm-model <served-name> --dry-run
python pipelines/hnav_geo/run.py     --llm-model <served-name> --dry-run

# 3. one shot per arm (each writes results/<model-tag>_<date>/)
python pipelines/hnav_raw/run.py    --llm-model <served-name> --llm-base-url http://localhost:8003/v1
python pipelines/hnav_idonly/run.py --llm-model <served-name> --llm-base-url http://localhost:8003/v1
python pipelines/hnav_geo/run.py    --llm-model <served-name> --llm-base-url http://localhost:8003/v1
```

Long runs go under `nohup` via a committed driver script — never an inline
compound ssh command (`hnav/deploy/run_geo_arm.sh`, `run_idonly_arm.sh` are
the templates; copy one per arm).

## Cost per model

Each arm runs 5 internal arms (native, native_repeat, detector_suppress,
detector_demote_late, detector_anti) × 100 questions × 3 subsets =
**1,500 chat completions per pipeline arm**, so ~4,500 for the three-arm
set. Prompt sizes are the benchmark's own RAG prompts (~53k tokens on
sh_64k); the detector arm's prompt is *shorter* than native
(−0.31 % sh_64k, −2.87 % sh_6k). **No prepass rebuild, no embedding
recompute, no extra generative call.**

## After the runs

```bash
# fetch into the repo and analyse (locally)
scp -r egekutlu@<box>:.../pipelines/<arm>/results/<tag> pipelines/<arm>/results/
python -m hnav.geometry_filter.e2e3_analysis pipelines/hnav_geo/results/<tag>
```

Then, for the campaign-level claims, check both:

1. **Replication** — does the governance gain hold per model (native vs arm,
   McNemar exact, per stratum)?
2. **Structural vs interaction** — suppression plans are LLM-independent, so
   the parser-only question set should be *identical* across models if the
   parser's edge is structural. The committed sh_64k reference set is
   **{9, 11, 26, 35, 54, 69, 70, 91, 93}**. Same set ⇒ structural; scattered
   ⇒ model interaction. Either result is publishable.

## Discipline (unchanged)

One shot per model per subset; a void is reported, not re-rolled; the runner
refuses to overwrite an existing `results/<tag>/`. Never tune on sh_64k.
A new embedder invalidates every threshold — that is a new calibration
campaign, not a runner flag.
