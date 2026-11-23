# Pair-label annotation: protocol

**DRAFT v0.1, 23 Nov 2026, not yet registered.** E. Kutlu, Ş. Özönder. Stages 1–4 were carried
out on 22–23 November, before this text was written; for them this document is a record, not a
plan. Stages 0, 5 and 6 are still to come and are fixed here before they start. To be registered
together with `PROTOCOL_GENERALISATION.md`; later changes are dated amendments.

## 1. Purpose

To give every pair of the conflict dataset (54,569 pair ids, 47,052 distinct sentence pairs) a
label whose origin is known, with human effort spent where it decides something: on the rules, on
a seed sample, on every pair where label sources disagree, and on an independent blind check.
The design is human-seeded, model-scaled and human-audited. The released labels of the dataset
(`gold_update`, `gold_strict`) are never overwritten; the labels produced here are added beside them.

## 2. Labels and instrument

Two outcome labels per pair. `update_conflict`: under one current value per (entity, attribute)
slot, one sentence replaces the other's value. `strict_conflict`: the two sentences cannot both
be true of the entity at the same time. Four component checks (`same_referent`, `same_relation`,
`context_overlap`, `values_incompatible`) explain an `update_conflict` answer.

The instrument is the written rubric. Rubric v1 (22 November) was ambiguous on five points, found
during stages 1–4 and listed in §6. Rubric v2 settles them and is used from stage 5 on.

## 3. Label sources

Every label is stored with its source and no source is ever reported as another.

| Source | What it is |
|---|---|
| parser | Rule-based template parser; same subject and relation, different value |
| GPT-5 mini | One call per pair, six fields; the basis of the released labels |
| Fable 5.2 | Claude Fable 5.2 subagents following the guideline of stage 2 |
| rule table | Authors' decision table applied by code (stage 0) |
| annotator A, annotator B | The two authors, each labelling blind and alone |

## 4. Stages

| # | Stage | Who | Blind to | Gate, fixed beforehand | Status |
|---|---|---|---|---|---|
| 0 | **Rules.** Rubric v2 and a decision table: for each of the 37 relations, whether it holds one value at a time; whether mutually exclusive values of a multi-valued relation count as a strict conflict; what counts as containment. | A and B together | — | Both authors sign the table | To do |
| 1 | **Seed.** 60 pairs labelled on six fields: 50 from the tiers where parser and GPT-5 mini disagree, 10 controls. | A | All machine labels, tier, the key | — | Done 22 Nov |
| 2 | **Calibration.** A guideline is written from 40 seed pairs. One model worker labels the other 20 without seeing their labels. | Fable 5.2 | The 20 held-out labels | Agreement with A at least 0.85 on `update_conflict` and 0.80 on each other field | Passed: 20/20 on five fields, 19/20 on `strict_conflict` |
| 3 | **Scale.** Model workers label every remaining pair in batches of 100, from the guideline alone. Second-pass batches carry 10 hidden repeats of first-pass pairs. | Fable 5.2, 91 workers | Tier, subset, cosine, every other label | Every batch file valid; repeats and duplicate texts reported | Done: 54,509 pair ids (54,529 with the 20 of stage 2) |
| 4 | **Disagreement review.** Every sentence pair on which the model's `update_conflict` differs from the released label is labelled by a human. | A | Which source said what | — | Done 23 Nov: 40 sentence pairs, 57 pair ids |
| 5 | **Independent audit.** Both annotators label the same sample, each alone: the 40 sentence pairs of stage 4, 110 drawn at random by stratum from pairs on which all sources agree, 50 from the new test set. Two questions per pair (`update_conflict`, `strict_conflict`). The page records the seconds spent on each pair. | A and B | Every machine label, each other, the seed examples | Label files frozen before agreement is computed | To do, Weeks 1–3 |
| 6 | **Assembly.** One table, one row per pair id, one column per source. Final `update_conflict`: the human label where stage 4 or 5 gives one (the two annotators settle their differences by discussion), otherwise the label on which the sources agree. Final `strict_conflict`: the rule table, plus a model pass for the pairs the table sends to per-pair judgement, if the table has such a rule. | Code | — | A test rebuilds the table from committed inputs | To do, Week 5 |

Stage 5 reports Cohen's kappa between the annotators, each annotator's agreement with every
machine source, and, for the 110 agreement pairs, the number on which a human contradicts the
agreed label, with an upper bound on that error rate.

## 5. Results so far

- **Seed (stage 1).** On the 50 disputed pairs the annotator sided with the parser on 38 and with
  GPT-5 mini on 12; on the 10 controls with both.
- **Calibration (stage 2).** 20 of 20 on `update_conflict`; 19 of 20 on all six fields.
- **Scale (stage 3).** 54,509 pair ids in about 25 minutes of wall-clock time and about 10
  million tokens. 4,920 of 4,920 hidden repeats received the same six labels; of 7,092 sentence
  pairs labelled more than once under different ids, 7,091 received the same six labels.
- **Disagreement review (stage 4).** The model's label differs from the released one on 57 pair
  ids (40 sentence pairs). The annotator agreed with the model on 56 of the 57. Ten of the 40
  sentence pairs had been in the seed and shown to the model as examples; on the 30 others the
  annotator agreed with the model on 29.

## 6. Deviations and limits, stated as they are

1. **Stages 1–4 were not registered in advance.** The pass mark of stage 2 was committed before
   the held-out run; nothing else was.
2. **Rubric v1 was ambiguous** on: whether "values that can coexist" are compatible; when
   contexts fail to overlap; whether the referent is the subject as written; which office titles
   are one relation; and `strict_conflict`, which it defined in two ways that disagree.
   `strict_conflict` labels made under v1, by anyone, are not used.
3. **One annotator seeded and reviewed.** The model was calibrated on annotator A, so A's
   agreement with it is not independent evidence. Stage 5 supplies that through annotator B.
4. **Both annotators are authors.**
5. **The model workers were blind by instruction.** They ran as general-purpose agents inside
   the repository, could have opened other files, and very probably had the repository's
   `CLAUDE.md` in context, which describes the dataset's label conventions (no pair labels).
6. **A `strict_conflict` reference sheet of 23 November is excluded.** Twelve of its 103 rows
   were labelled by annotator A; the other 91 were filled by a language model at A's request.
   The sheet is kept as received and used for nothing.
7. **Provenance of the two human sheets.** Annotator A states (23 November 2026) that he filled
   the stage 1 sheet (60 pairs) and the stage 4 sheet (40 pairs) himself. Neither sheet carries
   per-item timing, so this rests on his statement; the stage 5 page records it.
8. **No NLI score is shown to any annotator, human or model.** The method under study verifies
   with an NLI model.

## 7. What the paper may say

Once stage 5 is done: one annotator labelled a seed of 60 pairs; a
guideline written from 40 of them was checked on the other 20; a large language model then
labelled the remaining 54,509 pairs under that guideline; every pair on which it differed from
the released label was reviewed by the annotator; a second annotator independently labelled
those pairs and a random sample of pairs on which all sources agree, with kappa reported.

Not to be said: that the dataset is human-labelled; that the model labels are gold; that the
annotators were independent of the authors.

## 8. Files

`hnav/labeling/audit_human_pilot.py`, `audit_model_annotator.py`, `audit_disagreement_review.py`
(code and tests); `.claude/skills/pair-labelling/SKILL.md` (guideline of stage 2);
`stage0_results/conflict_pairs/human_pilot/`, `model_annotation/`, `disagreement_review/`,
`strict_review/` (sheets, keys, labels, summaries, run log); `paper/journal/YAPILANLAR.md` (log).
