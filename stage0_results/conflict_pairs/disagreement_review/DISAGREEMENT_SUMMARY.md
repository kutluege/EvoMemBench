# Human review of gold-model disagreements — summary

- sentence pairs reviewed: 40, covering 57 disputed pair ids; annotators: 1
- annotator A: update_conflict yes on 19 sentence pairs, strict_conflict yes on 12; rows departing from the rubric's derivation rules: 0
- 10 of the sentence pairs were labelled in the pilot and shown to the model as examples; on those the model label repeats a human label.
- Only disputed pairs were reviewed. Nothing here bears on the pairs on which gold and model agree. The gold dataset is unchanged.

## update_conflict: whom annotator A sides with (pair ids)

| group | n | sides with gold | Wilson 95 % | sides with model | Wilson 95 % |
| --- | ---: | ---: | --- | ---: | --- |
| all disputed pairs | 57 | 1 | [0.003, 0.093] | 56 | [0.907, 0.997] |
| in evaluation set | 32 | 1 | [0.006, 0.157] | 31 | [0.843, 0.994] |
| outside evaluation set | 25 | 0 | [0.000, 0.133] | 25 | [0.867, 1.000] |
| gold yes, model no | 32 | 1 | [0.006, 0.157] | 31 | [0.843, 0.994] |
| gold no, model yes | 25 | 0 | [0.000, 0.133] | 25 | [0.867, 1.000] |
| text new to the pilot | 41 | 1 | [0.004, 0.126] | 40 | [0.874, 0.996] |
| text labelled in the pilot | 16 | 0 | [0.000, 0.194] | 16 | [0.806, 1.000] |
| core | 2 | 0 | [0.000, 0.658] | 2 | [0.342, 1.000] |
| update_only_fork | 30 | 1 | [0.006, 0.167] | 29 | [0.833, 0.994] |
| rejected | 11 | 0 | [0.000, 0.259] | 11 | [0.741, 1.000] |
| discovered_unverified | 14 | 0 | [0.000, 0.215] | 14 | [0.785, 1.000] |

Gold and model differ on every pair here, so the two counts sum to n. Pair ids that share a sentence pair share one human answer and are not independent.

Sentence pairs whose pair ids carry opposite gold labels: 5 (annotator A says update_conflict on 5).
