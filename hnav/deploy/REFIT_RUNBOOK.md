# Threshold re-fit after the 512-token correction — RUNBOOK  [T12]

> **Status: QUEUED FOR BOX.** Written 2026-08-15 while `ozonderlab2` was
> unreachable. Nothing here has been executed. Every command runs from the
> repo root on the box with `source hnav/deploy/_activate.sh` (conda env
> `hnav`; ignore the empty `.venv-hnav/` skeleton).
>
> **Why:** `hnav/BUILD_NOTES.md` §10 — offline signals were computed from the
> first ~12% of each chunk. The frozen `nmargin`/`H_z`/`r_min` in
> `stage0_results/final/m3_headroom.json` inherit that defect and are not
> valid for the corrected embedder.
>
> **Scope guard: CALIBRATION SPLIT ONLY (`sh_6k` + `sh_32k`).** `sh_64k` and
> `sh_262k` are not touched. `m3_headroom.py` refuses to fit without a
> calibration subset; do not pass `--allow-no-calibration`.

## 0. Preconditions

```bash
cd /mnt/nvmes/nvme1/egekutlu/EvoMemBench
git pull --ff-only
source hnav/deploy/_activate.sh
pytest hnav/tests/ -q                 # expect 315 passed, 0 skipped (torch present)
nvidia-smi                            # GPU0 = the user's :8000, NEVER touched
```

The torch-dependent tokenizer test in `test_embedding_truncation.py` is
skipped locally and MUST run here — that is the one that proves `max_length`
reaches the tokenizer.

**Do not delete `hnav/_cache/emb/`.** The corrected run writes into a new
namespace (`...|L8192`); the old `|L512`-free entries stay as provenance.
Expect a full recompute: ~24k vectors, all misses, GPU-bound.

## 1. Confirm the model's real context limit (2 min, no GPU)

The 8192 default assumes Qwen3-Embedding-4B accepts ≥8192 positions. Verify
from the cached weights rather than from the model card:

```bash
python - <<'PY'
from transformers import AutoConfig, AutoTokenizer
m = "Qwen/Qwen3-Embedding-4B"
c = AutoConfig.from_pretrained(m)
t = AutoTokenizer.from_pretrained(m)
print("max_position_embeddings:", getattr(c, "max_position_embeddings", None))
print("tokenizer model_max_length:", t.model_max_length)
PY
```

- If `max_position_embeddings` < 8192 → **STOP and report.** Do not silently
  lower `HNAV_EMBED_MAX_LENGTH`; the chunk size is what it is, and a cap below
  it means the truncation defect is structural and must be declared, not hidden.
- Also record the **Qwen** token count of the largest real chunk (the 4,333
  figure is tiktoken):

```bash
python - <<'PY'
import json, sys; sys.path.insert(0, ".")
from transformers import AutoTokenizer
from hnav.stage0.m2_retrieval_calibration import build_chunks, subset_name
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-4B")
data = json.load(open("In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/data/Conflict_Resolution.json", encoding="utf-8"))
for item in data:
    n = subset_name(item)
    if n not in ("sh_6k", "sh_32k"):
        continue
    chunks, fb = build_chunks(item["context"], 4096)
    lens = [len(tok(c)["input_ids"]) for c in chunks]
    print(f"{n}: n_chunks={len(chunks)} fallback={fb} qwen_tokens max={max(lens)} min={min(lens)}")
PY
```

Record both numbers in the diff report. If any chunk exceeds 8192 Qwen tokens,
raise `HNAV_EMBED_MAX_LENGTH` to the next power of two that still fits the
endpoint's 16384 window and re-run from here.

## 2. Re-run the signal phases — calibration split only

`fallback_chunker: false` must hold in every output; `true` means punkt is
missing and the chunks are not the benchmark's.

```bash
# T1/M1 — geometry calibration. Repays the embedding cache in the new
# namespace. This is the long one (~24k vectors, GPU1).
python hnav/stage0/m1_geometry_calibration.py --subsets sh_6k sh_32k \
  2>&1 | tee hnav/_out/pipeline/refit_m1.log
# banner must read: max_length=8192

# T2/M1b — grouping ablation (reuses the cache written above)
python hnav/stage0/m1b_grouping_ablation.py --subsets sh_6k sh_32k \
  2>&1 | tee hnav/_out/pipeline/refit_m1b.log

# T5/M2 — retrieval calibration
python hnav/stage0/m2_retrieval_calibration.py --subsets sh_6k sh_32k \
  2>&1 | tee hnav/_out/pipeline/refit_m2.log

# T6/M3 — the threshold fit itself. --no-llm: this re-fit needs the
# geometry, not the counterfactual grading, and the LLM arm costs hours.
python hnav/stage0/m3_headroom.py --subsets sh_6k sh_32k --no-llm \
  2>&1 | tee hnav/_out/pipeline/refit_m3.log
```

Sanity checks before reading any number:
- `m1` banner shows `max_length=8192`;
- the embedding cache grew by ~24k `.npy` files (new namespace) and the old
  files are still present;
- `"fallback_chunker": false` in the m2/m3 outputs;
- m3's `thresholds.fit_subsets == ["sh_6k", "sh_32k"]` and
  `unfit_for_analysis == false`.

## 3. Produce the old-vs-new diff report

Write `stage0_results/refit_threshold_diff.md` containing, **per subset — never
pooled**:

| quantity | old (L512) | new (L8192) | Δ |
|---|---|---|---|
| `nmargin` p25 | | | |
| `H_z` p75 | | | |
| `r_min` p10 | | | |
| median chunk-pair cosine | | | |
| M1b best-F1 tau + precision/recall | | | |
| M2 `nmargin`/`H_z` p50 | | | |

Old values: `stage0_results/final/{m1b_grouping_ablation,m2_retrieval_calibration,m3_headroom}.json`.
New values: the corresponding `hnav/_out/*.json` after step 2.

### Two defects that MUST be stated in that report

**(a) `H_Z_CAL = 1.9569` is arithmetically unreachable at sh_6k.** sh_6k has
`n_chunks = 2`, so a ranking over 2 items has a fixed z-scored entropy:
z-scoring two scores always gives `{+1, −1}` regardless of their values, hence
`H_z ≡ 0.365333…` exactly. M2's sh_6k row confirms it — `min = max = p50 =
0.3653338550872077`. The frozen threshold `H_z > 1.9569` therefore **can never
fire on sh_6k**: half the calibration split contributes nothing but a constant
to that screen, and the gate's ambiguity precondition on sh_6k is decided
entirely by `nmargin`.

**(b) The threshold was fit on POOLED calibration rows.** `m3_headroom.py`'s
`fit_thresholds` concatenates the read rows of both subsets and takes a single
percentile (`np.percentile(hz, 75)` over sh_6k ∪ sh_32k). Since sh_6k's `H_z`
is the constant 0.3653 and sh_32k's p50 is 1.9573, the pooled p75 is
essentially an sh_32k statistic that has been diluted by 100 constant rows —
it describes neither subset. This violates the repo's own rule (`CLAUDE.md`:
*"Report stratified, never pooled across subsets"*, store sizes 455 → 18,332).

**Recommendation to state explicitly: a pooled percentile cannot be justified
here.** Pooling percentiles across subsets is defensible only when the
subsets are exchangeable draws from one population. These are not: `n_chunks`
differs by 4.5x (2 vs 9), `H_z`'s support differs (a point mass vs a
distribution), and its median moves 0.365 → 1.957 across the split — the
quantity is a deterministic function of store size as much as of ambiguity.
The re-fit should therefore report **per-subset thresholds** and, if a single
operating value is needed for a subset the gate has not been fit on, obtain it
from a stated scaling rule (e.g. as a function of `n_chunks`/`ln m`) rather
than from a pooled percentile — with the rule declared before any confirmatory
use. If a pooled number is nevertheless kept for continuity, it must be
labelled as such and never described as "the calibration threshold".

Also note in the report: `entropy_ceiling_ln_m` is `ln(n_chunks)` — for sh_6k
that is `ln 2 = 0.693`, so **no** threshold above 0.693 is reachable there at
all, which is the general form of defect (a).

## 4. What must NOT happen

- No re-fit on `sh_64k`/`sh_262k`, and no confirmatory run of any kind.
- No threshold from the truncated (L512) era may be used to justify a live
  decision once this runbook has been executed; if the re-fit is not done, the
  honest statement is "thresholds unavailable", not the old numbers.
- Do not delete or copy `hnav/_cache/emb/` between machines.
- `hnav/stage1/stale_suppression_probe.py` and
  `hnav/labeling/question_strata.py` belong to other agents — untouched here.

## 5. Deliverables

1. `stage0_results/refit_threshold_diff.md` — the table above, per subset,
   plus defects (a)/(b) and the pooling recommendation.
2. Refreshed measurement JSONs committed under `stage0_results/` with a
   `_L8192` suffix (keep the L512 originals — evidence is never deleted).
3. A one-line verdict: do the corrected thresholds move enough to change any
   conclusion drawn from the old ones? Answer per subset, with the numbers.
