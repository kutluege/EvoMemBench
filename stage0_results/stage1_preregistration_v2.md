# Stage-1 Confirmatory Campaign v2 — PRE-REGISTRATION  ·  **REGISTERED**

> **Registered 2026-08-15, before any `sh_64k` inference of any kind.** The
> commit that adds this file is the timestamp of record; the campaign artifact
> must carry a `git_head` at or after it. Supersedes
> `stage0_results/stage1_preregistration.md` (WITHDRAWN, retained as evidence).
>
> **Authority.** Supervisor verdict APPROVE-WITH-NOTES and user authorization,
> both 2026-08-15, conditional on the audit passing — it did, independently
> confirming every accuracy/McNemar/p/token figure, the uncached A/A floor at
> 0/0 twice, `page_edit ≡ probe surgery` at 0 mismatches over 60 draws for both
> mechanisms, gold-freedom on three checks including commit ORDER, and precision
> 1.000000 re-derived from parse truth over all 2,673 deletions. The user
> separately accepted `ambiguity_mode="none"` as a declared deviation.
>
> ## ⛔ ONE OPEN DECISION — §0. Do not start the confirmatory run until it is made.
>
> The harness this document was ordered to scope the claim to — the whole
> context as a single `Memory 1:` block — **cannot be executed on `sh_64k` at
> all.** It is 75,886 tokens against a 65,536-token server window. §0 states the
> measurement, the two available branches and their costs. Both branches are
> fully specified below **in advance**, so whichever is chosen, no analysis
> choice is made after seeing data. Everything else in this document is
> registered and fixed.

---

## 0. The blocker, measured before anything was planned around it

`build_prompt(whole sh_64k context, question)` tokenized by the frozen :8003
server's own tokenizer (`/tokenize`, `Qwen/Qwen3-4B-Instruct-2507`):

| subset | facts | chunks @4096 | retrieval complete at `top_k`=10? | whole-context prompt | top-10 page |
| --- | --- | --- | --- | --- | --- |
| sh_6k | 455 | 2 | **yes** | 6.7k tok | 6.5k tok |
| sh_32k | 2,310 | 9 | **yes** | 34.3k tok | 34.1k tok |
| **sh_64k** | 4,580 | **17** | **no — 10 of 17** | **75,886 tok** | ~42.4k tok |
| sh_262k | 18,332 | 67 | no — 10 of 67 | ~280k tok | ~42.5k tok |

Two independent facts follow, either one sufficient:

1. **Infeasible.** 75,886 > 65,536 by 10,350 tokens (15.8% over). `SUPPRESS`
   shortens the prompt by ~3.5%, which leaves ~73.2k — still over. **No arm
   fits**, so this is not a near-miss that a slightly smaller edit rescues.
2. **Not the deployed setting.** `sh_64k` is 17 chunks and the benchmark
   retrieves 10, so the system under study never sees ~41% of that context. The
   whole-context harness was a *deliberate, documented* deviation that was
   justified on the calibration split precisely because retrieval there is
   complete (2 and 9 chunks ≤ 10). That justification expires at `sh_64k`.

### Branch A — retrieval-path harness at `sh_64k` (recommended)

The page is the benchmark's own top-10 chunks in similarity-rank order, edited
through the shipped seam `MABAdapter.apply_read_decision`. ~42.4k tokens, fits
the frozen substrate untouched, and is the setting the deployed system actually
occupies. This merges the supervisor's items 2 and 3 **out of necessity, not
preference**, and it makes the calibration-split retrieval-path arm (§10) a
prerequisite rather than an extra: without it there is no bridge from the
whole-context calibration evidence to a retrieval-path confirmatory number.

Cost: the calibration bridge (2 × 500 calls) plus `sh_64k` (500 calls).

### Branch B — whole-context at `sh_64k` on a re-served substrate

Requires restarting the chat server with a larger `--max-model-len` and more KV
cache. This **breaks the frozen-substrate identity** against every calibration
number, including the two cross-run native checks that agreed 100/100 per
question and which are the sole reason the detector/oracle ratios are readable.
It also still measures a setting the benchmark never occupies (fact 2 above).

**Recommendation: Branch A.** Branch B buys a harness match at the cost of the
substrate match, and the substrate match is what the audit relied on.

Until this is decided, **no `sh_64k` inference is run.** The calibration-split
work in §10 proceeds, because it is authorized, non-confirmatory, and required
under Branch A anyway.

---

## 1. The claim, correctly scoped  *(requirement a)*

> On the MemoryAgentBench `Conflict_Resolution` single-hop arena, deleting the
> stale member of every **verified** conflict group from the assembled page —
> at FACT granularity, decided without any access to answers — raises accuracy
> on the conflicted stratum, at no cost on the non-conflicted stratum and at no
> token cost.

Everything that qualifies it, stated rather than implied:

- **Harness.** Per §0. The claim is scoped to the harness actually run and to no
  other. It is *not* a claim about the benchmark's default end-to-end pipeline
  unless Branch A is chosen, in which case it is.
- **Firing is unconditional.** At the frozen operating point the gate's
  ambiguity precondition is off, so the policy inspects **every** question
  (coverage 1.000 on both calibration subsets). There is no "only when the
  ranking looks ambiguous" story.
- **What the detector actually is.** Fact-level embedding geometry (pair cosine
  ≥ 0.90, leave-one-out span residual < 0.44) **+ a parsed-key subject-identity
  screen** (`MABAdapter.same_key_pair`) **+ bidirectional NLI contradiction ≥
  0.90**. That is the whole detector.
- **`nmargin` and `H_z` are INERT in this configuration.** They are carried in
  the frozen thresholds for the record and are consulted by nothing, because
  `ambiguity_mode="none"`. The reason is that they are the only gate inputs
  computed from CHUNK embeddings, which are still truncated at 512 of ~4,096
  tokens (the T12 defect, un-refit). **Consequence, stated plainly: the shipped
  mechanism is NOT "the frozen Stage-0 gate". The Stage-0 precondition layer is
  unvalidated here — it was switched off, not switched on and passed.** Any
  write-up that describes this as the Stage-0 gate operating end to end is
  wrong. Re-fitting the chunk embeddings and re-testing that layer is future
  work, not evidence.

---

## 2. Subsets  *(requirement b)*

**`sh_64k` ONLY.** Single confirmatory subset, single shot.

**`sh_262k` is excluded from the confirmatory claim.** Two measured reasons:
its gold-not-latest exposure is 3/76 = 3.9% (the highest of the four), and m3
measured net *harm* from intervention at that scale. If it is examined at all it
must be declared **exploratory**, run and reported separately, and must not
enter the confirmatory statistic under any circumstance.

`sh_6k` and `sh_32k` remain the calibration split and are never re-tuned.

---

## 3. Arms

Identical in structure to the T12/T13 design, so the confirmatory run is
readable against both.

| arm | what it does | role |
| --- | --- | --- |
| `native` | untouched page | baseline |
| `native_repeat` | same prompt, independent second call | **A/A floor**, uncached by construction |
| `detector_suppress` | `ReadFactPolicy("suppress")` → drop every stale member of every verified group | **the confirmatory arm** |
| `detector_demote_late` | `ReadFactPolicy("demote_late")` → each group's LATEST carrier to the page end | reported, **not** part of the claim |
| `detector_anti` | measurement-only mirror: the same carriers to the FRONT | direction control, reported (see §8) |

Grading: `hnav.labeling.counterfactual.substring_exact_match`, the transcription
of the benchmark's own evaluator. `generation_max_length` 10, temperature 0.

**Operating point: frozen, and not touched on `sh_64k`.**
`stage0_results/stage1_operating_point.json` (commit `4f66c52`, 2026-08-15
15:30 UTC) — `cos_pair 0.90 · r_min 0.44 · ambiguity_mode none ·
nli_contradiction 0.90 · pair_filter True`. Fit on `sh_6k`+`sh_32k` from
detection quality only, with no LLM, no accuracy and no gold answer in the
objective. **Nothing is tuned on `sh_64k`.**

---

## 4. Primary success criterion, in McNemar terms  *(requirement e)*

All three must hold. Discordant pairs only; `b` = native right / arm wrong,
`c` = native wrong / arm right; `p` is the exact two-sided binomial on `b+c`.

1. **Conflicted stratum:** `net = c − b ≥ +10` **and** exact `p < 0.01`.
2. **Protected stratum:** the §5 criterion.
3. **Token cost:** `delta_chars_vs_native ≤ 0` for `detector_suppress`.

Bare Δaccuracy is reported but is not the criterion. The threshold is set in
advance at +10 because with `b` small that is already `p ≈ 0.002`, and because
the calibration effects (+62 of 74, +44 of 65) must be allowed to shrink
substantially — see §7 — without the design silently redefining success.

**Failure is a result.** If the criterion is not met, the outcome is reported as
a negative confirmatory result and the mechanism does not enter the thesis as an
improvement claim.

---

## 5. Protected stratum, with its noise floor  *(requirement d)*

The non-conflicted stratum is natively 26/26 and 35/35 on the calibration
subsets, so it is a near-noiseless control and any loss there is signal — with
one measured exception that must not be allowed to decide a one-shot campaign.

**The measured exception.** On `sh_6k`, `detector_suppress` lost exactly one
unique-stratum question: native emitted `"Shinzō Abe"`, the suppressed arm
emitted `"Sinzō Abe"`. A dropped letter. The gold fact was **still on the page**;
nothing about it was deleted. The substring-exact evaluator scores it wrong. That
is a malformed generation, not information loss.

**Criterion, chosen and justified.** Both parts are required.

- **(5a)** unique-stratum `net ≥ −1`.
- **(5b)** every unique-stratum loss is classified by a rule fixed here, in
  advance:
  - `malformed_generation` — the gold value is **present in the page the arm
    was shown** AND `difflib.SequenceMatcher(native_output, arm_output).ratio()
    ≥ 0.8`;
  - `information_loss` — otherwise.
  - **A single `information_loss` on the unique stratum voids the protective
    claim, whatever the net is.**

*Why this rather than N>1.* A replicate at `sh_64k` costs another ~500 calls at
~42k prompt tokens each (~21M tokens, hours on a shared GPU) and would buy
little: the A/A floor has now been measured at **exactly 0/0 discordant on 200
paired questions across two subsets**, i.e. this substrate does not flip answers
between identical calls, so a within-run replicate mostly re-measures zero. What
N>1 would genuinely protect against is one malformed generation deciding the
outcome — and (5b) addresses that failure mode *directly and falsifiably*
instead of averaging over it. If (5a) fails while every loss is classified
`malformed_generation`, that is reported as an inconclusive protective result
and a replicate is then justified; it is not silently rounded to a pass.

---

## 6. Harm ceilings and the gold-cut prediction  *(requirement c)*

The detector applies the benchmark's own stated rule — the highest serial is
newest — so on questions where the gold value is **not** carried by the highest
serial, it deletes the gold. This is countable from the parse in advance.

| subset | conflicted | gold NOT latest | exposure | conflicted-question recall | **predicted gold-cuts** |
| --- | --- | --- | --- | --- | --- |
| sh_6k | 74 | 0 | 0.0% | 0.973 | 0 — **observed 0** |
| sh_32k | 65 | 2 | 3.1% | 0.938 | 1.88 → 2 — **observed 2** (1 became an accuracy flip) |
| **sh_64k** | 66 | **2** | **3.0%** | 0.957 (pooled) | **1.91 → 2** |

**Registered prediction: `n_conflicted_gold_cut` on `sh_64k` = 2, and the only
arithmetically possible outcomes are 0, 1 or 2.** Of those, at most 2 can appear
as accuracy flips, and fewer if the affected questions were already wrong
natively (which is what happened on `sh_32k`: 2 cuts, 1 flip).

This is the most falsifiable element of the design and is committed to in
advance. The campaign artifact reports observed against predicted, and a
mismatch is reported as a mismatch — it is not re-explained afterwards.

**Additional pre-registered harm ceilings:**

- `n_suppressed_harmful` (a deleted fact that carries its key's *current* value,
  judged per key over the whole drop set) must be **0**. It was 0 on all 2,673
  calibration deletions. Any non-zero value is a void condition (§7).
- Pooled harm on the conflicted stratum: `b ≤ 4` (i.e. ≤ 2 above the 2 predicted
  gold-cuts). Exceeding it does not void the run but must be reported as the
  criterion having been met with unexplained harm, and blocks the improvement
  claim pending forensics.

---

## 7. Void conditions  *(requirement f)*

If any of these holds, the run is **void**: it is reported as void, no
confirmatory claim is made from it, and it does not count as the single shot
having been spent on a negative result.

1. `n_page_edit_mismatch > 0` — the probe-style arm and the shipped `page_edit`
   path disagree on any question. The measurement would not be measuring the
   mechanism that ships.
2. **Native arm out of band.** `native` overall accuracy outside **[0.30, 0.50]**.
   Derivation, fixed in advance: m3-harness `accuracy_native` for `sh_64k` is
   0.440, and the measured m3→campaign-harness offset on the calibration split
   was −0.04 (`sh_6k` 0.33→0.29) and −0.05 (`sh_32k` 0.47→0.42), predicting
   ≈0.39–0.40; the band is that ±0.10. This is a substrate/harness sanity check,
   not a hypothesis test. Additionally the unique stratum must be ≥ 0.80 native
   — the entire protective design presumes that stratum is near-noiseless.
3. **A/A floor non-zero.** `b + c > 0` between `native` and `native_repeat`.
   Measured 0/0 on 100 questions on each calibration subset; a non-zero floor
   means the substrate changed under us and every paired statistic is unreadable.
4. `n_suppressed_harmful > 0` in the frozen-detection audit on `sh_64k`.
5. Any unique-stratum `information_loss` under the §5b classifier (voids the
   protective claim specifically).

---

## 8. Declared limitations  *(requirements g and i)*

1. **The 512-token truncation defect is un-refit.** Chunk embeddings were
   computed from ~12% of each chunk. It does not touch this result — fact
   vectors are unaffected and were *proven* identical to the prepass's to
   8.9e-16 — but it is why `nmargin`/`H_z` are inert (§1), and it means the
   Stage-0 precondition layer is untested rather than validated.
2. **The 50-fact pool cap, and the recall trend it produces.** The gate sees the
   50 most query-similar facts of the page. Measured:

   | | sh_6k | sh_32k | direction |
   | --- | --- | --- | --- |
   | pair recall vs the whole page | 0.0885 | 0.0151 | falling fast with store size |
   | conflicted-question recall | 0.973 | 0.938 | falling |

   **`sh_64k` is 4,580 facts against `sh_32k`'s 2,310, so the effect is expected
   to be SMALLER than `sh_32k`'s +44 — and under Branch A smaller again, because
   retrieval itself is incomplete there (10 of 17 chunks).** No part of the
   write-up may present +44, or +62, as transferring to `sh_64k`. The
   pre-registered threshold is +10 for exactly this reason.
3. **New failure mode at `sh_64k`, absent from all calibration evidence:
   incomplete retrieval.** ~41% of the context is off the page, so the queried
   key's superseder may simply not be there. A detector cannot suppress a fact
   it never sees, and it cannot promote one either. This is unmeasured and is
   the single largest source of uncertainty in the transfer.
4. **Parse coverage.** `conflict_analysis.parse` covers 4,563/4,580 = **99.63%**
   of `sh_64k` facts. The 17 unparsed facts cannot pass the identity screen, so
   they can never join a group; in the harm audit an unparsed deletion is
   counted **as harmful**, which is the conservative direction.
5. **Whole-context vs retrieval-path.** All calibration evidence is
   whole-context. §0 and §10 exist because of this gap; under Branch A the
   confirmatory number is retrieval-path and the calibration bridge is what
   makes it interpretable.
6. **The `anti` control is inconsistent across subsets** *(requirement i)*: it
   measured **−4 on `sh_6k`** (harmful, as the oracle's `anti` was) and **+6 on
   `sh_32k`** (helpful, where the oracle's `anti` was −4). Two differences are
   known: the oracle arm additionally moved the most recent STALE fact to the
   END, an adversarial second edit this mirror does not make; and the detector
   stacks ~13 latest carriers at one edge of a 2,310-fact context rather than
   moving a single fact. At 32k length both edges appear privileged
   (`demote_late` +9 and `anti` +6 both help). **Therefore the placement
   direction is NOT established for the detector-driven version, `anti` is
   registered as a reported control only, and no part of the success criterion
   depends on it.** Suppression is untouched by this.
7. Single model (`Qwen3-4B-Instruct-2507`), single arena, single run.

---

## 9. Execution discipline  *(requirement h)*

- **Analysis code is committed with this document and is not modified between
  registration and reporting:** `hnav/stage1/detector_gap.py` (arms, grading,
  McNemar, strata, token accounting, oracle comparison, gold-cut accounting),
  `hnav/core/read_policy.py`, `hnav/adapters/mab_adapter.py`. The campaign
  artifact records `git_head`; it must be at or after this file's commit.
- **Single shot.** One run, one operating point, one subset. No re-runs under a
  different operating point, no second look with a different threshold.
- **No optional stopping.** All 100 questions × 5 arms are executed before any
  accuracy figure is inspected. The script computes every statistic in one pass
  and writes one artifact.
- **`HNAV_MODE`** is `off` for the measurement harness (`require_not_live`);
  under Branch A the shipped seam is exercised through `page_edit` /
  `apply_read_decision` directly, which the tests pin as byte-identical to the
  armed live path.
- Whatever comes out is reported: table, gold-cuts observed vs predicted,
  void-condition status, and the limitations above restated.

---

## 10. Companion exploratory arm — retrieval path on the CALIBRATION split

**Explicitly NOT part of the confirmatory claim**, reported separately, and run
on `sh_6k`/`sh_32k` only.

The deployed system reads a rank-ordered page of retrieved chunks, not one
whole-context block. On the calibration split retrieval is complete (2 and 9
chunks ≤ 10), so switching harnesses there changes **only the block structure
and order** — which isolates that variable from retrieval incompleteness, the
variable that only appears at `sh_64k`. That gives the three-point decomposition
the claim needs:

| setting | retrieval | block structure | what it isolates |
| --- | --- | --- | --- |
| whole-context, calibration | complete | one block, context order | the mechanism (**done**: 0.984 / 0.957 of oracle) |
| retrieval-path, calibration | complete | top-10 blocks, rank order | **block structure** |
| retrieval-path, `sh_64k` | **incomplete** | top-10 blocks, rank order | **+ retrieval incompleteness** |

Under Branch A this is a prerequisite for interpreting the confirmatory run, not
an optional extra. It is registered here so that its result — whatever it is —
is on the record before the confirmatory run, and so that a weak result here
cannot be quietly dropped.

If time or GPU forces a choice, the confirmatory run comes first.

---

## Amendment 1 — a second Branch A prerequisite  ·  2026-08-15, post-registration

**This amendment only ADDS a constraint and a void condition. It relaxes
nothing, changes no criterion, no threshold and no prediction.** It is recorded
separately, with its own timestamp, because a registered document must not be
silently edited.

**Measured after registration.** Every `sh_64k` vector the harness would need is
already in the shared cache — 4,580/4,580 facts and 17/17 chunks — but all of
them sit under the pre-T12 namespace `Qwen_Qwen3-Embedding-4B|float32`, i.e.
they were embedded with the **512-token truncation defect** in force. Nothing is
cached under `|L512` or `|L8192`.

For facts this is harmless and already argued (§8.1): a fact is one short
sentence, far under 512 tokens, and the vectors were *proven* identical to the
prepass's to 8.9e-16.

For CHUNKS it is not harmless **at `sh_64k` specifically**, and the reason is new:

- on the calibration split, chunk vectors only decide the *order* of a page that
  contains every chunk anyway (2 and 9 ≤ `top_k` 10), so a defective ranking
  changes nothing about *what the model sees* — which is why every committed
  calibration result stands unaffected;
- at `sh_64k`, chunk vectors decide **which 10 of 17 chunks are on the page at
  all**. A ranking computed from ~12% of each chunk would select the page, and
  the confirmatory number would then be about a page the benchmark's own
  retriever would not have produced.

**Prerequisite added for Branch A.** Before any `sh_64k` confirmatory run, the
17 `sh_64k` chunks must be re-embedded at the corrected `max_length` (8192, the
current `DEFAULT_MAX_LENGTH`) and the prepass ranking recomputed from those
vectors. The re-embedding is trivial compute (17 texts) but currently blocked:
the fp32 embedder needs ~17 GB and both GPUs are held by the two chat servers.
Freeing the :8003 card and restoring it byte-identically is acceptable; the
user's :8000 is not ours to touch.

**Void condition 6 (added).** The `sh_64k` confirmatory run is void if its
chunk-level ranking was computed from 512-truncated chunk vectors. The run
artifact must record the embedding-cache namespace actually used, and it must be
the `L8192` one for chunks.

**Note for Branch B.** Branch B does not need this — a whole-context prompt has
no retrieval step — but Branch B remains blocked by §0's window arithmetic, so
this does not revive it.
