# Generalisation protocol: additions proposed before registration

**DRAFT, 23 Nov 2026.** Text to be merged into `PROTOCOL_GENERALISATION.md` (draft v0.1, which
the co-author has seen) before it is registered on 26 November. v0.1 itself is left untouched
until both authors agree. Five values in square brackets must be fixed at registration:
`[MODEL]`, `[ENCODER]`, `[HARDWARE]`, `[HOSTED]`, `[MARGIN]`. Section numbers are those of v0.1.

Why these additions: the claims agreed on 23 November (`journal/WEEKLY_PLAN.md` §1) compare the
method with language models on cost and accuracy. A comparison added after the results are in
would be read as chosen for its outcome, so each one is written down here with what will be
reported and what may be said.

## §4 Arms — add

- **End to end, two more baselines:** raw cosine with recency and no NLI check; the page sorted
  by serial number with nothing deleted. Thresholds are fitted as for the other baselines.
- **Generative comparator.** One call per question to `[MODEL]` that reads the same retrieved
  records and lists those stating a superseded value; the listed records are deleted (each
  group keeps its highest serial) and the answering step is unchanged. The prompt is written
  and frozen on the calibration split; no test example is used.
  *Suggested `[MODEL]`: Qwen3-4B-Instruct-2507, the reference answering model, so that no new
  model enters the study.*
- **Pair level, second encoder `[ENCODER]`.** The screen is refitted for it by the C3 procedure
  on the calibration split. Pair-level AUROC and TPR at FPR 10⁻³ only; no end-to-end run.
  *Suggested: bge-m3 or multilingual-e5.*
- **Hosted reference model `[HOSTED]`.** A commercial model whose weights and parameter count
  are not public, run on the three original stores and the new test store with the same
  retrieved page, prompt and scoring as the local models, in two arms: the unedited page and
  the page after the method's deletions (the frozen plan on the original stores, the C3 plan on
  the new store). It is reached through non-interactive Claude Code calls from an empty
  directory, with the system prompt replaced by the benchmark's and all tools off; a pilot of
  ten questions must show that the reported input tokens match the length of the prompt before
  any reported run. One run per cell; three on the 64K store, because the sampling temperature
  cannot be set through this route. Model identifier, client version, flags, dates and token
  counts are recorded for every call.
  *Proposed `[HOSTED]`: Claude Sonnet 5.5 as the large model and Claude Haiku 5.5 as a second,
  cheaper reference (three original stores only if usage limits bind).*

## §5 Secondary analyses — add (exact p-values where a test applies, no success claim)

- **Generative comparator** against native and against H-Nav-GEO under C3 (exact McNemar); its
  harmful-deletion rate as in P2.
- **Cost.** Wall-clock time and peak memory per question for the H-Nav-GEO filter and for the
  generative comparator, median and interquartile range over the test questions, on
  `[HARDWARE]`, with prompt and generated tokens for the comparator. For the hosted model,
  input and output tokens per question and the cost they imply at the public list price on the
  day of the run; the paper states that this is a list-price figure and not an amount paid.
- **Hosted reference.** For each store, conflicted-question accuracy of (i) the local reference
  model on the unedited page, (ii) the same model after the method's deletions, (iii) the
  hosted model on the unedited page, (iv) the hosted model after the deletions. Reported with
  them: the share of the gap closed, ((ii) − (i)) / ((iii) − (i)), given only where (iii)
  exceeds (i); and (iv) − (iii), whether the deletions also help the hosted model.
- **Pair-level readers.** On the validation sample of the annotation protocol
  (`PROTOCOL_ANNOTATION.md`, stage 5), agreement with the human labels of: a cosine threshold,
  the full screen, the NLI check alone, GPT-5 mini and Claude Fable 5.2, with the cost of each
  per 1,000 pairs. The rule-based parser is shown as the schema-keyed reference.
- **Label sensitivity.** Pair-level AUROC and TPR recomputed on the adjudicated labels of the
  annotation protocol (stage 6), beside the figures on the released labels.

## §7 Decisions and negative results — add

- P3 stays restricted to non-generative baselines (H5). The generative comparator is reported
  beside it with its cost. If it is significantly ahead on accuracy, the paper says so and
  states the method's contribution as cost and independence from a generative call.
- **Wording about the hosted model.** The paper says the local model with the method is
  "comparable" to the hosted model only where (ii) is within `[MARGIN]` points of (iii) on
  conflicted questions on the new test store and on the 64K store. Otherwise it reports the
  share of the gap closed and the cost, and makes no claim of parity. The measured comparison
  of the local 4B model after deletions with the local 9B model on the unedited page is
  reported in either case.
  *Proposed `[MARGIN]`: 5 points.*
- The hosted model runs at a stated reasoning effort while the local models run with thinking
  disabled; the paper states this next to the comparison.
- The label validation is governed by `PROTOCOL_ANNOTATION.md`, not by this protocol.
