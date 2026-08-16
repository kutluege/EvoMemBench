# How H-Nav Works — A Step-by-Step Guide

*Version: 2026-08-16. Describes the system as it exists after the Stage-1
confirmatory run. Every number cited here is traceable to a committed artifact;
see `TEZ_BULGULARI.md` for the evidence ledger.*

---

## 1. The problem in one paragraph

An LLM agent with memory accumulates facts over time. Some of those facts
**supersede** earlier ones — a person changes jobs, a value is corrected, a
record is updated. When the agent is later asked a question, the retrieval
system hands it a page of remembered text that may contain **both the old and
the new version**. The question this project asks is simple:

> Does the model reliably use the newer fact? And if not, can a governance layer
> fix that without breaking anything else?

The answer we measured is: **no, it does not** — and **yes, a very specific kind
of intervention fixes most of it.**

---

## 2. The benchmark: what it is and what it actually tests

### 2.1 Where we measure

We measure inside **MemoryAgentBench**, a benchmark suite that evaluates agent
memory across four quadrants (in-episode vs cross-episode × knowledge vs
execution). We use one quadrant and one dataset:

```
EvoMemBench/
└── In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/
    └── dataset: Conflict_Resolution
        └── subsets: factconsolidation_sh_6k
                     factconsolidation_sh_32k     ← our tuning ("calibration") data
                     factconsolidation_sh_64k     ← held out for the final test
                     factconsolidation_sh_262k    ← held out, not used
```

`sh` means *single-hop*: each question maps to exactly one fact. (There are also
`mh` multi-hop subsets; we excluded them because the question→fact mapping is
not 1:1, which makes ground truth ambiguous.)

The four subsets are the **same task at four store sizes**:

| subset | facts in the store | chunks | questions |
|---|---|---|---|
| sh_6k | 455 | 2 | 100 |
| sh_32k | 2,310 | 9 | 100 |
| sh_64k | 4,580 | 17 | 100 |
| sh_262k | 18,332 | 67 | 100 |

### 2.2 What one task looks like

Each subset gives the model a **numbered list of facts** as its memory:

```
0. Thomas Kyd was born in the city of London.
1. The chairperson of Fatah is Mahmoud Abbas.
2. Amy Winehouse died in the city of Camden Town.
...
91. Nobuhiro Watsuki is famous for Rurouni Kenshin.
...
259. Nobuhiro Watsuki is famous for The Fairly OddParents.
...
454. ...
```

The rule the benchmark encodes is: **a higher serial number means a newer
fact**. When two facts share the same subject and relation but give different
values, the higher serial wins.

So in the example above, facts 91 and 259 are about the same subject
(`Nobuhiro Watsuki`) and the same relation (`is famous for`), but disagree.
Fact 259 is newer, so it is the truth *for this benchmark*.

### 2.3 A worked question

> **Question:** Based on the provided Knowledge Pool, what is Nobuhiro Watsuki
> famous for?
>
> **Gold answer:** `The Fairly OddParents`   ← fact 259, the newer one
>
> **What the base model answers:** `Rurouni Kenshin`   ← fact 91, the *stale* one

Notice what makes this hard and interesting: `Rurouni Kenshin` is the
**real-world truth**. The benchmark deliberately injects counterfactual updates,
so a model that leans on world knowledge instead of reading the context will
answer the *old* fact. This is by design — it is how the benchmark separates
"the model read the memory" from "the model already knew."

### 2.4 Two kinds of question — and why the distinction matters enormously

Not every question involves a conflict. We classified all 400 questions:

| subset | questions on a **non-conflicted** key | questions on a **conflicted** key |
|---|---|---|
| sh_6k | 26 | 74 |
| sh_32k | 35 | 65 |
| sh_64k | 34 | 66 |
| sh_262k | 22 | 76 (+2 unmatched) |

This split turned out to be the single most important measurement in the whole
project:

| | non-conflicted questions | conflicted questions |
|---|---|---|
| model's accuracy (sh_6k, 8 independent runs) | **26/26 — every run** | **0–5 / 74** |

The model answers *perfectly* when there is no conflict, and **almost never**
answers correctly when there is one. And of ~575 conflicted-question errors
across those runs, **572 were the stale value of the correct key** — not a
refusal, not a hallucination, not an unrelated fact. The model finds the right
memory slot and reads the wrong version out of it.

**Consequence:** the benchmark's headline accuracy (0.29–0.45) is carried almost
entirely by the questions that contain no conflict. On the questions the
benchmark exists to test, base accuracy is roughly 5–26%.

### 2.5 How the benchmark scores an answer

The evaluator is `substring_exact_match`: the gold string must appear in the
model's output. It is deterministic, offline and free — no LLM judge, no
subjective grading. The model is capped at **10 output tokens**, so answers are
short phrases like `The Fairly OddParents`.

---

## 3. What goes into the model, and what comes out

### 3.1 The prompt, anatomically

Every question produces one prompt with three parts:

```
┌── SYSTEM MESSAGE ─────────────────────────────────────────────┐
│ (the benchmark's standard system prompt)                      │
└───────────────────────────────────────────────────────────────┘
┌── MEMORY BLOCKS ──────────────────────────────────────────────┐
│ Memory 1:                                                     │
│ 0. Thomas Kyd was born in the city of London. 1. The chair... │
│                                                               │
│ Memory 2:                                                     │
│ 228. ... 229. ... (the next chunk of facts)                   │
│  ... up to 10 blocks (top_k = 10) ...                         │
└───────────────────────────────────────────────────────────────┘
┌── QUERY TEMPLATE (verbatim from the benchmark) ───────────────┐
│ "Pretend you are a knowledge management system. Each fact in  │
│  the knowledge pool is provided with a serial number at the   │
│  beginning, and the newer fact has larger serial number.      │
│  You need to solve the conflicts of facts in the knowledge    │
│  pool by finding the newest fact with larger serial number... │
│  ...                                                          │
│  Now Answer the Question: Based on the provided Knowledge     │
│  Pool, {question}                                             │
│  Answer:"                                                     │
└───────────────────────────────────────────────────────────────┘
```

**Read that query template again.** The benchmark *explicitly tells the model
the rule*: higher serial = newer, resolve conflicts by taking the newest. And
the model still fails 95% of conflicted questions. That is not a prompt-design
oversight; it is a genuine limitation of the model's ability to follow an
explicit precedence rule inside a long context.

**Input size:** ~6,700 tokens at sh_6k, up to ~50,000 at sh_64k.
**Output:** at most 10 tokens, temperature 0.

### 3.2 How memory gets from the store into the prompt

```
455 facts
   │  chunk_text_into_sentences()   ← the benchmark's own chunker
   ▼
2 chunks of ~4,096 tokens each      (sh_64k: 17 chunks; sh_262k: 67)
   │  embed each chunk, build a FAISS index
   ▼
retrieve top-10 chunks by similarity to the question
   │
   ▼
those chunks become "Memory 1 … Memory N" in the prompt
```

At sh_6k and sh_32k there are only 2 and 9 chunks, so **everything is always
retrieved** — retrieval is lossless and the model sees the entire store. At
sh_64k only 10 of 17 chunks fit, so ~41% of the store never reaches the model.
This distinction matters later.

---

## 4. Baseline vs H-Nav, side by side

**Baseline (`HNAV_MODE=off`)** — H-Nav is inert, byte-for-byte:

```
question → retrieve top-10 chunks → build prompt → LLM → answer
```

**With H-Nav (`HNAV_MODE=live`)** — one extra step, between retrieval and the
prompt:

```
question → retrieve top-10 chunks → ★ H-NAV READ GATE ★ → build prompt → LLM → answer
                                    (edits the page)
```

H-Nav **never changes what is retrieved**. It only edits what is inside the
retrieved page before the model sees it.

---

## 5. The H-Nav pipeline, step by step

We follow the Nobuhiro Watsuki example all the way through.

### Step 1 — Explode the page into individual facts

The retrieved chunks are big blobs of ~230–260 facts each. H-Nav parses them
back into individually addressable facts using a validated parser (99.5%+
coverage):

```
chunk "Memory 1"  →  (0,  "Thomas Kyd was born in the city of London.")
                     (1,  "The chairperson of Fatah is Mahmoud Abbas.")
                     ...
                     (91, "Nobuhiro Watsuki is famous for Rurouni Kenshin.")
                     ...
                     (259,"Nobuhiro Watsuki is famous for The Fairly OddParents.")
```

**Why facts and not chunks?** Because we measured chunk-level operation and it
was *actively harmful* — see §6.1.

### Step 2 — Geometric filter: which pairs even look like a conflict?

Every fact is embedded into a vector. Two cheap geometric signals narrow the
field:

**(a) Pair cosine similarity** — how close two facts are in meaning-space.
Conflicting facts are near-identical except for one value, so they sit very
close together:

```
"Nobuhiro Watsuki is famous for Rurouni Kenshin."
"Nobuhiro Watsuki is famous for The Fairly OddParents."
                                        cosine ≈ 0.97   ← candidate ✓

"Nobuhiro Watsuki is famous for Rurouni Kenshin."
"Amy Winehouse died in the city of Camden Town."
                                        cosine ≈ 0.55   ← not a candidate ✗
```

The threshold (0.90) was chosen on calibration data only. For scale: across
the whole benchmark, conflicting pairs have a median similarity of **0.964**
against **0.60** for random pairs, and separate with **AUC ≥ 0.9999**. The
geometric premise is extremely strong here.

**(b) Span residual** — "how much of this fact is *new* relative to the
others?" Formally we take one member out of a group and ask how well it can be
rebuilt from the span of the remaining ones. A near-restatement rebuilds almost
perfectly (residual ≈ 0); genuinely new information does not (residual ≈ 1).
This screens out groups that merely look similar.

After this step we have **conflict candidates** — but they are not yet trusted.

### Step 3 — Subject-identity screen: is it really the same thing?

This step exists because of a failure we measured, and it is the single most
transferable finding in the project.

Consider these two facts:

```
"Thomas Kyd was born in the city of London."
"Marlowe was born in the city of London."
```

Same template, same relation, same value — **different people**. These do not
conflict at all. Both can be true.

H-Nav parses each fact into `(relation, subject, value)` and **requires the
relation and subject to match**:

```
(born in the city of, Thomas Kyd, London)
(born in the city of, Marlowe,    London)
        ↑ subjects differ → REJECT, not a conflict
```

Unparseable pairs are **rejected**, not trusted — the conservative direction.

### Step 4 — Bidirectional NLI: does a language model agree they contradict?

Surviving pairs are scored by a natural-language-inference cross-encoder
(`nli-deberta-v3-large`) in **both directions**:

```
premise: "Nobuhiro Watsuki is famous for Rurouni Kenshin."
hypothesis: "Nobuhiro Watsuki is famous for The Fairly OddParents."
        → contradiction 0.99+   ✓

premise and hypothesis swapped
        → contradiction 0.99+   ✓

Both directions agree → VERIFIED CONFLICT
```

If only one direction says contradiction, the pair is rejected. (A one-way
contradiction usually means one statement is more specific than the other, not
that they conflict.)

**Why both the screen and the NLI?** Because either alone is insufficient:

| configuration | false-verification rate |
|---|---|
| bidirectional NLI **alone** | **33–93%** |
| NLI **+ subject-identity screen** | **0.000** (2,673 verified pairs, precision 1.000) |

The Kyd/Marlowe pair scores contradiction at **0.9995 in both directions**.
NLI alone would happily "verify" it. The parsed screen is what makes the
detector safe.

### Step 5 — Identify the newest member

Within each verified group, the fact with the **highest serial number** is the
current one:

```
group: { fact 91  → "Rurouni Kenshin"
         fact 259 → "The Fairly OddParents" }   ← LATEST (higher serial)
```

If the newest member cannot be identified unambiguously (ties, unparseable
serials), H-Nav **does nothing to that group**. It refuses to guess.

### Step 6 — Suppress the stale fact

H-Nav deletes the superseded fact **from the page text**, byte-exactly:

```
BEFORE (what the model would have seen):
  ... 90. ... 91. Nobuhiro Watsuki is famous for Rurouni Kenshin. 92. ...
  ... 258. ... 259. Nobuhiro Watsuki is famous for The Fairly OddParents. 260. ...

AFTER (what the model actually sees):
  ... 90. ... 92. ...
  ... 258. ... 259. Nobuhiro Watsuki is famous for The Fairly OddParents. 260. ...
```

Rules that make this safe:

- **No renumbering.** Serial 91 simply disappears; the gap is left alone. The
  benchmark's precedence rule depends on serials, so rewriting them would
  corrupt the very signal the model is told to use.
- **No reflow, no reformatting.** Every other byte is identical.
- **Same page, same number of blocks.** Only content inside a block changes.
- **Fewer tokens, never more** — measured at −0.31% to −3.48%.
- **Any irregularity → fall back to the original page**, and count it. A silent
  fallback would look like a null result, so the counter is a hard failure
  condition, not a warning.

### Step 7 — The model answers

```
Question: What is Nobuhiro Watsuki famous for?
Page now contains only: 259. Nobuhiro Watsuki is famous for The Fairly OddParents.
Model answers: "The Fairly OddParents"   ✓ correct
```

---

## 6. Why it is built this way — every design choice has a measurement

This is the part that matters most for a thesis: **nothing in the final design
is there by intuition.** Three earlier designs were built, measured, and
discarded.

### 6.1 Why facts, not chunks

Our first read-path design reordered **chunks** — promoting the chunk containing
the newest fact toward the top of the page. We tested 162 different
configurations of it.

| result | |
|---|---|
| configurations with net benefit | **0 of 162** |
| total questions helped | 228 |
| total questions harmed | **441** |

It was not neutral — it was **twice as harmful as helpful**, with a detector
operating at precision 1.000. The reason is granularity: **a chunk carries
~230–260 facts.** Moving one chunk to fix a single conflict scrambles the
relative order of hundreds of unrelated facts. The effective signal-to-noise
ratio is about 1:250.

### 6.2 Why deletion, not reordering

Once we operated at fact level, we tested three interventions against each
other on calibration data (an "oracle" version, using gold answers to identify
the target — measuring the **ceiling**, not a shippable system):

| intervention | conflicted accuracy sh_6k | sh_32k |
|---|---|---|
| do nothing (baseline) | 4/74 (5.4%) | 7/65 (10.8%) |
| **delete the stale fact** | **66/74 (89.2%)** | **53/65 (81.5%)** |
| move the newest fact to the **end** | 20/74 (27.0%) | 33/65 (50.8%) |
| move the newest fact to the **front** | 1/74 (1.4%) | 4/65 (6.2%) |

Three things fall out of this table:

1. **Deletion is dramatically effective** — the failure is *repairable*.
2. **Position matters, and the model anchors on late-appearing text.** Moving
   the newest fact to the end helps *without deleting anything*. Moving it to
   the front hurts.
3. **This retroactively explains §6.1's failure.** The chunk design promoted the
   newest fact *upward* — i.e. away from the position that helps.

### 6.3 What is switched off, and why we say so

The operating point disables H-Nav's original "ambiguity precondition"
(entropy/margin screens from Stage 0). Two honest reasons:

- Those screens are the **only** inputs contaminated by an embedding-truncation
  defect we found and fixed (see §7.3), and re-fitting them was not possible in
  time for the confirmatory run.
- Keeping them collapsed the detector's recall from 0.957 to 0.403.

**The consequence must be stated plainly:** with the screen off, H-Nav evaluates
*every* question (though it only acts on verified conflicts). So the shipped
system is **"a fact-level conflict detector applied unconditionally"**, not
"H-Nav's validated Stage-0 gate." What carries the result is the detector's
precision, not the gate.

---

## 7. How performance is measured — the experimental protocol

### 7.1 The split discipline

```
sh_6k  + sh_32k   →  CALIBRATION.  All tuning happens here. Thresholds,
                     operating points, design choices.
sh_64k            →  HELD OUT.  Touched exactly once, for the final test.
sh_262k           →  HELD OUT.  Not used at all.
```

Every script refuses held-out subsets by default; the confirmatory run required
an explicit flag that itself refuses any configuration other than the
pre-registered one.

### 7.2 Pre-registration

Before the final run, we committed a document specifying:

- the exact claim being tested,
- the arms, the number of questions, the analysis code,
- the success criterion (**net ≥ +10 discordant pairs, exact p < 0.01, token
  cost ≤ 0**),
- the harm criterion and what would void it,
- a **falsifiable side-prediction** (exactly 2 questions where the gold fact
  would be deleted, derived from the parse with no model involved),
- and eight "void conditions" that would invalidate the run.

Commit timestamps prove the pre-registration (19:52:24) preceded the run
(22:00:02). No optional stopping; one shot.

### 7.3 Controls that make the numbers trustworthy

| control | why it exists | result |
|---|---|---|
| **A/A floor** — grade the untouched baseline twice | the server is not perfectly deterministic; effects must clear its noise | **0/0 discordant** on every run |
| **`anti` arm** — do the *opposite* of the intervention | if position causes the effect, the reverse must hurt | −1, −6, −2 across three subsets |
| **stratified reporting** — conflicted vs non-conflicted | the non-conflicted stratum is natively ~100% with *zero* observed noise, so any drop there is signal | see §8 |
| **precision audit** — every deleted fact checked against ground truth | deleting a current value would be silent damage | **735/735 correct, 0 errors** |

A measured detail worth knowing: identical baseline runs of this benchmark
differ on ~3.3% of questions (a 4-point accuracy swing), and that noise is
confined **entirely** to the conflicted stratum. Any single-run claim smaller
than that band is not interpretable.

---

## 8. The result

**Held-out sh_64k, single pre-registered run, 100 questions × 5 arms:**

| arm | overall | non-conflicted | conflicted | vs baseline |
|---|---|---|---|---|
| baseline | 0.450 | 28/34 | 17/66 (25.8%) | — |
| baseline repeated (A/A) | 0.450 | 28/34 | 17/66 | 0/0 discordant |
| **H-Nav suppression** | **0.640** | 27/34 | **37/66 (56.1%)** | **+20, p = 1.9×10⁻⁶** |
| placement (newest last) | 0.480 | 28/34 | 20/66 | +3, n.s. |
| anti (newest first) | 0.430 | 28/34 | 15/66 | −2, n.s. |

- **Accuracy up:** conflicted-stratum accuracy more than doubled.
- **Tokens down:** −0.31%. The intervention is *cheaper* than the baseline.
- **Zero conflicted questions harmed** — the McNemar b-cell is literally 0.
- **One non-conflicted question regressed**, which voids the pre-registered
  safety criterion (see §9).
- **Detector recovered 96–98% of the oracle ceiling** on calibration — i.e.
  running without gold answers costs almost nothing.

---

## 9. What H-Nav does *not* do

Being precise about the boundaries is what makes the rest credible.

- **It does not govern writes.** We measured write-side intervention headroom in
  this arena and it was ~0 (0.00 could-change-correctness on held-out data).
  `write_policy.py` is permanently forbidden by a test.
- **It is not proven safe.** On the held-out run, one non-conflicted question
  regressed: the model *refused to answer* after the edit, even though the fact
  it needed was still on the page. That failure mode ("refusal after edit") is
  understood as a mechanism but not eliminated. The registered conclusion is
  therefore: **effective, but not yet safe** — not recommended for deployment on
  traffic containing non-conflicted queries until that is fixed.
- **It does not generalize (yet).** One benchmark, one model (Qwen3-4B-Instruct),
  one scale, one shot.
- **It does not archive or canonicalize.** Those parts of the original design had
  no substrate to be measured against in this repository.
- **It does not fix a store the retriever cannot reach.** At sh_64k, 41% of the
  store never enters the page; H-Nav only edits what was retrieved.

---

## 10. One-page summary

| | |
|---|---|
| **Where** | MemoryAgentBench → `Conflict_Resolution` → `factconsolidation_sh_*` |
| **What the benchmark tests** | can the model use the *newest* of two conflicting memories, when told the rule explicitly |
| **Model input** | system message + up to 10 retrieved memory blocks + templated question (~6.7k–50k tokens) |
| **Model output** | ≤10 tokens, scored by exact substring match |
| **The failure** | the model answers the **stale** value on ~95% of conflicted questions |
| **H-Nav's action** | detect superseded facts in the retrieved page and delete them — nothing else |
| **How it detects** | fact-level: cosine + span residual → parsed subject-identity screen → bidirectional NLI |
| **Detector precision** | 1.000 (735/735 deletions correct on held-out data) |
| **Result** | conflicted accuracy 25.8% → 56.1% held out, p = 1.9×10⁻⁶, tokens −0.31% |
| **Caveat** | one non-conflicted regression voids the safety criterion: *effective but not yet safe* |
