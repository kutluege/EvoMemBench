# H-Nav — What This Project Does, In Plain Language

*A guide for explaining this work to a supervisor. Written 2026-08-18.
Every number in this document comes from a committed measurement file in this
repository; the sources are named at the end of each section.*

---

## 0. The whole project in five sentences

LLM agents keep a memory of facts. Over time some facts get **replaced** by
newer ones — a person changes jobs, a value is corrected. When the agent later
looks something up, the retrieval system may hand it **both the old and the new
version**, and we measured that the model then answers with the **old one about
95% of the time**, even when it is explicitly told which one is newer.

**H-Nav** is a supervision layer that sits between the memory system and the
model. It reads the retrieved page *before* the model sees it, works out which
facts have been superseded, and **deletes them**. On held-out test data this
raised accuracy on conflict questions from **25.8% to 56.1%**, cost **fewer**
tokens, and harmed **zero** conflict questions — but one unrelated question
regressed, so the honest verdict is **"effective, but not yet proven safe."**

---

## 1. What problem is being solved

### 1.1 Where "memory" sits in an LLM agent

A memory-equipped agent has a loop like this:

```
    ┌──────────── WRITE PATH ────────────┐
    new information  →  embed it  →  store it in a vector database
                                              │
    ┌──────────── READ PATH ─────────────┐    │
    question  →  embed it  →  find the most similar stored items
                                     │
                                     ▼
                          "the retrieved page"  →  put into the prompt  →  LLM answers
```

Both paths can go wrong, and they go wrong in different ways:

| Path | What can go wrong |
|---|---|
| **Write** | The agent stores a fact that contradicts one it already has, or stores the same thing five times, or stores something useless. The memory slowly becomes inconsistent and bloated. |
| **Read** | The retrieval returns a mix of current and outdated facts. The model then has to work out which is which — and this is the failure we measured. |

### 1.2 The specific failure this project attacks

**"Stale-fact dominance."** The retrieval works correctly. The right facts are
found. Both versions are on the page. And the model reads the **outdated** one.

This is *not* a retrieval bug and *not* a hallucination. We classified ~575
errors: **572 of them were the stale value of exactly the right memory slot.**
The model found the right drawer and pulled out the wrong paper.

*Source: `HNAV_FINAL_REPORT.md` §5, `TEZ_BULGULARI.md` §A.*

---

## 2. Where we measure it (the testing ground)

We use one dataset inside the EvoMemBench suite:

```
EvoMemBench/
└── In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/
    └── dataset: Conflict_Resolution
        └── factconsolidation_sh_6k     455 facts    ← tuning data
            factconsolidation_sh_32k  2,310 facts    ← tuning data
            factconsolidation_sh_64k  4,580 facts    ← FINAL TEST (used once)
            factconsolidation_sh_262k 18,332 facts   ← never used
```

The four subsets are **the same task at four memory sizes**. Each has 100
questions.

### 2.1 What one task looks like

The memory is a numbered list of facts. **A higher number means a newer fact.**

```
  0. Thomas Kyd was born in the city of London.
 ...
 91. Nobuhiro Watsuki is famous for Rurouni Kenshin.       ← old version
 ...
259. Nobuhiro Watsuki is famous for The Fairly OddParents. ← new version (wins)
 ...
454. ...
```

> **Question:** What is Nobuhiro Watsuki famous for?
> **Correct answer:** `The Fairly OddParents` (fact 259, the newer one)
> **What the model actually answers:** `Rurouni Kenshin` (fact 91, the stale one)

Notice the trap: `Rurouni Kenshin` is the **real-world truth**. The benchmark
deliberately injects fake updates, so a model that leans on what it already
knows instead of reading the memory will answer the *old* fact. That is how the
benchmark separates "the model read the memory" from "the model already knew."

The prompt even **spells out the rule**: *"the newer fact has larger serial
number… you need to solve the conflicts by finding the newest fact."* The model
still fails ~95% of the time. That is a real limitation, not a prompt bug.

### 2.2 The discovery that reframed the whole project

Not every question involves a conflict. We split all 400 questions by whether
the key they ask about actually has two competing values:

| | questions with **no conflict** | questions **with a conflict** |
|---|---|---|
| sh_6k: how many | 26 | 74 |
| model's accuracy (8 independent runs) | **26/26 correct — every single run** | **0–5 / 74** |

Read that table again. The model is **perfect** when there is no conflict, and
**almost never right** when there is one.

**Three consequences, and they carry the whole thesis:**

1. The benchmark's headline accuracy (0.29–0.45) is produced almost entirely by
   the conflict-free questions. Anyone quoting "Conflict_Resolution accuracy"
   is largely measuring something other than conflict resolution.
2. Because the failure is **one single mode** (take the stale value), the room
   to improve is enormous — 71 of 100 questions wrong for one reason.
3. The conflict-free questions become a **zero-noise control group**: across 28
   pairs of repeated runs, not a single answer flipped there. So any drop in
   that group is a real signal, not noise.

*Source: `HNAV_HOW_IT_WORKS.md` §2.4, `TEZ_BULGULARI.md` §A.*

---

## 3. The methods — organized in three layers

The project has three kinds of method, and it helps to keep them apart when
explaining it:

```
LAYER 1  MEASUREMENT METHODS    "Are my instruments trustworthy?
                                 Is there anything to win at all?"
                                 → this is Stage 0

LAYER 2  DETECTION METHODS      "Which facts in this page are superseded?"
                                 → embedding geometry + parsing + NLI

LAYER 3  INTERVENTION METHODS   "What do I do about it?"
                                 → delete the stale fact (and nothing else)
```

Most published memory work jumps straight to Layer 3. The distinctive thing
about this project is that Layer 1 came **first**, and it killed two of the
three intervention ideas before they were ever built.

---

## 4. LAYER 1 — The measurement methods (Stage 0)

**Purpose:** before writing a single line of intervention code, prove that
(a) the signals we plan to use actually separate the cases we care about, and
(b) there is measurable room to improve.

The motivation is concrete: a **previous version of this project on a different
benchmark (BFCL) returned a null result** — the target failure class was only
~3.5% of decisions there, so there was nothing to fix. Here it is 65–77%. Arena
choice is part of the argument.

### Method 1.1 — Geometry calibration (does the core premise hold?)

**The premise being tested:** *conflicting facts sit very close together in
embedding space.* If false, the whole approach dies.

**Steps:**
1. Parse every fact into `(relation, subject, value)` with a validated regex
   parser (99.5% coverage).
2. Group facts that share `(relation, subject)`. A group with two different
   values is a real conflict — this is ground truth.
3. Build a **control set** of random *non*-conflicting fact pairs, same count.
4. Embed everything, normalize to unit length, measure cosine similarity.

**Result:**

| | conflicting pairs | random control pairs |
|---|---|---|
| median similarity | **0.964** | **0.60** |
| separation (AUC) | **≥ 0.9999** on all four subsets | |

An AUC of 0.9999 means the two groups barely overlap at all. The premise holds,
and this was set up as a **kill switch** — if median similarity had been below
0.70, the project would have stopped there.

**What it improves:** nothing directly. It *licenses* everything downstream.

### Method 1.2 — The grouping ablation (is the gain from geometry or from metadata?)

**The critique this pre-empts:** "Your benchmark gives you templated sentences
and serial numbers. Your gains come from that metadata, not from your geometry.
Your method would not work on real memory."

**Steps:** build a second grouper that uses **only** geometry — nearest
neighbours above a similarity threshold, no parsing, no serial numbers — and
score it against the regex grouper as ground truth.

**Result:** best F1 **0.892** (smallest store) → **0.757** (largest store),
precision 0.83–0.90.

**Interpretation, recorded verbatim in the output file:** geometry recovers most
of the grouping *without parsing*, which is what licenses applying this method to
substrates that have no templates and no serial numbers. It degrades with store
size, and that is stated rather than hidden.

### Method 1.3 — Retriever replica + fidelity check

To reason about retrieval offline, we rebuild the benchmark's index ourselves
(a "replica") and check it reproduces the benchmark's rankings exactly.

**Result:** top-1, top-k and rank correlation (Kendall τ) all **1.0000**, 400/400
sampled cases, maximum score error 4.5×10⁻⁵.

**This check caught a real bug.** The pipeline halted 16 seconds in because
agreement had collapsed to **0.24**. Root cause: the embedding server had been
started without a precision flag and defaulted to **bfloat16** instead of
float32. Vectors that should have length exactly 1 came back at 0.998–1.002, and
at that error size the ordering of near-identical chunks becomes unstable.
Restoring float32 gave 1.0000.

**This is a reportable finding on its own:** *serving an embedding model in
reduced precision can silently destroy retrieval fidelity while every component
still appears to work.*

### Method 1.4 — Shadow-mode neutrality (does the instrument disturb the experiment?)

H-Nav has three modes: `off`, `shadow` (compute everything, change nothing) and
`live` (actually intervene). Shadow mode is required to produce byte-identical
output to `off`.

It differed on 2 of 100 answers. Before calling that a bug, we ran the control:
**two identical baseline runs with no H-Nav code at all**. They differed on
**5 of 100**, with a 4-point accuracy swing.

**Finding:** the serving stack (vLLM) is **not run-to-run deterministic at
temperature 0** — continuous batching and prefix caching reorder floating-point
work. Byte identity was unachievable for *any* code. We replaced the criterion
with a pre-registered statistical equivalence test (TOST), which passed:
off↔shadow difference (2.42%) came in *below* the baseline's own noise floor
(3.04%).

**Why this matters for the thesis:** it establishes the **noise floor**. Any
single-run claim smaller than ~3 points is uninterpretable. Our final effect is
+19 points, well clear of it.

### Method 1.5 — Headroom measurement (how much is there to win?)

For every candidate write and every read, we ask counterfactually: *if H-Nav had
intervened here, could the answer have changed from wrong to right?*

| path | measured headroom |
|---|---|
| **write path** | after safety vetoes, would touch 0–1.6% of writes; **0.00** of those could change correctness on held-out data |
| **read path** | large, but an early repair experiment helped at one scale and net-harmed at the largest |

**Consequence: the write path was killed here, before any code was written.**
`hnav/core/write_policy.py` is now permanently forbidden by an automated test.

Important nuance for the defence: this is **the arena's answer, not the design's
failure**. In single-hop fact consolidation the retrieval already finds the
newest fact, so there is nothing left for a write policy to repair.

### Method 1.6 — The marginal-diff hypothesis test (a registered test that FAILED)

**Hypothesis (H2):** comparing only the *changed part* of two facts (the value)
adds predictive information beyond comparing the whole sentences.

**Method:** two nested logistic regressions, likelihood-ratio test, ΔAUC with a
clustered bootstrap.

**Result:** ΔAUC **+0.0674** (direction positive) but the likelihood-ratio test
gave **p = 0.341**, far above the required 0.01. The pre-registered conjunction
**did not pass**, and it is reported as a failure rather than reframed.

*Sources for §4: `STAGE0_REPORT.md`, `stage0_results/final/*.json`, `KAPI_KARARI.md`.*

---

## 5. LAYER 2 — The detection methods (how a stale fact is identified)

This is the technical core. It runs on the **retrieved page** at question time,
and it never sees the correct answer.

Design principle: **cheap and exact first, then linear algebra, then — only for
the few survivors — the expensive neural check.**

### Step 1 — Explode the page into individual facts

The retrieved chunks are big blobs of ~230–260 facts each. A validated parser
splits them back into individually addressable facts with their serial numbers.

**Why facts and not chunks?** Because we *measured* chunk-level operation and it
was actively harmful. See §6.1.

### Step 2 — Geometric filter (cheap, removes 99% of pairs)

**(a) Pair cosine similarity.** Every fact becomes a 2560-dimensional vector
(Qwen3-Embedding-4B), normalized to length 1. For unit vectors, cosine
similarity is just the dot product — one matrix multiplication scores everything.

```
"Nobuhiro Watsuki is famous for Rurouni Kenshin."
"Nobuhiro Watsuki is famous for The Fairly OddParents."     cos ≈ 0.97  ✓ candidate

"Nobuhiro Watsuki is famous for Rurouni Kenshin."
"Amy Winehouse died in the city of Camden Town."            cos ≈ 0.55  ✗ reject
```

Threshold: **0.90**, chosen on tuning data only.

**(b) Span residual — "how much of this fact is genuinely new?"**

This is the one piece of real linear algebra. Take a group of similar-looking
facts. Remove one member. Ask: *can I rebuild the removed fact from the others?*

Formally, project the removed vector onto the subspace spanned by the rest
(computed with a QR decomposition) and measure what is left over:

```
residual r = ‖ v − (projection of v onto the span of the others) ‖

r ≈ 0  →  the fact is essentially a restatement of what is already there
r ≈ 1  →  the fact is genuinely new information
```

A group survives only if **at least one member is almost entirely
reconstructible from the rest** (`min residual < 0.44`). That is the signature of
*one memory slot restated* — which is exactly what a supersession is — rather
than several distinct facts that merely look alike.

**A nice property worth showing an advisor:** for a two-member group these two
screens are the *same screen written two ways*. If everything else is unrelated,
`r = √(1 − cos²)`, so `r_min = 0.44` implies `cos > 0.898`. Pairing it with
`cos_pair = 0.90` means the two thresholds **agree** instead of one silently
overriding the other. The original Stage-0 value (`r_min = 0.1924`) implied
`cos > 0.981` — stricter than the median true-conflict similarity of 0.964,
which is precisely why it almost never fired.

**(c) ABTT whitening (optional, used where the store is big enough).** Sentence
embeddings are not spread evenly — a few directions are shared by nearly every
English sentence and carry no distinguishing information, yet they dominate the
dot product (this is why unrelated sentences sit at 0.6 rather than 0). The fix
is Mu & Viswanath's *all-but-the-top*: subtract the mean, find the top 3
principal directions by SVD, project them out, renormalize. It **refuses to run
on stores under 200 records** (the estimates would be noise) and records which
path it took, so the fallback rate is reportable rather than invisible.
Measured effect: separation AUC 0.936 → 0.955. Real, but modest — informative in
itself, because it says the raw geometry here was already strong enough.

**(d) Grouping is then a graph problem.** Nodes = facts. Edges = pairs passing
the cosine screen. Tentative groups = connected components. Deterministic
ordering, so the same input always gives the same grouping.

### Step 3 — The subject-identity screen (the most transferable finding)

Consider:

```
"Thomas Kyd was born in the city of London."
"Marlowe was born in the city of London."
```

Same template, same relation, same value — **different people**. Both can be
true. This is *not* a conflict.

So each fact is parsed into `(relation, subject, value)` and the relation **and**
subject must match:

```
(born in the city of, Thomas Kyd, London)
(born in the city of, Marlowe,    London)
                      ↑ subjects differ → REJECT
```

Unparseable pairs are **rejected, not trusted** — always the conservative
direction.

### Step 4 — Bidirectional NLI (the expensive check, on survivors only)

Surviving pairs go to a natural-language-inference cross-encoder
(`nli-deberta-v3-large`), scored in **both directions**:

```
premise "…famous for Rurouni Kenshin"  → hypothesis "…famous for The Fairly OddParents"   contradiction 0.99+ ✓
premise and hypothesis swapped                                                            contradiction 0.99+ ✓
                                                                    both agree → VERIFIED CONFLICT
```

One-way contradiction is rejected — it usually means one statement is more
specific than the other, not that they conflict.

**Why both Step 3 and Step 4? Because either alone is useless:**

| configuration | false-verification rate |
|---|---|
| bidirectional NLI **alone** | **33–93%** |
| NLI **+ subject-identity screen** | **0.000** (2,673 pairs, precision 1.000) |

The Kyd/Marlowe pair scores contradiction at **0.9995 in both directions**. NLI
alone would happily "verify" it as a conflict.

> **This is a standalone methodological contribution:** *NLI cannot verify
> memory conflicts on its own. The dominant failure class is
> same-template/different-subject. A parsed identity screen is what makes it
> safe.* Any memory-intervention result published without its detector's
> precision should be treated with suspicion.

### Step 5 — Name the newest member

Within a verified group, the fact with the highest serial number is current. If
the newest cannot be identified unambiguously — a tie, an unparseable serial —
**H-Nav does nothing to that group.** It refuses to guess.

*Sources for §5: `hnav/core/geometry.py`, `hnav/core/read_gate.py`,
`HNAV_HOW_IT_WORKS.md` §5 and §11.*

---

## 6. LAYER 3 — The intervention methods (and the two that were rejected)

### 6.1 Rejected method A — chunk reranking

**The idea:** promote the chunk that contains the newest fact toward the top of
the page. Nothing deleted, token-neutral.

**We tested 162 configurations with real LLM grading.**

| | |
|---|---|
| configurations with net benefit | **0 of 162** |
| questions helped | 228 |
| questions harmed | **441** |

It was not neutral, and it was not noise — it was **twice as harmful as helpful,
with a detector operating at precision 1.000.**

**The reason is granularity.** A chunk carries ~230–260 facts. Moving one chunk
to fix one conflict scrambles the relative position of hundreds of unrelated
facts. Signal-to-noise ≈ 1:250.

**Reportable lesson:** *intervention granularity must match conflict
granularity.* Also: a first look at the summary statistic said "no feasible
operating point," which reads like a null. Digging into the raw per-cell data
turned a null into a **directional finding**. That investigation is part of the
method.

### 6.2 The oracle probe — measure the ceiling before building anything

Before building a real detector, we measured what a **perfect** intervention
could achieve, using the correct answers to pick the target. This is a *ceiling*,
not a shippable system.

| intervention (tuning data) | sh_6k conflicted | sh_32k conflicted |
|---|---|---|
| do nothing (baseline) | 4/74 (5.4%) | 7/65 (10.8%) |
| repeat the baseline (A/A control) | 4/74 — **0/0 flips** | 7/65 — **0/0 flips** |
| **delete the stale fact** | **66/74 (89.2%)** | **53/65 (81.5%)** |
| move the newest fact to the **end** | 20/74 (27.0%) | 33/65 (50.8%) |
| move the newest fact to the **front** | 1/74 (1.4%) | 4/65 (6.2%) |

**Three things fall out of this one table:**

1. **The failure is repairable.** 5% → 89% is not a marginal effect.
2. **It answers a mechanism question.** Was the model *anchoring on the stale
   fact's presence*, or *overriding the context with its world knowledge*?
   Deletion lifting accuracy to ~85% settles it: **the model does read the
   context** — it just loses to whatever appears in a particular position.
3. **The front/end asymmetry names the mechanism: late-position anchoring.**
   The model latches onto text appearing late in the prompt. That
   *retroactively explains* why §6.1 failed — chunk reranking pushed the newest
   fact *upward*, away from the position that helps.

### 6.3 The shipped method — fact-level stale suppression

The surviving design is deliberately narrow. **Delete the superseded fact from
the page text. Nothing else.**

```
BEFORE (what the model would have seen):
  ... 90. ... 91. Nobuhiro Watsuki is famous for Rurouni Kenshin. 92. ...
  ... 258. ... 259. Nobuhiro Watsuki is famous for The Fairly OddParents. 260. ...

AFTER (what the model actually sees):
  ... 90. ... 92. ...
  ... 258. ... 259. Nobuhiro Watsuki is famous for The Fairly OddParents. 260. ...
```

**The safety rules that make the edit trustworthy:**

- **No renumbering.** Serial 91 simply disappears; the gap stays. The
  benchmark's precedence rule depends on serials, so rewriting them would
  corrupt the very signal the model is told to use.
- **No reformatting.** Every other byte is identical.
- **Same page, same number of memory blocks.** Only content inside a block
  changes.
- **Fewer tokens, never more.** Measured at −0.31% to −3.48%.
- **Any irregularity → fall back to the original page, and count it.** A silent
  fallback would look exactly like a null result, so the counter is a hard
  failure condition, not a warning.
- **H-Nav never changes what is retrieved.** It only edits what is inside the
  page that was already retrieved.

### 6.4 Closing the gap from oracle to a real detector

A shippable policy may use **only** detector output — no correct answers. We
measured the cost of that substitution:

| | detector achieved | oracle ceiling | ratio |
|---|---|---|---|
| sh_6k | +61 | +62 | **0.984** |
| sh_32k | +44 | +46 | **0.957** |

Across 1,000 graded calls, replacing the correct answers with the detector cost
**two flips**. The operating point was frozen on **detection quality alone** —
no LLM, no correct answers, no accuracy figure — *before* any experimental arm
was graded, and the commit timestamps prove the ordering.

*Sources for §6: `STAGE1_NULL_ANALIZI.md`, `hnav/stage1/stale_suppression_probe.py`,
`hnav/stage1/detector_gap.py`, `stage0_results/stage1_operating_point.json`.*

---

## 7. The experimental protocol — why the number is believable

This is worth explaining to a supervisor in its own right, because it is what
separates this from "we tried something and it went up."

### 7.1 Split discipline

```
sh_6k + sh_32k  →  CALIBRATION.  Every threshold, every operating point, every
                   design choice was fitted here and nowhere else.
sh_64k          →  HELD OUT.  Touched exactly once, for the final test.
sh_262k         →  HELD OUT.  Never used at all.
```

Every script **refuses** a held-out subset by default. The final run required an
explicit flag that itself refuses any configuration other than the registered
one.

### 7.2 Pre-registration

Before the final run, a document was committed specifying: the exact claim, the
arms, the number of questions, the analysis code, the success criterion
(**net ≥ +10 discordant pairs, exact p < 0.01, token cost ≤ 0**), the harm
criterion, **eight void conditions** that would invalidate the run, and a
**falsifiable side-prediction** (exactly 2 questions where the correct fact
would be deleted).

Commit timestamps prove registration (19:52:24) preceded the run (22:00:02).
One shot, no optional stopping.

An earlier pre-registration was **formally withdrawn with cause** rather than
quietly amended, and is kept in the repository as evidence.

### 7.3 The four controls

| control | why it exists | result |
|---|---|---|
| **A/A floor** — grade the untouched baseline twice | the server is not deterministic; an effect must clear its noise | **0/0 flips** on every run |
| **`anti` arm** — do the *opposite* of the intervention | if position causes the effect, reversing it must hurt | −1, −6, −2 across three subsets ✓ |
| **stratified reporting** — conflicted vs non-conflicted | the non-conflicted group is natively ~100% with *zero* observed noise, so any drop there is real signal | see §8 |
| **precision audit** — every deleted fact checked against ground truth | deleting a current value would be silent damage | **735/735 correct, 0 errors** |

### 7.4 Adversarial audit

Every deliverable passed through a supervisor process whose job was to **refute**
it — re-deriving numbers with independent implementations, re-verifying deletions
against ground truth, attacking classifiers with independently written
alternatives, and checking commit ordering rather than trusting claims.

Across eleven audits it found **five real defects**: a void condition whose prose
read weaker than its code, a question mis-classification, a cross-context state
leak, an internal contradiction in the void rules, and a latent code path that
could have fitted thresholds on held-out data. **All five were fixed rather than
argued away.**

### 7.5 The structural safeguards in the code itself

These are enforced by automated tests, not by convention:

- **No leakage.** Correct answers may appear only in offline analysis modules.
  An AST scanner fails the build if any online module so much as references
  them — and the scanner is itself tested against three deliberate violations,
  because *a scanner that cannot fail is decoration*.
- **`write_policy.py` may never exist.** A test enforces the Stage-0 NO_GO
  permanently.
- **Raw-score entropy may never reach a decision.** Also enforced by AST scan.
- **Default off.** A stray import can never move a benchmark number.
- **Write-time vs read-time visibility are separate APIs**, so the write path
  physically cannot look at facts it would not yet have seen.

---

## 8. The result

**Held-out `sh_64k`, one pre-registered run, 100 questions × 5 arms, 500 LLM calls:**

| arm | overall | non-conflicted | conflicted | McNemar b/c | net | exact p | tokens |
|---|---|---|---|---|---|---|---|
| baseline | 0.450 | 28/34 | 17/66 (25.8%) | — | — | — | 0 |
| A/A repeat | 0.450 | 28/34 | 17/66 | 0/0 | 0 | 1.0 | 0 |
| **suppression (H-Nav)** | **0.640** | 27/34 | **37/66 (56.1%)** | **0/20** | **+20** | **1.9×10⁻⁶** | **−0.31%** |
| placement (newest last) | 0.480 | 28/34 | 20/66 | 2/5 | +3 | 0.45 | 0 |
| anti (newest first) | 0.430 | 28/34 | 15/66 | 3/1 | −2 | 0.63 | 0 |

- **Conflict accuracy more than doubled** — 25.8% → 56.1%.
- **Zero conflict questions harmed.** The McNemar b-cell is literally 0.
- **Tokens went down**, not up. The intervention is cheaper than the baseline.
- **Detector precision 1.000** — 735 of 735 deleted facts independently verified
  as genuinely superseded.
- **Effect size shrank exactly as predicted, for the predicted reason**
  (+62 → +44 → +20), because at this scale only 10 of 17 chunks are retrieved
  and the detector sees less. That prediction was written two hours before the
  run.

### 8.1 The one failure, stated up front

**The protective criterion was VOIDED by a single question.** On q77 the model
went from answering `John Milton` to *"the knowledge pool does not contain any
information about…"* — **with the correct fact still on the page**. Not a
deletion error. A **refusal induced by the edit**, most likely because the page
now reads as truncated.

Under the deliberately strict registered rule, one such case voids the safety
claim. So the registered conclusion — written before the data existed — stands:

> **Effective, but not yet safe.**

The falsifiable side-prediction was also **missed and reported as missed**: we
predicted 2 correct-fact deletions, observed 1, with 0 accuracy losses. And even
that is a caveat rather than reassurance — on the one real deletion the page was
left containing only the *wrong* value and the model answered correctly anyway
from world knowledge. So "zero loss from correct-fact cuts" is evidence about the
**evaluator**, not evidence that such cuts are safe.

---

## 9. Which part of memory management each method improves

This is the table to put on a slide.

| Method | Which part of memory management | What it improves |
|---|---|---|
| Geometry calibration (cosine, control set, AUC) | **Detection — write & read** | Establishes that near-duplicate geometry can find conflicting memories at all. AUC ≥ 0.9999. |
| Span/QR residual (novelty) | **Detection — write & read** | Separates "one slot restated" from "several similar facts." Stops the detector grouping unrelated things. |
| ABTT whitening | **Detection — representation quality** | Removes uninformative shared directions from embeddings so similarity means something. AUC 0.936 → 0.955. |
| Adaptive threshold `τ_t` | **Write path — online admission** | Compensates for similarity drifting up as the store grows, so a fixed threshold does not silently tighten. |
| Subject-identity screen | **Detection — precision** | Kills the dominant false-positive class. False verification 33–93% → **0.000**. |
| Bidirectional NLI | **Detection — semantic confirmation** | Confirms real disagreement rather than mere similarity; one-way contradiction rejected. |
| Graph grouping (connected components) | **Detection — structure** | Turns pairwise scores into memory "slots" deterministically. |
| **Fact-level stale suppression** | **Read path — context repair** | **The actual improvement: 25.8% → 56.1% conflicted accuracy, p = 1.9×10⁻⁶, tokens −0.31%.** |
| Retriever replica + fidelity gate | **Measurement validity** | Guarantees offline reasoning matches the live retriever. Caught the bf16 precision fault. |
| Headroom measurement | **Scoping** | Killed the write path before it was built (headroom ≈ 0) and correctly flagged the read path. |
| Shadow mode + equivalence testing | **Measurement validity** | Proves the instrument does not disturb the experiment; established the ±3-point noise floor. |
| Pre-registration + split discipline | **Inference validity** | Makes the final number a test rather than a search. |
| Adversarial audit | **Inference validity** | Five real defects found and fixed rather than argued away. |

### The one-line version

> **The improvement is on the READ path, at FACT granularity, by DELETION.**
> Everything else in the project exists either to make that deletion safe
> (detection) or to make the resulting number believable (measurement).

---

## 10. Honest negative results (these belong in the thesis too)

A supervisor will ask what did *not* work. There are four, and each was reported
as negative rather than reframed:

1. **Write-path intervention: NO_GO.** Headroom ≈ 0 in this arena.
   `write_policy.py` is permanently forbidden by a test. *This is the arena's
   answer, not the design's* — in single-hop fact consolidation, retrieval
   already surfaces the newest fact.
2. **Chunk-level reranking: harmful.** 0 of 162 configurations net-positive;
   helped 228, harmed 441.
3. **Marginal-diff hypothesis (H2): failed.** Direction positive
   (ΔAUC +0.0674) but the likelihood-ratio prong failed at p = 0.341.
4. **Secondary arena (Cross-Episode Knowledge): redundancy measured, benefit
   unproven.** Within-context near-duplication is **21.8%** against **0.04%**
   across contexts — a ~545× separation, so the redundancy is real and
   structural. But fact-level critical conflict is **0.0000**, so this substrate
   is about *redundancy*, not *conflict* — a structurally different problem. We
   explicitly refuse to assert that removing redundancy would improve accuracy,
   for three reasons: the direction is unpredictable (this very project produced
   a fix that helped at one scale and harmed at another), the measurement needs
   credentials we do not have, and "redundancy exists" is not "redundancy harms."

An extra piece of self-correction worth mentioning: the secondary arena's
headline was **argued down by its own author** from 86% to 21.8%, because 86%
was a *nearest-neighbour* statistic and, given the pairwise rate and store size,
independence alone predicts 0.944 — *above* the observed value. So the 86%
carried no evidence at all and was removed from the claim.

---

## 11. Methodological findings that stand on their own

Independent of whether H-Nav works, these are publishable observations:

1. **The benchmark's headline metric is dominated by conflict-free questions.**
   Anyone citing `Conflict_Resolution` accuracy is largely measuring something
   else.
2. **The model does not read the serial number as a precedence signal at all.**
   Explicit precedence instructions are ~95% ineffective, and the failure is
   systematic (the stale value, not confusion). When the symbolic recency label
   and text position are put in *conflict*, the model follows **position** on
   93–97% of conflicted questions. See `HNAV_POSITION_VS_RECENCY.md`.
3. **NLI alone cannot verify memory conflicts** — 33–93% false verification;
   a parsed subject screen drives it to 0.000.
4. **Reduced-precision embedding serving silently destroys retrieval fidelity** —
   top-k agreement 1.0000 → 0.24 under bf16.
5. **vLLM at temperature 0 is not run-to-run deterministic** — a 4-point
   accuracy swing between identical runs, with the noise confined entirely to
   the conflicted stratum.
6. **Retrieval-page membership is not reproducible by re-encoding** when chunks
   cluster tightly — 26/100 agreement even with a corrected encoder. You must
   read the index, not rebuild it.
7. **Content-addressed caches must encode every parameter that shapes the
   content.** We hit this three times. In each case a *correction* would have
   been invisible — the cache would have returned the old values and the fix
   would have measured as "no change."
8. **A pooled percentile across non-exchangeable subsets describes neither.**
   Our own frozen entropy threshold (`H_z > 1.9569`) was **arithmetically
   unreachable** on the smallest subset: with only 2 chunks, entropy is bounded
   by log 2 = 0.693 and in fact collapses to the constant 0.36533. Fitted on
   pooled data, it had landed on a different subset's median — making it a
   **store-size detector rather than an ambiguity detector**. This is why that
   screen is switched off in the shipped configuration, and why the codebase
   now requires per-subset reporting.
9. **Intervention granularity must match conflict granularity.** A
   precision-1.000 detector still harmed twice as often as it helped when acting
   on chunks of ~250 facts.

---

## 12. What may and may not be claimed

### May be claimed

> On the held-out `factconsolidation_sh_64k` subset, in a single pre-registered
> confirmatory run (100 questions × 5 arms, 500 calls, frozen substrate,
> benchmark-retrieved top-10 page), fact-level suppression of detector-verified
> superseded facts raised conflicted-stratum accuracy from **17/66 to 37/66** —
> **+20 net discordant pairs, McNemar exact p = 1.9 × 10⁻⁶, zero conflicted
> questions harmed** — against an A/A noise floor of exactly 0/0, at **no token
> cost (−0.31%)**. Suppression precision was **1.000** (735/735 verified). The
> gate was gold-free: the operating point was frozen on detection quality alone
> before any arm was graded. **The pre-registered protective criterion was not
> met** — one non-conflicted question regressed, where the model declined to
> answer although the fact it needed was still on the page. The mechanism is
> therefore **effective but not yet safe**.

### May **not** be claimed

- Not *"H-Nav improves accuracy"* unqualified — the protective claim voided, and
  that belongs in the **same sentence** as the improvement, never a later
  paragraph.
- Not *"effective"* without scope — effective *on the conflicted stratum of this
  arena, at this scale*.
- No oracle-ratio figure at sh_64k — the 98.4%/95.7% numbers are
  calibration-only and cross-harness.
- No forecast from calibration to held-out data; the pre-registration explicitly
  banned it.
- Not *"H-Nav's validated Stage-0 gate improves accuracy"* — the entropy/margin
  precondition is **inert** in the shipped configuration. What carries the
  result is the detector's precision. The precondition layer is *untested*, not
  validated.
- No generalization: one arena, one subset, one scale, one model, one shot.
- Not *"safe at scale"* — `sh_262k` was never tested, and it has the highest
  exposure to the known failure mode.

---

## 13. Limitations

- **Single model, single arena.** Qwen3-4B-Instruct-2507 on one dataset family.
- **The safety failure is understood but unfixed.** "Refusal after edit" has a
  mechanism and a count, not a solution.
- **The shipped configuration disables a Stage-0 component** for a stated reason
  (its inputs were contaminated by an embedding-truncation defect and re-fitting
  in time was impossible), so it fires on every question.
- **Held-out subsets carry pre-fix labels** from before the truncation
  correction, with inputs confirmed identical.
- **`sh_262k` was never tested.**
- **The evaluator can be satisfied by a wrong page** (see §8.1), which bounds
  what any accuracy number on this benchmark proves.
- **Secondary-arena runs are incomplete** — one backend measured; the
  LLM-mediated path is blocked on credentials.

---

## 14. What would come next, in order of value per unit of effort

1. **Eliminate refusal-after-edit.** This is the single thing standing between
   "effective" and "effective and safe." Likely direction: leave a minimal
   marker where a fact was removed, so the page does not read as truncated.
2. **Replicate at sh_64k with N > 1**, so a single malformed generation cannot
   decide the safety criterion.
3. **A second model.** The mechanism is a claim about how models read context;
   one model cannot support it.
4. **`sh_262k`**, declared exploratory, to test whether the effect survives
   where retrieval is most lossy.
5. **The secondary arena's accuracy question** — a token-matched retrieval-level
   A/B test, which needs only a judge model and credentials.

---

## 15. Glossary

| Term | Plain meaning |
|---|---|
| **Embedding** | A list of ~2560 numbers representing a sentence's meaning. |
| **Cosine similarity** | How close two embeddings point in the same direction. 1 = identical meaning, 0 = unrelated. |
| **L2-normalized** | Every vector rescaled to length exactly 1, so cosine similarity is just a dot product. |
| **QR / span residual** | "How much of this fact cannot be rebuilt from the others?" 0 = a restatement, 1 = entirely new. |
| **ABTT whitening** | Removing the few embedding directions shared by nearly all sentences, which carry no information but dominate similarity. |
| **NLI** | Natural Language Inference — a model that judges whether one sentence contradicts, entails or is neutral to another. |
| **AUC** | How well a score separates two groups. 0.5 = useless, 1.0 = perfect. Ours is 0.9999. |
| **McNemar test** | The correct significance test when the *same* questions are graded under two conditions. Counts only the questions that flipped. |
| **Discordant pairs (b/c)** | b = helped→harmed, c = harmed→helped. Our run: b = 0, c = 20. |
| **A/A test** | Run the *same* condition twice. Any difference is pure noise. Ours: 0/0. |
| **Held-out / calibration split** | Data you may tune on vs data you may only test on, once. |
| **Pre-registration** | Committing the analysis plan and success criterion *before* seeing the data, so the result is a test rather than a search. |
| **Precision (of the detector)** | Of the facts we deleted, what fraction genuinely were superseded? Ours: 1.000. |
| **Shadow mode** | Run all the detection code but change nothing, to prove the instrument does not disturb the experiment. |
| **Headroom** | The maximum number of answers an intervention *could* fix. If it is zero, do not build the intervention. |

---

## 16. Where the evidence lives

| Document | Contents |
|---|---|
| `HNAV_FINAL_REPORT.md` | The full program report — the definitive account. |
| `HNAV_HOW_IT_WORKS.md` | Step-by-step mechanism, including the mathematics in §11. |
| `HNAV_POSITION_VS_RECENCY.md` | Does the model track recency or position? The position-swap re-analysis, and what is still untraced. |
| `TEZ_BULGULARI.md` | Evidence ledger (Turkish) — every claim with its artifact. |
| `STAGE0_REPORT.md` | Machine-generated measurement report; every number read off disk. |
| `KAPI_KARARI.md` | The Stage-0 gate decision (Turkish; partly superseded, kept as a record). |
| `STAGE1_NULL_ANALIZI.md` | The chunk-reranking investigation that turned a null into a finding. |
| `stage0_results/final/*.json` | Raw measurement files for M0–M4. |
| `stage0_results/stage1/*.json` | Oracle probe, detector gap, confirmatory run. |
| `stage0_results/stage1_preregistration*.md` | The pre-registrations, including the withdrawn one. |
| `hnav/core/geometry.py`, `read_gate.py`, `read_policy.py` | The detector and the intervention. |
| `hnav/tests/` (~253 tests) | Every numeric quantity checked against a closed-form or independently computed answer. |
