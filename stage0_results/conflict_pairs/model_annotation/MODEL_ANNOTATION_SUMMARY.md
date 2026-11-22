# Model annotator pass — summary

Annotator: claude-fable-5-2, reasoning effort medium, Claude Code subagents (parallel workers). Labels follow a guideline written from the human pilot; no model weights were changed. These are model labels, not human labels.

Pairs labelled: 5417 ({'heldout': 20, 'stage1': 5397}).

## Coverage

| group | batches done | invalid | missing |
|---|---|---|---|
| heldout | 1 | 0 | 0 |
| stage1 | 54 | 0 | 0 |

## Held-out pilot pairs: model vs the human annotator

Pairs the guideline was drafted without. One human annotator; small n.

| field | n | agree | Wilson 95% | Cohen κ |
|---|---|---|---|---|
| same_referent | 20 | 20 | [0.839, 1.000] | 1.000 |
| same_relation | 20 | 20 | [0.839, 1.000] | — |
| context_overlap | 20 | 20 | [0.839, 1.000] | — |
| values_incompatible | 20 | 20 | [0.839, 1.000] | 1.000 |
| update_conflict | 20 | 20 | [0.839, 1.000] | 1.000 |
| strict_conflict | 20 | 19 | [0.764, 0.991] | 0.643 |
| all six fields | 20 | 19 | [0.764, 0.991] | — |

Gate (fixed in advance: update_conflict ≥ 0.85, every other field ≥ 0.8; 20 of 20 held-out pairs scored): **passed**.

## By gold tier (`update_conflict` unless stated)

| tier | labelled / in tier | model update yes | model strict yes | = judge | = parser | = gold_update | strict = gold_strict |
|---|---|---|---|---|---|---|---|
| core | 2385 / 2388 | 2383 | 764 | 0.999 | 0.999 | 0.999 | 0.496 |
| update_only_fork | 259 / 282 | 229 | 0 | 0.116 | 0.884 | 0.884 | 1.000 |
| rejected | 11 / 12 | 11 | 1 | 0.000 | 1.000 | 0.000 | 0.909 |
| discovered_unverified | 96 / 105 | 14 | 11 | 0.146 | 0.854 | 0.854 | 0.885 |
| negative | 2666 / 51782 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |

## Field-level agreement with the GPT-5-mini judge (all labelled pairs)

| field | n | agreement | Cohen κ |
|---|---|---|---|
| same_referent | 5417 | 0.967 | 0.933 |
| same_relation | 5417 | 0.961 | 0.708 |
| context_overlap | 5417 | 0.920 | 0.000 |
| values_incompatible | 5417 | 0.783 | 0.580 |
| update_conflict | 5417 | 0.940 | 0.880 |
| strict_conflict | 5417 | 0.764 | 0.429 |

## Consistency

- 5417 labelled rows are 4062 distinct sentence pairs (a pair can occur in several subsets under different ids).
- Sentence pairs labelled more than once: 1183; identical on all six labels in 1183.
- Of these, labelled in different batches: 1164; identical in 1164.
- Pairs where both sentences parse: 5400. `same_referent` equals "same subject string" in 5400; `same_relation` equals "same template" in 5394.
- Same template and same value: 1613, of which labelled incompatible: 0. Same template and different value: 3473, of which labelled compatible (alias or containment): 55.

## Rows departing from the written rubric's derivation rules

none
