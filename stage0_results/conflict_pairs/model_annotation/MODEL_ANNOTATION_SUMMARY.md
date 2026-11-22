# Model annotator pass — summary

Annotator: claude-fable-5-2, reasoning effort medium, Claude Code subagents (parallel workers). Labels follow a guideline written from the human pilot; no model weights were changed. These are model labels, not human labels.

Pairs labelled: 20 ({'heldout': 20}).

## Coverage

| group | batches done | invalid | missing |
|---|---|---|---|
| heldout | 1 | 0 | 0 |
| stage1 | 0 | 0 | 54 |

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
| core | 2 / 2388 | 2 | 1 | 1.000 | 1.000 | 1.000 | 0.500 |
| update_only_fork | 12 / 282 | 9 | 0 | 0.250 | 0.750 | 0.750 | 1.000 |
| rejected | 1 / 12 | 1 | 0 | 0.000 | 1.000 | 0.000 | 1.000 |
| discovered_unverified | 4 / 105 | 1 | 1 | 0.250 | 0.750 | 0.750 | 0.750 |
| negative | 1 / 51782 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |

## Field-level agreement with the GPT-5-mini judge (all labelled pairs)

| field | n | agreement | Cohen κ |
|---|---|---|---|
| same_referent | 20 | 0.950 | 0.857 |
| same_relation | 20 | 1.000 | — |
| context_overlap | 20 | 1.000 | — |
| values_incompatible | 20 | 0.500 | 0.194 |
| update_conflict | 20 | 0.350 | -0.161 |
| strict_conflict | 20 | 0.800 | 0.412 |

## Rows departing from the written rubric's derivation rules

none
