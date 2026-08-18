# Prompt — Build the presentation evidence pack

*Paste everything below the line into a fresh Claude Code session opened on this
repository. It is self-contained: every file path and JSON key path in it has
already been verified to exist.*

---

## Your task

I am presenting this project to my thesis advisor. I have chosen 15 pieces of
evidence. For each one you must do **two** things:

1. **LOCATE** — find the evidence in the repository and tell me *exactly* where
   it lives: the file path, the JSON key path (or line numbers for source
   files), and the exact numbers read from it. I need to be able to open that
   file, look at that spot, and screenshot it for a slide.
2. **VISUALIZE** — if the evidence has enough underlying data to make a real
   chart, produce the chart. If it does not, say so explicitly and give me the
   pointer instead. **Do not fake a chart out of two numbers.** I will
   screenshot the file myself for those.

## Hard rules

- **Offline only.** No GPU, no embedding server, no LLM calls, no network. Every
  number must come from a file already committed in this repository. The GPU box
  is not reachable — anything that needs it is out of scope, and you should say
  so rather than approximate it.
- **Never invent or interpolate a number.** If a figure is not in an artifact,
  write `NOT IN REPOSITORY` and explain what would be needed to get it.
- **Read numbers from the JSON artifacts, not from the markdown reports.** The
  reports are secondary. Where a report and an artifact disagree, the artifact
  wins — but see "Numbers to state carefully" below before changing anything.
- **English** for all output.
- Recompute derived numbers yourself (sums, rates, ratios) rather than trusting a
  summary field, and show the arithmetic in the index file.
- `pip install matplotlib` if it is missing. No seaborn, no plotly.
- **Load the `dataviz` skill before writing any chart code.**

## Deliverable

Create a directory `presentation_evidence/` containing:

```
presentation_evidence/
├── EVIDENCE_INDEX.md          the main deliverable — one section per item
├── figures/                   *.png (300 dpi) AND *.svg, one pair per chart
└── data/                      the extracted numbers as .csv / .json, one per item
```

`EVIDENCE_INDEX.md` must have **one section per numbered item below**, each with:

- **Claim** — the one sentence this evidence supports, as I will say it on the slide.
- **Source** — file path + JSON key path (or `file.py:line`) + the exact value.
- **Numbers** — a small markdown table, slide-ready.
- **Figure** — the filename, or `NO CHART — screenshot <exact location>` with a
  one-line reason.
- **Caveat** — anything that would embarrass me if the advisor asked. Be blunt.

Finish with a short **"Numbers to state carefully"** section (see below) and a
**"What is missing"** section listing anything you could not produce offline.

---

# The 15 items

Paths below are verified. Use them as your starting point, but confirm each value
yourself.

---

## 1. Old and new fact really are in the same retrieved context — MUST HAVE

**Claim:** the problem is not that retrieval fails to find the right fact; it is
that the old and the new fact arrive *together*.

**The Nobuhiro example is real and fully verifiable.** Confirm all of it:

- Dataset: `In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/data/Conflict_Resolution.json`,
  the entry whose `metadata.qa_pair_ids[0]` starts with `factconsolidation_sh_6k`.
  In its `context`, serial **91** = `Nobuhiro Watsuki is famous for Rurouni Kenshin.`
  and serial **259** = `Nobuhiro Watsuki is famous for The Fairly OddParents.`
- The question is index **1**; gold answer is `The Fairly OddParents`.
- Model behaviour: `stage0_results/stage1/stale_suppression_probe_sh6k.json`
  → `results[0].per_question[]` where `index == 1` → `arms.native.output` is
  `"Rurouni Kenshin"` (wrong) and `arms.oracle_suppress.output` is
  `"The Fairly OddParents"` (right). `plan` gives `gold_serials [259]`,
  `stale_serials [91]`.

**Find 2 more examples like this** from the same `per_question` list — pick
conflicted questions where `native` is wrong and `oracle_suppress` is right, and
where the subject is recognisable. Report for each: question text, gold, old
serial + text, new serial + text, native output, suppressed output.

**Important limitation you must state:** the *raw retrieved page* is not stored
in any artifact. The benchmark run files keep `query` (template + question) and
`input_len` but **not** the memory blocks. For `sh_6k` this does not matter —
only 2 chunks exist and both are always retrieved, so the page is the whole
context and can be reproduced byte-exactly with
`hnav/stage1/stale_suppression_probe.py::render_context`. Do that, and write the
reproduced page excerpt (the lines around serials 91 and 259, plus the prompt
head and tail) to `presentation_evidence/data/item01_page_excerpt.txt`.
For `sh_64k` the page cannot be reproduced offline — the prepass file is on the
GPU box (`detector_gap_confirmatory_sh64k.json` → `detector_inputs.prepass`
points at `/mnt/nvmes/...`). Say so; do not attempt it.

**Chart:** none. This is a text exhibit. Produce the excerpt file and tell me
what to screenshot.

---

## 2. Stale-fact dominance: 572 of ~575 errors — MUST HAVE

**Claim:** the model is not picking the wrong entity or the wrong relation. It
finds the correct memory slot and reads the stale value out of it.

**Source:** `stage0_results/question_strata.json` → `aggregate.errors_total`
= `{"stale_value": 572, "off_list": 3, "empty": 0}`. Total 575.

Also extract the per-run, per-stratum breakdown from `runs[].strata.conflicted.errors`
and `runs[].strata.unique.errors` (8 runs). Note that `runs[].strata.unique.errors`
is all zeros — that is part of the story.

Get the error-class definitions from `definitions.stale_value`, `definitions.off_list`
and `definitions.empty` and quote them, so the advisor can see the classification
was defined rather than eyeballed.

**Chart:** yes — a simple horizontal bar (572 / 3 / 0) is defensible, but the
better one is a stacked bar per run showing `correct / stale_value / off_list`
for the conflicted stratum across all 8 runs. Do both if cheap; the per-run one
is the one I will use.

---

## 3. Model is fine without conflict, collapses with conflict — MUST HAVE

**Claim:** the failure is not general language understanding and not retrieval.
The collapse is conditional on conflict.

**Source:** `stage0_results/question_strata.json`:
- `runs[]` — 8 entries, each with `run`, `file`, `strata.unique.{n,correct,accuracy}`
  and `strata.conflicted.{n,correct,accuracy}`.
- `aggregate.unique_accuracy_min/max` = 1.0 / 1.0 and
  `aggregate.conflicted_accuracy_min/max` = 0.0 / 0.0676.
- Raw run files: `stage0_results/t4_s2_evidence/sh_6k_{off,offA,offB,detA,detB,detC,detD,shadow}_results.json`,
  each with a 100-row `data` array carrying `qa_pair_id`, `output`,
  `substring_exact_match`.
- Question IDs per stratum: `subsets[].indices`.

Build a table: 8 rows (one per run) × columns `run | unique n/correct | unique acc |
conflicted n/correct | conflicted acc | overall acc`.

**Chart:** yes — this is the single most important visual in the deck. Two
grouped bars per run (unique vs conflicted accuracy), 8 runs on the x-axis, with
a horizontal line at 1.0 to show the unique stratum pinned at the ceiling. Make
the collapse impossible to miss.

---

## 4. The prompt already states the recency rule — MUST HAVE

**Claim:** the model is *told* the rule explicitly and still takes the stale fact.

**Source:** `In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/utils/templates.py`,
line **41**, key `'rag_agent'` (line 40 `'long_context_agent'` is nearly identical;
line 42 `'agentic_memory_agent'` is the archival-memory variant). The load-bearing
sentences are:

> "Each fact in the knowledge pool is provided with a serial number at the
> beginning, and the newer fact has larger serial number."
> "You need to solve the conflicts of facts in the knowledge pool by finding the
> newest fact with larger serial number."

Confirm which template the runs actually used, and quote the two sentences
verbatim with the exact line number. Also note the instruction that the answer
must come "**only** from the knowledge pool ... rather than the real facts in real
world", since that pre-empts an obvious advisor question about world knowledge.

**Chart:** none. Give me the file, the line, and the exact substring to highlight.

---

## 5. Position / ordering experiment — MUST HAVE

**Claim:** the physical position of a fact inside the prompt changes the answer.
Framing: we are **not** saying the model has no notion of the temporal rule. We
are saying that despite an explicit recency instruction, positional competition
exerts a strong effect on the response.

**Sources:**
- `stage0_results/stage1/stale_suppression_probe_sh6k.json` and `..._sh32k.json`
  → `results[0].by_stratum.conflicted.arms.{native,native_repeat,oracle_suppress,oracle_recency,anti}`
  and `results[0].by_stratum.conflicted.paired_vs_native` (McNemar b/c and exact p).
- `results[0].arms` in the same files describes what each arm does.
- Held-out mirror: `stage0_results/stage1/detector_gap_confirmatory_sh64k.json`
  → arms `detector_demote_late` (newest → end) and `detector_anti` (newest → front).
- Already built and committed: **`hnav/stage1/position_taxonomy.py`**. Run
  `python3 hnav/stage1/position_taxonomy.py --json presentation_evidence/data/item05_taxonomy.json`.
  It re-reads the raw outputs and classifies every answer as NEW / OLD / OTHER
  instead of just right/wrong. Use its output — it is the sharper version of this
  evidence. Background: `HNAV_POSITION_VS_RECENCY.md`.

**Paired examples:** from the same `per_question` arrays, find questions where
`native` and `oracle_recency` disagree, and report the condition → answer mapping
per question. Give me 3 clean ones.

**Charts:** yes, two.
1. Grouped bar of conflicted accuracy: `baseline / newest→end / newest→front`,
   for sh_6k and sh_32k (and sh_64k as the attenuated held-out mirror, clearly
   labelled as a different harness).
2. Stacked bar of the NEW / OLD / OTHER taxonomy per arm, per subset. Include the
   A/A row so the zero noise floor is visible.

---

## 6. Does geometry actually separate conflicts? — MUST HAVE

**Claim:** conflicting facts sit far closer in embedding space than random pairs.

**Source:** `stage0_results/final/m1_geometry_calibration.json` — a list of 4
objects (one per subset), each with `whole_blob_sim`, `diff_sim`,
`control_whole_blob_sim`, `qr_residual_new_vs_old` (each as
`{mean, p10, p50, p90}`), plus `separation_auc_conflict_vs_control`,
`n_conflict_pairs`, `n_control_pairs`, `model`, `dtype`, `gate_pass`.

**Read this limitation carefully and state it in the index.** This file stores
**summary percentiles only — the raw per-pair similarity arrays are not saved.**
So a histogram or an ROC curve **cannot** be drawn offline. Producing one would
require re-running `hnav/stage0/m1_geometry_calibration.py` with an embedder on
the GPU box. Do not fabricate a distribution.

**Chart:** yes, but the honest one — a percentile range plot (p10–p50–p90 as a
box-like interval) with two series, `conflict pairs` vs `control pairs`, across
the 4 subsets, annotated with the AUC. Title it as a **percentile summary**, not
a distribution. Also report `diff_sim` as a third series since it is in the file.

---

## 7. Geometry-only grouping ablation — MUST HAVE

**Claim:** conflict structure is genuinely present in the embedding geometry —
it is not the template and serial metadata doing the work.

**Source:** `stage0_results/final/m1b_grouping_ablation.json` — 4 objects, each
with `best_f1 {tau, precision, recall, f1, tp, n_predicted}`,
`equal_coverage {...}`, `recall_ceiling_from_knn`, `n_truth_pairs`,
`n_candidate_pairs`, and — importantly — a **full `pr_curve` array** swept over
`tau` from 0.5 upward with `precision`, `recall`, `f1` at each step.

This is the richest artifact in the set. Use the whole sweep.

Also quote the `interpretation` field verbatim in the index — it was written into
the output deliberately and it is the exact wording to use with the advisor.

**Chart:** yes, two.
1. Precision–recall curve, one line per subset, with the best-F1 operating point
   marked.
2. F1 vs tau, one line per subset, marking `best_f1.tau` per subset.

---

## 8. How the parser works — pointer only

**Claim:** relation, subject and value are not extracted by another LLM. A
validated deterministic regex parser runs over the benchmark's templated fact
structure.

**Source:** `hnav/labeling/conflict_analysis.py`, function `parse`. Coverage is
recorded as `parse_coverage` in `stage0_results/final/m1_geometry_calibration.json`
(99.56 on sh_6k) and `parse_coverage_pct` in the m1b file — report the value for
all four subsets.

Give me the function's line range and a worked example produced by actually
calling it:

```
"Nobuhiro Watsuki is famous for Rurouni Kenshin."
  → relation = ...   subject = Nobuhiro Watsuki   value = Rurouni Kenshin
```

Run it for real and paste the true output — do not hand-write the tuple.

**Chart:** none. Method slide only.

---

## 9. Span residual — no evidence needed

Rationale and mathematics only; I will explain it on the method slide. Just give
me the source location (`hnav/core/geometry.py`, the QR-residual function) and
confirm the two threshold values used at the shipped operating point:
`r_min = 0.44` and `cos_pair = 0.90` from
`stage0_results/stage1_operating_point.json` → `thresholds`. Confirm numerically
that `sqrt(1 - 0.44**2) = 0.898`, i.e. that the two screens agree rather than one
overriding the other.

**Chart:** none.

---

## 10. NLI alone is not safe — MUST HAVE

**Claim:** bidirectional NLI on its own false-verifies a large fraction of pairs;
adding a parsed subject-identity screen drives that to zero.

**Source:** `stage0_results/stage1/stage1_calibration.json` → `cells`, an array of
**162** objects. Each has `pair_filter` (the subject screen, true/false),
`n_verified`, `n_true_supersession`, `n_fv_diff_key`, `n_fv_same_object`,
`helped`, `harmed`, plus the grid coordinates `cos_pair`, `r_min_label`,
`ambiguity_mode`, `nli_contradiction`.

Compute the false-verification rate per cell as
`(n_fv_diff_key + n_fv_same_object) / n_verified` and report the range for
`pair_filter == false` versus `pair_filter == true`. Also report the grid from
`provenance.grid` and the NLI model from `provenance.nli_model`.

Precision at the shipped operating point: `stage0_results/stage1_operating_point.json`
→ `metrics.pair_precision`, `metrics.fact_precision`, `metrics.tp`, `metrics.fp`,
`metrics.n_questions` (**200 — this is the calibration split, not held-out**).

**Kyd/Marlowe example:** the contradiction score **0.99949 in both directions**
appears only in `TEZ_BULGULARI.md` around line 266 — there is **no JSON artifact**
behind that specific number. Report it with that provenance stated honestly, and
do not present it as machine-extracted.

**Chart:** yes — a strip or box plot of the per-cell false-verification rate,
two groups (screen off vs screen on), 81 cells each. The screen-on group
collapsing to a single point at zero is the whole message.

---

## 11. Why chunk-level intervention was rejected — short, main deck

**Claim:** conflict is fact-level, so a chunk-level intervention is too coarse. A
chunk carries ~230–260 facts; moving it to fix one conflict displaces hundreds of
unrelated facts. **Intervention granularity should match conflict granularity.**

**Source:** the *same* file as item 10 — `stage0_results/stage1/stage1_calibration.json`
→ `cells` (162). Aggregate `helped` and `harmed` and count net-positive cells,
**split by `pair_filter`**. Narrative: `STAGE1_NULL_ANALIZI.md`.

**Chart:** yes — scatter of `helped` (x) vs `harmed` (y) for all 162 cells,
coloured by `pair_filter`, with the `y = x` diagonal drawn. Everything sitting
above the diagonal is the point.

---

## 12. How close does the detector get to the oracle? — MUST HAVE, one small slide

**Claim:** the ground-truth-free detector recovers roughly 96–98% of the perfect
intervention's ceiling on calibration data.

**Source:** `stage0_results/stage1/detector_gap_sh6k.json` and `..._sh32k.json`
→ top-level key `detector_vs_oracle`. It carries the oracle probe it compares
against (`source`), the harness match (`same_harness`), and the native
cross-run check (`native_cross_run`). Extract the detector improvement, the
oracle improvement, and the ratio.

**Do not use** `detector_gap_retrieval_sh6k.json` / `..._sh32k.json` for the
headline ratio — those carry `harness_match: false` and an explicit
`harness_caveat` saying they compare across harnesses. Read the caveat and
mention it.

Also report the pair-level differences / missed cases if the file records them.

**Chart:** yes — a small grouped bar, detector vs oracle improvement, for sh_6k
and sh_32k, with the ratio printed above each pair.

---

## 13. Final held-out result — MUST HAVE

**Claim:** on held-out `sh_64k`, in one pre-registered run, fact-level suppression
of detector-verified superseded facts raised conflicted-stratum accuracy.

I will show exactly these four numbers on the main slide:
`25.8% → 56.1%` · `+20` · `p = 1.9×10⁻⁶` · `−0.31% tokens`
and say "0 conflicted questions were harmed" out loud.

**Source:** `stage0_results/stage1/detector_gap_confirmatory_sh64k.json`:
- `results[0].by_stratum.conflicted.arms.*` and `.unique.arms.*` — the 5 arms
  (`native`, `native_repeat`, `detector_suppress`, `detector_demote_late`,
  `detector_anti`).
- `results[0].by_stratum.conflicted.paired_vs_native.detector_suppress` —
  McNemar `b_native_only`, `c_arm_only`, `net`, `p_exact`.
- `results[0].tokens` — the token comparison.
- `results[0].harm` — harm counts by class and `voiding_questions`.
- `results[0].per_question` — 100 records, each with `index`, `stratum`, `key`,
  `truths`, `plan`, and per-arm `output` / `correct`. This is the question-level
  baseline-vs-H-Nav answer table.
- `results[0].void_conditions` — the 8 pre-registered conditions and their status.
- `preregistration` field points to `stage0_results/stage1_preregistration_v2.md`.

**You must also report the failure**, in the same section, not a later one:
`void_conditions.5_protected_stratum` has `status: "fail"` with
`voiding_questions: [77]` and `counts.refusal_after_edit: 1`. One non-conflicted
question regressed — the model refused to answer although the fact it needed was
still on the page. The registered conclusion is **effective, but not yet safe**.

**Chart:** yes — grouped bar, 5 arms × (overall, non-conflicted, conflicted), with
the McNemar b/c annotated on the suppression bar. Export the 100-row question-level
table to `data/item13_per_question.csv`.

---

## 14. 735/735 deletion precision — MUST HAVE

**Claim:** every suppressed fact was independently checked against benchmark
ground truth; all 735 were genuinely stale. This is a *different* claim from
accuracy — it answers "are you deleting the right things?", not "did the answers
improve?".

**Source:** `stage0_results/stage1/detector_gap_confirmatory_sh64k.json`
→ `results[0].void_conditions.4_no_harmful_suppression.observed` =
`{"n_suppressed_harmful": 0, "n_suppressed_superseded": 735, "n_suppressed_same_value": 0}`.

The **per-deletion list** is derivable: sum `len(per_question[i].plan.suppress_serials)`
over all 100 questions — it totals exactly **735**. Build
`data/item14_deletions.csv` with one row per deleted fact: question index, serial,
fact text (join against the dataset context), the key's gold value, and whether
that serial is the key's latest. Verify independently that none of the 735 carries
a current value, and report your own recomputed count rather than only quoting the
field.

Cross-check: `void_conditions.8_guards_and_positive_control.observed.positive_control.n_facts_suppressed`
also reports 735. Note that `n_fact_edits_applied` is 200 because it accumulates
across two editing arms — the file explains this in `counter_note`; do not
misread it.

**Chart:** none — it is a precision figure, not a distribution. Give me the table
and the exact JSON location to screenshot.

---

## 15. Is the effect just serving nondeterminism? — MUST HAVE

**Claim:** the serving stack is not fully deterministic, so small single-run
differences are uninterpretable — but H-Nav's effect is far larger than the
measured noise floor.

**Source:** `stage0_results/t4_s2_trials_summary.json`:
- `off_sem_per_run` (10 values) and `shadow_sem_per_run` (5 values) — the raw
  per-run accuracies.
- `noise_floor.within_off_mismatch_mean` (0.0304), `within_off_mismatch_max`,
  `within_shadow_mismatch_mean`, `cross_mismatch_mean` (0.0242), and `n_pairs`.
- `tost` — `p_lower`, `p_upper`, `equivalent`.
- `permutation` — `observed_delta`, `p_two_sided`, `reps`, `seed`.
- Protocol: `stage0_results/t4_s2_protocol.md`. Raw runs:
  `stage0_results/t4_s2_evidence/`.

The comparison to make: off↔shadow disagreement **2.42%** sits *below* the
baseline's own off↔off floor **3.04%**, while the final effect is ~19 accuracy
points overall on the conflicted stratum.

**Chart:** yes — dot plot of the 10 off runs and 5 shadow runs on one accuracy
axis, with the noise band shaded, and the final held-out effect drawn alongside at
the same scale so the size difference is visually obvious.

---

# Numbers to state carefully

I have already checked these against the artifacts. Do not silently rewrite the
existing reports, but **use the precise form in the evidence pack**, because an
advisor could catch the loose version:

1. **"0 of 162 configurations were net-beneficial" is not accurate.** In
   `stage1_calibration.json` the correct statement is: with the subject screen
   **ON**, **0 of 81** cells were net-positive (helped 228 / harmed 441). Across
   all 162 cells, **21** are net-positive — but every one of them has
   `pair_filter == false`, i.e. a detector that false-verifies a large fraction of
   pairs. Verify this yourself and state it in the screen-on form.

2. **735 and 2673 are different things.** `operating_point.metrics`
   (`tp 2673`, `fp 0`, `fact_precision 1.0`, `n_questions 200`) is the
   **calibration** operating-point selection, on sh_6k + sh_32k. The **735** is
   the held-out sh_64k suppression count. Never present 2673 as a held-out figure
   or merge the two into one precision claim.

3. Item 6's numbers are **percentile summaries**, not a distribution. Any chart
   must be labelled as such.

Everything else can stay as written in the existing reports.

# What must not be claimed

Read `HNAV_FINAL_REPORT.md` §10 before writing the index, and respect it. In
particular: the protective criterion was **voided** by one question, and that
belongs in the same breath as the improvement — never in a later paragraph. Do
not present calibration figures as held-out. Do not generalise beyond one arena,
one subset, one scale, one model, one shot.

# When you are done

Print a summary table: item number, LOCATED yes/no, CHART yes/no + filename,
and any item you could not complete offline.
