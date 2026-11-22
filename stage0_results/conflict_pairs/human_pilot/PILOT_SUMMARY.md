# Pilot human review of parser–judge disputes — summary

- pairs reviewed: 60 ({'disputed': 50, 'control': 10}); annotators: 1
- This is a pilot. The pairs come from disputed tiers only, so nothing here estimates the judge's accuracy on the dataset, and one annotator gives no agreement figure. The gold dataset is unchanged.

## update_conflict: whom the annotator sides with

| group | n | human yes | agrees with judge | Wilson 95 % | agrees with parser | Wilson 95 % |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| disputed | 50 | 33 | 12 | [0.143, 0.374] | 38 | [0.626, 0.857] |
| control | 10 | 5 | 10 | [0.722, 1.000] | 10 | [0.722, 1.000] |
| update_only_fork | 35 | 27 | 8 | [0.121, 0.390] | 27 | [0.610, 0.879] |
| rejected | 2 | 2 | 0 | [0.000, 0.658] | 2 | [0.342, 1.000] |
| discovered_unverified | 13 | 4 | 4 | [0.127, 0.576] | 9 | [0.424, 0.873] |
| core | 5 | 5 | 5 | [0.566, 1.000] | 5 | [0.566, 1.000] |
| negative | 5 | 0 | 5 | [0.566, 1.000] | 5 | [0.566, 1.000] |

In a disputed tier the parser and the judge disagree on every pair, so the two counts sum to n.

## Agreement with the judge, field by field (all pairs)

| field | n | agree | rate | Wilson 95 % |
| --- | ---: | ---: | ---: | --- |
| same_referent | 60 | 56 | 0.933 | [0.841, 0.974] |
| same_relation | 60 | 59 | 0.983 | [0.911, 0.997] |
| context_overlap | 60 | 60 | 1.000 | [0.940, 1.000] |
| values_incompatible | 60 | 27 | 0.450 | [0.331, 0.575] |
| update_conflict | 60 | 22 | 0.367 | [0.256, 0.493] |
| strict_conflict | 60 | 49 | 0.817 | [0.701, 0.894] |
