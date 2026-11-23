# Seven-week plan, revised 23 November 2026

Target: submit to *Natural Language Processing* (Cambridge) on **Thursday 14 January 2027**.

This replaces the plan of 21 November. It keeps that plan's experiments, gates and writing
track, moves every date one week later, and reshapes the claims after the label work of
22–23 November (`YAPILANLAR.md`). Tasks marked **New** or **Changed** differ from the 21 November
plan. Who does a task: **E** = Ege, **Ş** = co-author, **C** = a Claude session in this
repository, **GPU** = a run on the GPU machine.

Trust labels are those of the readiness report: **[J]** journal rule, **[S n/8]** seen in n of 8
sampled papers, **[I]** inference.

## 1. What the paper claims

Decided with the author on 23 November. Each claim lists what already supports it and what is
still missing; a claim is written in the paper only as far as its evidence goes.

| # | Claim | In hand | Missing | Weeks |
|---|---|---|---|---|
| C1 | **Problem.** When a vector memory holds several versions of a fact, small models read out the superseded value. | Measured: 94 per cent of wrong answers on conflicted questions contain a superseded value. | Whether it survives fictitious entities and a short page. | 2 |
| C2 | **Method and cost.** Version pairs can be found from embedding geometry alone, without a schema, a parser or a generative call, faster and cheaper than with language models. | Pair-level AUROC 0.972 against 0.893 for cosine. Cost of two LLM readers of the same pairs: GPT-5 mini US$19.49 for 54,569 pairs; Claude Fable 5.2 about 10 million tokens. | (a) Pair-level table: geometry, NLI, GPT-5 mini and Fable against human labels, with cost per 1,000 pairs. (b) End to end: a generative extract-then-keep-newest filter against the method, with accuracy, latency and calls. (c) Latency and memory of the filter. | 3–4 |
| C3 | **Effect.** With the filter, a small model answers conflicted questions about as well as a much larger one. | Measured: filtered Qwen3-4B is at or above unfiltered Qwen3.5-9B on all three stores (77 against 39, 77 against 61, 56 against 51). | (a) A large hosted model run in the same harness, unfiltered and filtered (Section 4, Week 2, for which model). (b) The same on the fact-disjoint test set. (c) The simple baselines. | 2–3 |
| C4 | **Scope.** The method detects supersession under a one-value-per-slot convention, not logical contradiction. | Decision of 23 November on `strict_conflict`; preliminary NLI measurement. | The share of update conflicts that are strict conflicts; the NLI measurement with the paper's own model. | 0–1 |
| C5 | **Resource.** Two additions to the FactConsolidation task of MemoryAgentBench: (a) 54,569 fact pairs with two label layers, read by two language models and checked by two human annotators; (b) a fact-disjoint test set of free-text records. | All pairs labelled by GPT-5 mini, by a rule-based parser and by Claude Fable 5.2. One annotator has labelled every pair on which they disagree: 57 pair ids, 40 sentence pairs. | The second annotator; a sample of pairs on which the sources agree; kappa. The test set itself. | 1–4 |

Rules that keep the claims honest:

- **"About as well as a large model" is a measured statement.** The protocol fixes the report
  before the run: accuracy of filtered Qwen3-4B and of the unfiltered and filtered hosted model on
  conflicted questions, the share of the gap between unfiltered Qwen3-4B and the unfiltered hosted model
  that the filter closes, and cost per question. The word "comparable" is used only if the
  filtered small model is within five points of the unfiltered large one; otherwise the paper
  gives the share of the gap closed. *The five-point margin is my proposal [I]; the authors fix
  it at registration.*
- **The hosted model is described as what it is:** a commercial model whose parameter count is
  not published, reached through Claude Code, run at a stated reasoning effort while the small
  models run with thinking disabled. Haiku 5.5 is the smallest tier of its family and is not
  called a large model; Sonnet 5.5, if used, is "a large hosted model", not "a frontier model".
  These facts go in the text and the limitations.
- **"Checked by two humans and two models" is written out in full:** every pair labelled by two
  language models and a parser; every sentence pair on which they disagree and a stratified
  sample of those on which they agree labelled independently by two annotators, who are the
  authors. Fable 5.2 was calibrated on one annotator's pilot labels, so its agreement with that
  annotator is not independent evidence; its agreement with the second annotator is.
- **No NLI score is shown to any annotator, human or model.** The method verifies with an NLI
  model, so the labels must stay independent of one.
- **The 21 November outcome table still applies.** If the full method does not transfer to the
  fact-disjoint set, the lead claim falls back as that table says, and C2, C4 and C5 carry more
  of the paper.

Not claimed: generality to real agent memory (stated as a hypothesis); safe use in stores with
multi-valued relations; that NLI verifies conflicts; that all pairs are human-labelled; anything
about languages other than English.

## 2. What changed since the 21 November plan

1. **Dates move one week.** Week 1 is 26 November – 2 December; submission is 14 January. The
   three days before Week 1 are used for work that needs no registration (Week 0).
2. **Label validation is redesigned around what the label work found.** The sample is no longer
   500 pairs drawn by tier. It is the 40 sentence pairs on which the label sources disagree, 110
   on which they agree and 50 from the new test set: about 200, labelled by both authors. The
   110 agreement pairs are the part that tests the bulk of the dataset.
3. **The annotators are the authors.** The 21 November plan asked for non-authors. The paper
   states this openly. An outside annotator can be added at revision if a reviewer asks.
4. **The rubric is rewritten before the second annotator starts.** The first rubric was
   ambiguous in ways that produced the disputed tiers (Week 0).
5. **A large-model reference run is added,** because C3 now rests on it. It goes through the
   author's Claude Code subscription, not the API (Week 1 and Week 2).
6. **The generative comparator and the cost analysis move from "should" to "never cut",** and the
   comparator moves one week earlier, because C2 rests on them.
7. **A pair-level comparison with language-model readers is added.** It uses data that already
   exist and costs about a day.
8. **The model-scale section stays in the main text.** The 21 November budget moved it to the
   supplement; it is now the home of C3 (Section 5).
9. **Two small tasks close C4:** the `strict_conflict` pass and the NLI measurement.
10. **Done since 21 November:** open-access funding has been asked about; the co-author has seen
    the protocol draft; a 60-pair pilot, a model annotator pass over all pairs and a review of
    all disagreements are finished.

## 3. Timeline

| Week | Dates | Focus | Milestone | Gate |
|---|---|---|---|---|
| 0 | 23–25 Nov | Rubric, protocol text, journal questions | Protocol ready to register; rubric v2; `strict_conflict` reference labels | — |
| 1 | 26 Nov – 2 Dec | Registration and data | Protocol registered; test and calibration sets built; validation sample drawn | Registration precedes data generation |
| 2 | 3–9 Dec | Phenomenon checks, transfer, large-model reference | Native checks; transfer under three conditions; hosted-model runs; annotation under way | **Framing decision with co-author: 9 Dec** |
| 3 | 10–16 Dec | Baselines, robustness, comparator built | Baseline table; pair-level reader table; annotation complete and frozen | First tables in the manuscript |
| 4 | 17–23 Dec | Cost, labels, generative comparator | Latency table; agreement report; comparator results | Existing text cut to about 11,100 words |
| 5 | 24–30 Dec | Verification and data release | Verified tables; data card; claims memo | **Experimental freeze: 30 Dec** |
| 6 | 31 Dec – 6 Jan | Rewrite | Full draft inside the budget | **Draft to co-author: 4 Jan** |
| 7 | 7–13 Jan | Reproducibility and submission | Complete package | **Go/no-go: 11 Jan; submit: 14 Jan** |

Two tracks run beside the experiments, as before: writing (about one day a week from Week 2) and
annotation (Weeks 1–3).

## 4. Week by week

### Week 0 (23–25 November): what can be done before registration

- [x] **E** Fill the `strict_conflict` reference sheet (received 23 November, 103 sentence pairs).
- [ ] **E** Two answers the sheet cannot be used without (`YAPILANLAR.md`, 23 November):
  - ~~how the sheet was filled~~ answered 23 November: rows S012–S102 were filled by a model,
    so only the first 12 rows are the annotator's own. Those 91 rows are not a human reference;
  - which rule stands. The sheet follows a relation-only table and says "no" on the two pairs
    that prompted the decision of 23 November (US and ancient Rome citizenship; Lu and New York
    City). Either the table is the rule, or the decision is.
  - **Due before rubric v2 goes to the second annotator (26 November).** If it is still open
    then, rubric v2 goes out with the other five fields, and `strict_conflict` is labelled
    later by both annotators on a separate one-question sheet; nothing else waits for it. The
    last point at which it can be settled without moving a gate is the label report of Week 4.
- [ ] **C**, after those answers:
  - *if the table is the rule:* derive `strict_conflict` from it for all update conflicts. No
    model pass is needed; 360 pair ids (222 sentence pairs) change from yes to no;
  - *if the decision stands:* E re-decides 7 rows that contradict it and 3 borderline ones,
    settles six relations (headquarters, married, continent, broadcaster, director, original
    language), and labels 20–30 added pairs chosen to contain mutually exclusive values. Then
    one Fable 5.2 pass over about 708 sentence pairs (up to 897), batched by relation, in which
    each worker records the period of each value as evidence, with a held-out set that contains
    such pairs. Nothing else is relabelled.
- [ ] **New, 23 November. E, Ş** Read and approve the annotation protocol
      (`paper/PROTOCOL_ANNOTATION.md`, draft v0.1): stages 1–4 are recorded as done, stages 0, 5
      and 6 are fixed before they start. It is registered together with the generalisation
      protocol on 26 November.
- [ ] **New. E, Ş** Fill the decision table of stage 0 (about 45 decisions); it replaces the
      `strict_conflict` reference sheet.
- [ ] **New. C, then E and Ş approve.** Rubric v2 for the two-annotator validation. It settles the
      points the first rubric left open:
  - `values_incompatible` is about the slot: two different values are incompatible even when
    both could hold in the world; aliases and containment are compatible. (The first rubric said
    "values that can coexist are compatible", which is how GPT-5 mini produced the 282 disputed
    pairs.)
  - `context_overlap` is "no" only when the sentences state excluding qualifiers.
  - `same_referent` follows the subject as written; a historical state and its modern successor
    are different.
  - `same_relation` for office titles: which templates count as one relation.
  - containment: a short list of what counts as "a kind of" or "part of".
  - `strict_conflict`: the two sentences cannot both be true of the entity at the same time.
- [ ] **E, Ş** Final protocol text. Add to the draft (`paper/PROTOCOL_GENERALISATION.md`):
  - the full baseline list, with raw cosine + recency and the serial-sorted page;
  - the generative comparator, the cost measurement and the second encoder (text ready in
    `WEEKLY_PLAN_NOTES.md` §2.2), with `[MODEL]`, `[ENCODER]` and `[HARDWARE]` filled in;
  - **New:** the large-model reference run and its reporting rule (Section 1);
  - **New:** the pair-level reader comparison, as a secondary analysis with no success claim;
  - **Changed:** the label-validation design of Section 2, item 2, including what counts as a
    label correction;
  - the phenomenon threshold and the rules for reading negative results.
- [ ] **E** Email the editorial office (NLP@cambridge.org): does the word guideline count
      tables, captions, references and appendices; is about 11,500 words plus a supplement
      acceptable; does the form ask for suggested reviewers; usual time to first decision.
- [ ] **E** Fix the main-text budget and tag each planned table as main or supplement (Section 5).
- [ ] **E, Ş** Two decisions that block nothing yet but should not wait: the method's name
      without the project label, and whether the local commits are pushed (the repository is
      public, so a push publishes the manuscript source and these plans).

Deliverables: protocol ready to register; rubric v2; `strict_conflict` labels; journal email sent.

### Week 1 (26 November – 2 December): registration and data

- [ ] **E, Ş** Register the protocol on the first day, before any record is generated: OSF, or
      a public commit whose hash is posted somewhere dated.
- [ ] **C, E** Build the test set: about 400 questions, 300 conflicted and 100 unique;
      fictitious entities, paraphrased free-text records, seen and unseen relations, look-alike
      negatives, labels fixed at construction.
- [ ] **C, E** Build the calibration split: entities disjoint from the test set, none of its
      unseen relations, large enough to refit the probe and thresholds.
- [ ] **C** Record provenance for both: the model that wrote the paraphrases, its version, the
      dates of use, how others can reach it, prompts, seeds, filtering [J].
- [ ] **E** Inspect at least 50 examples by hand; write a short quality-control note.
- [ ] **GPU** Build the record-level index over the 64K store from the existing embeddings.
- [ ] **Changed. C** Draw the validation sample and build its blind sheets, one row per distinct
      sentence pair:
  - 40 pairs on which the label sources disagree (the sheet exists; E has filled it);
  - 110 pairs on which they agree: 40 core version pairs, 40 look-alike negatives nearest the
    0.94 threshold, 15 update-only pairs, 15 quarantined pairs;
  - 50 pairs from the new test set: 25 version pairs and 25 look-alikes.
- [ ] **Ş** Start labelling: the 40 disputed pairs first, with rubric v2 only and without seeing
      E's labels, the pilot examples or any machine label.
- [ ] **New. GPU** Repeat the NLI measurement with the paper's verifier
      (`cross-encoder/nli-deberta-v3-large`) on the 2,135 sentence pairs of the preliminary run:
      contradiction rate on single-valued and multi-valued relations, on containment pairs and
      on look-alike negatives.
- [ ] **New, changed 23 November. C** Write the runner for the hosted model and run a
      ten-question smoke test. The model is reached through the author's Claude Code
      subscription, not the API: one non-interactive `claude -p` call per question from an
      empty directory outside this repository, with the system prompt replaced by the
      benchmark's, tools off, and JSON output for token counts. Same retrieved page, prompt and
      scoring as the local models. The smoke test must show that the reported input tokens
      match the length of our prompt, that is, that nothing else reaches the model. The run is
      **never** done with subagents inside this repository: they receive `CLAUDE.md`, which
      states the benchmark's rule, and they can open the gold answers.
- [ ] **E** Check that the subscription's terms allow an automated evaluation run of this size.
- [ ] **E** Rename and reorganise the repository.

Deliverables: registered protocol; test set and calibration split with provenance and a
quality-control note; record-level index; validation sheets; NLI table; working API adapter.

### Week 2 (3–9 December): phenomenon checks, transfer, large-model reference

Days 1–2, native only
- [ ] **GPU** Native page on the new test set with two answering models: conflicted and unique
      accuracy, and the share of wrong answers that contain a superseded value.
- [ ] **GPU** Native page with record-level top-k retrieval on the 64K store, reference model.
- [ ] **E** Compare both with the protocol's phenomenon threshold.

Days 3–6, transfer
- [ ] **GPU, C** Pair-level evaluation on the new set: raw cosine, ABTT alone, probe alone, the
      full screen; token overlap, common prefix, NER subject match. Seen and unseen relations
      apart; candidate recall at 0.94.
- [ ] **GPU** End to end with two answering models: native, the full method, the method without
      the probe; each under frozen transfer, ABTT re-estimated and recalibrated, in separate
      columns.
- [ ] **C** Count harmful deletions for every plan, with intervals. No threshold is tuned on the
      test set.

**New.** Large-model reference, one to two days
- [ ] **C, E** Run the hosted reference model on the three original stores and the new test
      set, with the unfiltered page and with the filtered page. The deletion plan does not
      depend on the answering model, so the filtered page is the one already built. About 1,400
      calls per model: 600 on the original stores, 800 on the new set. Which model: proposed
      on 23 November, **Claude Sonnet 5.5 as the large model and Claude Haiku 5.5 as a second,
      cheaper reference**, Haiku being the counterpart of the small hosted models whose
      published scores the manuscript cites; the author asked first for Haiku 5.5 and has not
      yet confirmed the proposal. If usage limits bind, the second model runs on the three
      original stores only.
- [ ] **C** Each cell is run three times, because the temperature cannot be set through this
      route; report mean and range.
- [ ] **C** Record for every call: model identifier, Claude Code version, flags, date, input and
      output tokens, latency. A subscription has no price per call, so cost per question is
      computed from the measured tokens and the public list price on the day of the run, and
      the paper says so. The journal wants name, version and dates for any AI tool that
      analyses data [J].
- [ ] **C** Report as fixed in the protocol: the three accuracies on conflicted questions, the
      share of the gap closed, cost per question for the hosted model against the small model
      with the filter.
- [ ] *Optional, first to drop:* one open-weights model of about 30B on the GPU machine, so the
      comparison does not rest on a hosted model alone.

Annotation track
- [ ] **E, Ş** Both label the 110 agreement pairs and the 50 test-set pairs; Ş finishes the 40
      disputed pairs. About two hours each.

Writing track, about one day
- [ ] **E** Statements that need no result: funding, competing interests, ethics, author
      contributions, vLLM version string, model-card access dates, Holm reference, GPT-5 mini
      snapshot and dates.
- [ ] **C** Move the development history to the supplement (about 900 words).

**Decision on 9 December, with the co-author.** The outcome table of the 21 November plan
decides the lead claim. **New:** the same meeting settles the wording of C3 from the hosted-model
result (comparable, or share of the gap closed), the method's name, and the final list of
main-text tables.

Deliverables: phenomenon checks; pair-level and end-to-end tables under three conditions;
harmful-deletion analysis; large-model reference table; a written framing decision.

### Week 3 (10–16 December): baselines, robustness, comparator built

- [ ] **GPU** End-to-end baselines, same questions, stores and scoring: raw cosine + recency;
      cosine + NLI + recency; NLI only + recency; token overlap + recency; NER subject key +
      recency; page sorted by serial; delete + move newest to end. Reference model and one
      non-Qwen model on the 64K store and the new set; the two smaller stores for the reference
      model only.
- [ ] **GPU** No-probe ablation for the other four answering models on the three original stores.
- [ ] **C, GPU** Edge-level NLI grouping fix, labelled post hoc everywhere.
- [ ] **GPU** Repeat every 64K cell three times; report mean and range.
- [ ] **GPU, C** Second encoder at pair level (bge-m3 or multilingual-e5); no end-to-end run.
- [ ] **New. C** Pair-level reader table for C2: for the cosine threshold, the full screen, NLI,
      the rule-based parser, GPT-5 mini and Fable 5.2, agreement with the human labels on
      the validation sample and cost per 1,000 pairs. The parser is shown as the schema-keyed
      reference, not as a competitor.
- [ ] **Changed, moved from Week 4. C** Implement the generative comparator and smoke-test it on
      ten questions.
- [ ] **E** Friday: move finished tables into the manuscript with one draft paragraph each.

Annotation track
- [ ] **E, Ş** Finish. Both label files are frozen before anyone looks at agreement.

Writing track, about one day
- [ ] **C, E** Replace project vocabulary across text, tables and figures.
- [ ] **E** Start the figure fixes that need no result.

Conditional, two days at most, only if everything above is done by 15 December: the Turkish
pair-level check on about 200 hand-translated pairs.

Deliverables: baseline table; no-probe ablation; run-to-run variance; second-encoder
comparison; pair-level reader table; runnable comparator; frozen annotation files.

### Week 4 (17–23 December): cost, labels, generative comparator

- [ ] **GPU** Cost analysis on fixed hardware: embedding latency, NLI latency, filtering time
      per question, GPU memory, number of model calls; one-time preprocessing apart from
      per-question cost; against one generative call of the 4B model. **New:** the same table
      carries the hosted model's cost per question.
- [ ] **Changed. C** Label validation report:
  - Cohen's kappa between the two annotators, field by field;
  - each annotator against GPT-5 mini, Fable 5.2, the parser and the constructed labels of the
    new test set;
  - the two annotators resolve their disagreements by discussion; the result is the human label;
  - the adjudicated label file: the human label where one exists, otherwise the label on which
    the sources agree. The frozen dataset is not overwritten;
  - Table 4 AUROCs recomputed on the adjudicated labels, and how many flips change them (36 of
    the 5,340 evaluation labels differ so far);
  - the share of update conflicts that are strict conflicts.
- [ ] **Changed, moved from Week 5. GPU** Run the generative extract-then-keep-newest comparator:
      same 4B model, stores and questions; native, the method, the strongest non-generative
      baseline, the comparator; accuracy, conflicted accuracy, harmful deletions, latency,
      memory, extra calls. If the week is short, shrink it to the 64K store and the new set.
- [ ] **E** Friday: tables into the manuscript.

Writing track, about one day
- [ ] **C, E** Related Work from five subsections to three (about 1,000 words).
- [ ] **E** Add the citations from this journal; replace preprints with published versions.
- [ ] Gate: the existing text, before new results, is at about 11,100 words.

Optional, only if Week 3 closed on time: LongMemEval feasibility check (two days at most);
record-level retrieval in full.

Deliverables: latency and cost table; agreement report and adjudicated labels; comparator table;
Related Work in three subsections.

### Week 5 (24–30 December): verification, data release, freeze

- [ ] **GPU, C** Finish any comparator cell left from Week 4.
- [ ] **C** Verify: rerun failed cells, check unexpected results, recompute every table from the
      result files, confirm seeds, finalise intervals, reconcile label corrections.
- [ ] **New. C** Assemble the final pair dataset as one table, one row per pair id: the two
      sentences, subset and split, the duplicate-group id, the frozen labels, the GPT-5 mini,
      parser and Fable 5.2 labels, both annotators' labels where they exist, the adjudicated
      `update_conflict`, and the final `strict_conflict` under whichever rule was decided in
      Week 0. A test rebuilds it from the committed inputs and checks the counts.
- [ ] **New. C, E** Prepare the data release:
  - data card: selection frame (cosine at least 0.80, one encoder), the 32,533 unaudited
    candidates, tier definitions, who labelled what, known limits;
  - the 54,529 labelled rows are 47,052 distinct sentence pairs; release with a duplicate-group
    column so that nobody splits train and test across copies of one pair;
  - label files: frozen labels, model labels, human labels, adjudicated labels, rubric v2;
  - licence and citation of the MemoryAgentBench-derived sentences.
- [ ] **E** Count the body against the budget; confirm the main-text figures and tables.
- [ ] **30 December: freeze,** then send the co-author a claims memo: final tables, a draft
      abstract of at most 300 words, the contribution list, the agreed framing, the word count.

After the freeze: no new hypotheses, no new model comparisons, no tuning on the test set, no
post hoc change presented as preregistered.

Deliverables: verified result package; data release folder; claims memo.

### Week 6 (31 December – 6 January): rewrite

- [ ] **E, C** Rewrite abstract, introduction, contributions, results, discussion, limitations
      and conclusion to the 9 December framing and the frozen evidence.
  - Abstract at most 300 words, problem and practical outcome first, about five numbers.
  - The new test set is the headline; the 64K store is "partial overlap with calibration".
  - **New:** the contribution list follows C1–C5.
  - **New:** one paragraph that separates supersession from contradiction and gives the share of
    strict conflicts (C4).
  - **New:** NLI is described by what it was measured to do. If the Week 1 measurement confirms
    the preliminary one, it is a guard against restated values, not a verifier of conflict, and
    the limitation about multi-valued relations is rewritten.
  - **New:** the resource sentence of the abstract says who labelled what; "LLM-adjudicated" goes.
  - The missed preregistered endpoint is stated in Results and in the abstract's last clause.
  - One "Protocol and deviations" paragraph; the rest in the supplement.
- [ ] **E** Narrow the scope claim to stores of atomic fact statements.
- [ ] **E** Explain the English-only choice.
- [ ] **E** Write for readers new to agent memory; define each term at first use.
- [ ] **E, C** Fit the body to about 11,500 words; the supplement must be final [J].
- [ ] **C** House style [J]: three heading levels; "per cent"; sentence-case table headings;
      every table has a source; author–date citations.
- [ ] **E** Figures: larger fonts; "frozen transfer" and "ABTT" labels; no file names; Figure 7A
      cites the right table; 454 against 455 resolved; WCAG 2.1 AA.
- [ ] **4 January: full draft to the co-author.**

Deliverables: rewritten manuscript inside the budget; corrected figures and tables; final supplement.

### Week 7 (7–13 January): reproducibility and submission

- [ ] **Changed. E** AI-use declaration [J], each entry with name, version, dates and access:
  - in the methods: GPT-5 mini (pair labels), Claude Fable 5.2 (pair labels, calibrated on a
    human pilot), the hosted answering model or models, the model that wrote the test-set
    paraphrases;
  - in the acknowledgements: tools used for code and text.
- [ ] **E** Data availability statement with the DOI.
- [ ] **C, E** Release: tagged public repository, persistent DOI, environment specification,
      reproduction instructions, the registered protocol, both datasets with provenance, the
      label files and rubric. Reproduce one central table from a clean clone.
- [ ] **E** Alt text for every figure [J]; cross-check citations and numbering.
- [ ] **E** Author requirements: ORCID linked in ScholarOne; both names and emails on the first
      page; one PDF as "Main Document".
- [ ] **Changed. E** Ethics statement: "Ethical approval was not required." plus one sentence
      that the annotators are the authors.
- [ ] **E** Three or four suggested reviewers, in case the form asks.
- [ ] **E** Confirm the open-access answer before choosing a licence.
- [ ] **E, Ş** Preprint on submission day, or not.
- [ ] **11 January: go/no-go.** Go if the clean-clone reproduction passes and the co-author's
      substantive comments are resolved. Otherwise slip by up to one week; cut nothing from the
      evidence to hold the date.
- [ ] **E** Cover letter and submission on 14 January. Five points: a practical problem; no
      schema, parser or generative call; the evidence, led by the fact-disjoint test and the
      comparison with language models; the released data with its kappa; the limits stated plainly.

## 5. Main-text budget

Target unchanged: body about 11,500 words, abstract at most 300, about 14 figures and tables.
Changes to the 21 November budget, all estimates [I]:

| Item | 21 November | Now | Words |
|---|---|---|---|
| Model-scale comparison (Table 11, Figure 5) | Two sentences; rest to supplement | **Stays in main text**, with the hosted-model rows | +400 kept, +150 new |
| Pair-level reader comparison with cost | — | Merged into the label-agreement table; one paragraph | +150 |
| Supersession against contradiction, strict share | — | One paragraph in the problem setting | +150 |
| Detection inside the retrieved pools | Main text | Supplement; one sentence | −300 |
| "Why identity is decided geometrically", "Read time and write time" | Merged into one subsection | Same, cut harder | −300 |
| Second encoder | About 100 words | One sentence; table in supplement | −50 |
| Generative comparator and cost | About 350 words | Shares one table with the hosted-model cost | −200 |

Net change about zero. The table count stays at nine: the label-agreement table gains the
reader rows and the model table gains the hosted model.

## 6. Cut order if time runs short

Drop in this order:

1. The 262K store experiment.
2. The open-weights 30B reference model.
3. The full LongMemEval run, then its feasibility check.
4. Record-level retrieval in full; the one-day native check in Week 2 stays.
5. The Turkish pair-level check.
6. Repeated 64K runs for three of the five models.
7. The no-probe ablation on the two smaller stores.
8. The second encoder.

Never cut:

- the new-set evaluation under all three conditions, with harmful-deletion counts;
- the phenomenon checks before 9 December;
- the lexical, entity, cosine and NLI baselines end to end;
- the two-annotator validation with kappa;
- **the generative comparator, the cost analysis and the hosted reference run:** C2 and C3
  rest on them;
- the cut to the budget, the mandatory statements, the AI-use declaration and the alt text.

## 7. Risks to the claims

- **The hosted model may be far ahead,** Sonnet 5.5 more likely than Haiku 5.5. Published
  single-hop scores for hosted models on this task range from 60 to 96 per cent in other
  pipelines. If the filtered small model is not within the margin, C3 is written as the share
  of the gap closed and its cost, and the 4B-against-9B result remains.
- **The model labels were not fully blind.** The labelling subagents ran inside this repository
  and very probably had `CLAUDE.md` in context, which describes the dataset's label conventions
  (no pair-level labels). Recorded in `RUN_LOG.json`; stated in the data card.
- **The filter may help the hosted model as well.** That is a finding for the paper, not against it: the
  manuscript already asks whether read-time deletion helps large models.
- **The generative comparator may be more accurate than the method.** Then C2 is cost and
  independence from a generative call, as the protocol text already says.
- **The annotators are the authors.** A reviewer may ask for an independent annotator. The
  mitigation is in the design: rubric v2 only, blind to each other and to every machine label,
  files frozen before agreement is computed.
- **`strict_conflict` needs world knowledge.** Agreement on it may be lower than on the other
  fields. Report it as measured.
- **The NLI measurement so far used another model** (`microsoft/deberta-large-mnli`). Nothing
  about NLI is written until the Week 1 run with the paper's verifier.

## 8. Decisions still open

1. `strict_conflict`: how the reference sheet was filled, and whether the relation table or the
   decision of 23 November is the rule (E; blocks the Week 0 strict task).
2. The hosted reference model: Sonnet 5.5 with Haiku 5.5 as a second point, or Haiku 5.5 alone (E).
3. The five-point margin for "comparable" (E, Ş; at registration).
4. `[MODEL]`, `[ENCODER]`, `[HARDWARE]` in the protocol (E, Ş; at registration).
5. The method's name (9 December).
6. Push and the public state of the repository.
7. Preprint on submission day (Week 7).
