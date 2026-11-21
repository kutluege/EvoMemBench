# H-Nav-GEO generalisation study: experimental protocol

**DRAFT v0.1, 21 Nov 2026, not yet registered.** E. Kutlu, Ş. Özönder. To be registered before
any new record or question is generated; later changes are dated amendments. Method under test:
artifact `335b4540…`, operating point `9c3cb668…`.

## 1. Questions and hypotheses

| | Question | Hypothesis |
|---|---|---|
| H1 | Does the failure survive fictitious entities and a short page? | Native conflicted accuracy stays below 50 % (§6). |
| H2 | Does recalibrated H-Nav-GEO beat native on conflicted questions? | Yes, in both models (**confirmatory**). |
| H3 | Does it do so without refitting? | C1 and C2 gain less than C3; candidate recall at cosine ≥ 0.94 is below 0.74. |
| H4 | Does the slot probe add to ABTT + NLI? | On seen relations only. |
| H5 | Does it beat the strongest non-generative baseline? | Yes. |

## 2. Data, fixed before generation

- **Test store:** 1,200–1,500 paraphrased free-text records about fictitious entities, one per
  line with a leading serial, two versions per conflicted key. At most nine 4,096-token chunks, so
  the unchanged benchmark pipeline puts the whole store on the page.
- **Questions:** 100 unique and 300 conflicted: 150 on 10 benchmark relations (5 place- or
  category-valued, 5 person-valued; *seen*) and 150 on 10 new single-valued relations (*unseen*).
  Each conflicted key has a same-relation, different-subject look-alike; half share its object.
- **Calibration split:** entities disjoint from the test store, none of its unseen relations, at
  least 1,000 version pairs and 200 questions.
- **Labels** are fixed at construction and stay offline. Generator model, prompts and seeds are
  committed; 50 examples are inspected and both sets hashed before any model reads them.

## 3. Conditions: separate columns, never merged, nothing tuned on the test set

| | Condition | Refitted |
|---|---|---|
| C1 | Frozen transfer | nothing |
| C2 | ABTT re-estimated | mean and 128 directions, on the test store's vectors, without labels |
| C3 | Recalibrated (**confirmatory**) | ABTT statistics, probe, anchors, scales and operating point, on the calibration split, by the existing procedure, grid and selection rule |

## 4. Arms

- **End to end** (deletion arms keep each group's highest serial): native; native repeat (A/A); H-Nav-GEO; ABTT + NLI without the probe; raw
  cosine + NLI; NLI only; token Jaccard; NER subject match; H-Nav-GEO with the newest record
  moved to the end; a construction-key oracle as the ceiling.
- **Pair level:** raw cosine, ABTT cosine, probe, full screen, Jaccard, common prefix, NER subject
  match.
- **Strongest baseline:** each baseline's threshold is fitted on calibration by the method's rule
  (highest pool recall at zero harmful deletions); the best is named before any test output is read.
- **Models:** Qwen3-4B-Instruct-2507 and Phi-4-mini-instruct, served as in the campaign; one
  run per cell; the same questions, store, prompt and substring-exact-match scoring in every arm.

## 5. Primary endpoints

- **P1, accuracy.** Conflicted accuracy (n = 300), H-Nav-GEO under C3 against native: exact
  two-sided McNemar per model, Holm over both, α = 0.05.
- **P2, harm.** Harmful deletions over all deletions in the plan, 95 % Clopper–Pearson interval. A
  deletion is harmful if it leaves a key without its current value on the page. Criterion: upper
  limit at most 5 %.
- **P3, baseline.** H-Nav-GEO under C3 against the strongest baseline, tested as in P1.

Secondary, with exact p-values and no success claim: P1–P3 under C1 and C2; the screen without
the probe; seen and unseen slices; unique-stratum discordant counts; recall after each stage;
pair-level AUROC and TPR at FPR 10⁻³; the superseded-value share of native errors.

## 6. Phenomenon threshold

- **New set:** the failure *survives* if native conflicted accuracy is below 50 % in both models,
  does not if in neither, and is model-dependent otherwise.
- **Record-level page** (reference model; the 50 `sh_64k` facts nearest the query, in rank
  order): the same bar on the conflicted questions whose page holds both versions; fewer than 30
  such questions is inconclusive.
- Losing the failure on the new set points to the parametric prior; on the short page, to page
  length.

## 7. Decisions and negative results

A screen *generalises* under a condition if P1 holds in both models and P2 holds; P1 in one model
only is model-dependent and is treated as the second row.

| Outcome under C3 | Reported as |
|---|---|
| H-Nav-GEO generalises | the method, with C1 and C2 beside it |
| only ABTT + NLI does | the transferable components; the probe as relation-bound |
| neither generalises | a failure-mode and boundary analysis |
| P3 fails | level with the named baseline, or behind it if that baseline is significantly ahead |
| failure does not survive | what drives the failure leads the paper |

Every outcome is reported. A cell is void only for an instrument fault (A/A not zero, a serving
fault, a fingerprint mismatch); it is rerun once and the fault is stated. Harmful deletions do
not void a run, unlike under `GEO_PREREG.md`; they count under P2. Any analysis not listed here, including the edge-level NLI
grouping fix, is labelled post hoc.
