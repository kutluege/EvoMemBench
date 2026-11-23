# Preliminary NLI measurement, 23 November 2026

Exploratory, run once on a laptop CPU, **not with the paper's verifier**. It is kept so that the
measurement can be repeated on another machine; nothing in the paper may cite these numbers.

- Model: `microsoft/deberta-large-mnli` (the paper's method uses
  `cross-encoder/nli-deberta-v3-large`, which was not on the machine).
- Rule: a pair counts as "contradiction" when the contradiction probability is at least 0.90 in
  both directions, the threshold the method uses.
- `nli_select_pairs.py <repo> <out_dir>` draws the 2,135 sentence pairs (deterministic; it was
  checked to reproduce the pair list of the original run). `nli_run.py <pkgs_dir> <pairs.json>
  <out.json>` scores them; it needs `torch` and `transformers` and loads the model offline from
  the local Hugging Face cache. Both scripts are as run, without tests.
- **Per-pair scores are deliberately not committed.** The method under study verifies with an
  NLI model, so NLI output must stay away from the label files and from every annotator, human
  or model.

| Group | Sentence pairs | "Contradiction" |
|---|---:|---:|
| Update conflicts by the model labels (same subject, same relation, different value) | 1,692 | 1,684 |
| — relations the first guideline called single-valued | 466 | 464 |
| — relations it called multi-valued | 1,226 | 1,220 |
| Same subject and relation, values the model called compatible (alias, containment) | 26 | 4 |
| Negatives: different subject, same relation | 150 | 106 |
| Negatives: same subject, different relation | 120 | 30 |
| Negatives: subject and relation both differ | 123 | 86 |

Against the first author's own labels on 89 sentence pairs: `strict_conflict` yes, 16 of 16
"contradiction"; `update_conflict` yes but `strict_conflict` no, 35 of 37; `update_conflict` no
with the same subject, 3 of 24; with a different subject, 10 of 12.

What it suggests, to be confirmed with the paper's model (plan item K14, Week 1): the NLI check
follows `update_conflict` and does not separate single-valued from multi-valued relations, and
it calls most template pairs about different subjects contradictions, which matches the thesis
finding that NLI cannot carry identity.
