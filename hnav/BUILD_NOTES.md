# H-Nav Stage 0 — build notes

Local build phase (T2–T8), written on an Intel MacBook Air with no GPU and no
`torch`. Everything here is what a reader needs in order to trust — or distrust —
the code before it runs on the 2× RTX 4090 box.

`pytest hnav/tests/ -q` → **151 passed**, with no torch, no GPU and no network.

---

## 1. What was built

| Task | Files | What it is |
| --- | --- | --- |
| T3 | `hnav/config.py`, `core/{types,embedding,replica,audit}.py` | Core types, the two retriever replicas, the audit log, and the embedder interface |
| T4 | `adapters/{mab_adapter,clbench_adapter}.py`, `labeling/conflict_index.py`, 4 benchmark edits | Shadow-mode instrumentation for both arenas |
| T5 | `core/retrieval_signals.py`, `stage0/m2_retrieval_calibration.py` | Rank/margin/entropy/dH/churn, and the M2 measurement |
| T2 | `stage0/m1b_grouping_ablation.py` | Regex-vs-geometry grouping ablation |
| T6 | `core/{geometry,diff_geometry}.py`, `labeling/{labels,counterfactual}.py`, `stage0/m3_headroom.py` | Geometry signals, the retained labels, counterfactual replay, headroom |
| T7 | `stage0/m4_marginal_diff_test.py` | The H2 nested-model test |
| T8 | `stage0/report.py` | `STAGE0_REPORT.md` and the GO/NO_GO gate |

Not built, deliberately: **`core/write_policy.py` and `core/read_policy.py` do not
exist.** They are live-intervention code and are gated behind the T8 human
decision. `test_no_raw_entropy_in_policy.py::test_stage0_ships_no_policy_modules`
fails if either appears.

---

## 2. Things found while building that change how the remote run behaves

### 2.1 `FACT_RE` alone matches **zero** facts on a real memorize chunk

The brief specifies exploding a chunk with
`FACT_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$", re.M)`. That regex is exact on the
raw `context` string, but the benchmark does not hand H-Nav the raw context. It
hands it the output of `chunk_text_into_sentences`
(`utils/eval_other_utils.py:173`), which ends in

```python
text_chunks.append(" ".join(current_chunk_sentences))
```

Every newline that fell on a sentence boundary becomes a space, so a
line-anchored regex has nothing to anchor to. Measured on the committed `sh_6k`
context: **`FACT_RE` finds 0 of 455 facts** on the joined form.

`explode_facts` therefore tries `FACT_RE` first — it is the prescribed regex and
is exact on raw context — and falls back to `FACT_RE_INLINE`, which runs each
fact to the next serial. On `sh_6k` the two forms give byte-identical results,
455/455. Covered by `test_chunking_and_facts.py`, including an explicit assertion
that the line-anchored form fails, so the fallback can never be quietly deleted
as redundant.

**Without this, every write-side signal on the primary arena would have been
computed from one fact per 4096-token chunk.**

### 2.2 A single arena-wide score convention

`RetrievalView.scores` is always "higher is better". `NumpyCosineReplica` emits
the native `(bank @ q) * 100.0` unchanged. LangChain FAISS returns **squared L2
distance**, so the retriever hook passes `score_kind="l2sq"` and
`to_similarity` converts with `cos = 1 − d²/2`, exact for the L2-normalized
embeddings both shipped embedders produce and strictly decreasing, so ranks are
untouched. One conversion, one place, one test.

### 2.3 The harm criterion implies a minimum sample size

A consequence of the frozen gate, not a choice made here: with **zero** observed
harm, the 95% Wilson upper bound only falls below 0.03 at n ≈ 124. A component
with the minimum 40 positives cannot clear the harm row however clean it is.
Worth knowing before sizing the campaign. Asserted in
`test_report.py::test_the_harm_criterion_implies_a_minimum_sample_size`.

---

## 3. What is tested locally

Every numeric quantity is checked against a **closed-form or independently
computed answer**, not against "it ran".

- **Replica fidelity (M0).** 1,200 sampled `(store, query)` pairs against the
  native two-liner inlined verbatim from `qwen3_embedding_memory.py:218`:
  100% top-1, 100% top-k, 100% full-ranking identity, **zero** score error.
  Plus a deliberate exact-tie fixture, a non-mutation check, and
  fast-path-equals-rebuild for `simulate_insert`.
- **Retrieval signals.** `ln m` for an orthonormal neighbourhood and 0 for a
  collinear one (`H_vn`); uniform scores giving maximum entropy and full tie
  counts; exact churn, displaced-id and rank-shift counts; raw-softmax
  saturation demonstrated on a `cosine × 100` fixture.
- **Geometry.** QR residual 0 inside a span, 1 outside, 0.8 for a known partial
  projection; ABTT refusing below `min_fit_n`, removing an injected dominant
  direction, and being deterministic; the `tau_t` trajectory hand-computed.
- **Labels.** 455 real write contexts from `sh_6k` and 120 read contexts, each
  label compared against an oracle reimplemented independently in the test, plus
  determinism and the `READ_CLEAR` complement property.
- **Counterfactual.** `normalize_answer` pinned to the benchmark's evaluator;
  the five classes exercised with stub models that reproduce specific failure
  modes (latest-wins, first-fact-anchored); prompt-cache accounting.
- **H2 statistics.** Informative *and* null synthetic regimes: a correct
  implementation must show ΔAUC > 0 with tiny LRT p on one and neither on the
  other. Bootstrap, cross-validation and matrix assembly checked separately.
- **Report.** All three NO_GO verdict types produced from inputs that are
  unambiguously each one; unmeasured criteria proved never to render as
  failures; Wilson interval endpoints.
- **Leakage.** The AST scanner is run against three deliberate violations
  (a `["answers"]` subscript, a `["questions"]` subscript, a `counterfactual`
  import) and must flag all three, and against clean prose it must not flag.
  A scanner that cannot fail is decoration.
- **No torch.** Every module under `hnav/` is imported in a fresh subprocess and
  the test fails if `torch`, `transformers`, `faiss`, `openai`, `langchain` or
  `vllm` lands in `sys.modules`; a second test forbids them as top-level imports
  textually.

### Pipelines actually executed end to end, locally

`--smoke-embedder` swaps in `HashEmbedder` and `--stub-llm` swaps in a
deterministic answer stub, so M1b, M2, M3 (counterfactuals included) and M4 have
all been **run to completion on the real dataset** on this laptop. The numbers
are meaningless and are written to separate `*_SMOKE.json` files so they can
never be mistaken for data — but the plumbing, the JSON shapes and the failure
paths are exercised.

---

## 4. What is necessarily untested until it reaches the GPU

Listed plainly, because these are where a first-try failure would come from.

1. **The real embedder.** `HFEmbedder` has never been constructed — no torch
   here. Its pooling mirrors `Qwen3Embedding4BEmbeddings`
   (`embedding_retriever.py:58`) line for line, and its cache layout is
   byte-compatible with T1's, but *loading a model* is untested. **Run T1 first;
   it is the cheapest thing that exercises this path.**
2. **Live-index M0.** `FaissFlatReplica` is verified against squared-L2
   ordering, not against a live LangChain FAISS index. FAISS's internal tie order
   is not reproducible from outside it. Until that check runs, the report prints
   M0 as NOT RUN and treats `rank_self`, `margin`, `dH_*` and `churn` as
   provisional. Producing `m0_replica_fidelity.json` is the first remote job
   after T1.
3. **Run-level shadow neutrality.** The acceptance criterion is byte-identical
   model output between `HNAV_MODE=off` and `shadow` on `sh_6k`/`sh_32k` at
   `temperature=0`. That needs the benchmark, the LLM server and a GPU. What is
   verified here is the *mechanism*: hooks return the caller's own object by
   identity, no store is mutated, the wrapper makes exactly one inner call, and
   all four benchmark edits keep their native branch intact.
4. **The four benchmark files import torch at module level** (they are benchmark
   code, not H-Nav code), so they are checked by `ast.parse` and marker
   assertions rather than by import. They have never been executed.
5. **`local_answer_fn` against vLLM.** The client is constructed lazily and has
   never talked to an endpoint. `--stub-llm` exercises everything downstream of
   it.
6. **The real chunker.** `nltk`/`tiktoken` are absent here, so `build_chunks`
   fell back to line grouping in every local run. The fallback is recorded as
   `"fallback_chunker": true` in every output file — **if that flag is `true` in
   a GPU run, nltk or punkt is missing and the chunking is not the benchmark's.**
7. **Scale.** The largest local run was `sh_6k` (455 facts, 2 chunks). Nothing
   has been run at 18,332 facts. The two places that could bite: the QR basis
   (mitigated by `_QRBasis`, refreshed every 500 admissions rather than rebuilt
   per candidate) and the `sh_262k` bank matrix at ~188 MB in float32.

---

## 5. Deviations from the brief, with reasons

1. **`explode_facts` has a second regex.** §2.1. The prescribed `FACT_RE` is
   tried first and is exact on raw context; on a real chunk it matches nothing.
2. **`hnav/config.py` and `hnav/core/embedding.py` are additions.** The brief
   requires reading config from `.env` and mocking the embedder behind one
   interface; both needed a home, and neither belonged in an existing file.
   `hnav/deploy/.env.template` was referenced by the brief but did not exist, so
   it was written (and un-gitignored, since `.env.*` was matching it).
3. **`diff_novelty` is defined against the store's prior object vocabulary**,
   not as a transform of `diff_sim`. Defining it as `sqrt(1 − diff_sim²)` would
   have made it a deterministic function of a feature already in the model, and
   M4's likelihood-ratio test would then be testing a nonlinearity rather than
   added information.
4. **M4 reports two extra numbers**: a key-clustered bootstrap CI and a
   group-k-fold cross-validated ΔAUC. The protocol's subset-clustered CI is
   still primary and still decides the verdict, but the calibration split has
   **two** subsets, so that bootstrap resamples from two clusters. Reporting only
   it would be reporting a number that cannot mean what it looks like.
5. **`test_leakage_audit` exempts docstrings.** Prose has to be able to state the
   rule. Comments are invisible to the AST anyway. Every other string constant,
   identifier, attribute, keyword and dict key is scanned.
6. **`READ_DISTRACTOR` / `READ_MISSING` use the offline question→key mapping.**
   The protocol marks them online-computable, but that needs a query-side parser
   Stage 0 does not build. Their M3 rates are therefore an **upper bound** on
   what an online detector could reach, and the code and the report both say so.
7. **The QR basis is refreshed every N admissions**, not rebuilt per candidate.
   A 512-column QR per candidate over 18,332 candidates is not a measurement.
   The basis is a random subsample either way, so this is a change of sampling
   frequency, not of estimator; the interval is in every output file.
8. **`AuditLogger` truncates the persisted ranking at 200 entries.** Signals are
   computed on the full pre-truncation ranking; only the stored copy is
   shortened, or an 18,332-entry list would dominate every log record.

---

## 6. Order to run on the GPU box

```bash
cp hnav/deploy/.env.template .env      # then edit
bash hnav/deploy/setup_remote.sh
python hnav/deploy/check_env.py
pytest hnav/tests/ -q                  # must still be green with torch installed

bash hnav/deploy/run_t1.sh             # T1 — the S3 gate. STOP and report.
python hnav/stage0/m1b_grouping_ablation.py       # T2, reuses T1's cache
python hnav/stage0/m2_retrieval_calibration.py    # T5
python hnav/stage0/m3_headroom.py                 # T6, needs the LLM server
python hnav/stage0/m4_marginal_diff_test.py       # T7, calibration split only
python hnav/stage0/report.py --strict             # T8 — HARD STOP
```

`run_t1.sh` exits 2 if the S3 gate fires. **Stop there and report to a human** —
that is the kill switch, and everything after it assumes it passed.
