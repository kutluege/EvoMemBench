# Decision table for `strict_conflict` — to be filled by both authors

`strict_conflict` means: the two sentences cannot both be true of the entity at the same time. It is asked only of pairs that are already update conflicts (same entity, same attribute, two different values, neither containing the other).

Fill the `decision` column of `decision_table.csv` with `yes` or `no`. A group decision covers every relation of the group; to make an exception, write the other answer on that relation's row with a reason. Counts are update-conflict pairs under the model annotator's labels. "First guideline" is what the model answered under the table of 22 November, which is not final. "Own answers" are the first author's earlier answers: `P` rows from the seed sheet and `D` rows from the disagreement review, both under the ambiguous first rubric, and `S` rows from the strict sheet; `+` is yes, `-` is no.

## Decisions

The first six rows of the CSV are these decisions; the relation rows follow.

| | Decision | Answer |
| --- | --- | --- |
| D1 | Group A (one by definition): strict conflict? | |
| D2 | Group B (one holder or seat at a time): strict conflict, although a second holder is conceivable? One answer for the group. | |
| D3 | Group C (several values are normal): the relation alone is never a strict conflict. Confirm. | |
| D4 | In group C, are two values that exclude each other a strict conflict (for example citizenship of two states that never existed in the same period)? If yes, these pairs need a per-pair pass; if no, every group C pair is `no`. | |
| D5 | If D4 is yes: does it apply only when the two values never existed in the same period (answer `period`), or also to values that exclude each other for another reason, such as two religions or two sports positions (answer `any`)? | |
| D6 | If D2 is no: does D4 then also apply to group B (two spouses who never lived at the same time)? | |

## Group A: One by definition

The relation names a single event or a single origin: nothing can be born, die or be founded in two places, and "original" picks one. If yes, two different values cannot both be true.

| relation | pair ids | sentence pairs | first guideline | own answers | decision |
| --- | ---: | ---: | --- | --- | --- |
| was created in the country of | 121 | 69 | yes | 4 yes, 0 no: P023+ P025+ P040+ S003+ | |
| died in the city of | 52 | 29 | yes | — | |
| was born in the city of | 48 | 32 | yes | — | |
| The origianl broadcaster of … is | 29 | 24 | yes | 0 yes, 1 no: S011- | |
| was founded in the city of | 26 | 15 | yes | — | |
| The original language of … is | 7 | 5 | no | 0 yes, 1 no: S002- | |
| **total** | 283 | 174 | | | |

## Group B: One holder or one seat at a time

An office, a seat or a status that is normally held by one value at a time, although a second one is conceivable (co-chief executives, two capitals, dual headquarters, polygamy, a country on two continents). The whole group needs one answer to the question: does "conceivable" make it multi-valued?

| relation | pair ids | sentence pairs | first guideline | own answers | decision |
| --- | ---: | ---: | --- | --- | --- |
| is married to | 91 | 56 | yes | — | |
| is located in the continent of | 71 | 41 | yes | — | |
| The headquarters of … is located in the city of | 70 | 46 | yes | 1 yes, 0 no: P014+ | |
| The capital of … is | 67 | 38 | yes | 1 yes, 0 no: D037+ | |
| The chief executive officer of … is | 43 | 23 | yes | — | |
| The chairperson of … is | 39 | 24 | yes | — | |
| The name of the current head of the … government is | 36 | 22 | yes | — | |
| The director of … is | 26 | 13 | yes | — | |
| The name of the current head of state in … is | 26 | 13 | yes | — | |
| The head coach of … is | 18 | 13 | yes | — | |
| office titles the parser does not read (Prime Minister of, President of, Attorney General) | 5 | 3 | yes | 6 yes, 0 no: D004+ D013+ D035+ P048+ P056+ S009+ | |
| The Governor of … is | 2 | 1 | yes | — | |
| **total** | 494 | 293 | | | |

## Group C: Several values are normal

A person has several languages, citizenships, employers, children; a work has several authors or performers. Two different values can both be true, so the relation alone never makes a strict conflict. Decision D4 says what happens when the two particular values exclude each other.

| relation | pair ids | sentence pairs | first guideline | own answers | decision |
| --- | ---: | ---: | --- | --- | --- |
| is a citizen of | 331 | 228 | no | 1 yes, 4 no: D006+ P006- P044- P045- S000- | |
| is associated with the sport of | 224 | 135 | no | 0 yes, 12 no: D026- D029- D030- D038- P001- P002- P008- P032- P036- P037- P042- S007- | |
| is affiliated with the religion of | 161 | 110 | no | 0 yes, 1 no: P046- | |
| The author of … is | 150 | 99 | no | — | |
| plays the position of | 136 | 96 | no | — | |
| was founded by | 116 | 73 | no | — | |
| was performed by | 94 | 63 | no | 0 yes, 1 no: P028- | |
| was created by | 93 | 59 | no | 0 yes, 1 no: P015- | |
| The univeristy where … was educated is | 74 | 46 | no | — | |
| was developed by | 74 | 49 | no | 0 yes, 1 no: S001- | |
| The type of music that … plays is | 52 | 34 | no | 0 yes, 3 no: D005- P035- P039- | |
| speaks the language of | 48 | 32 | no | 0 yes, 10 no: P007- P011- P013- P024- P030- P031- P033- P041- S004- S008- | |
| The official language of … is | 47 | 26 | no | — | |
| is famous for | 47 | 35 | no | 0 yes, 4 no: P003- P022- P038- S005- | |
| is employed by | 43 | 30 | no | 0 yes, 1 no: P054- | |
| The company that produced … is | 35 | 22 | no | — | |
| was written in the language of | 34 | 24 | no | — | |
| works in the field of | 32 | 18 | no | 0 yes, 4 no: D032- P016- S006- S010- | |
| 's child is | 30 | 18 | no | 0 yes, 1 no: P034- | |
| worked in the city of | 30 | 21 | no | 0 yes, 2 no: D024- P047- | |
| **total** | 1851 | 1218 | | | |

## Group P: Two wordings of one relation

The two sentences use different templates for the same attribute. They follow the decision of the relation they paraphrase; the only question is whether the two wordings are the same relation at all, which rubric v2 settles.

| relation | pair ids | sentence pairs | first guideline | own answers | decision |
| --- | ---: | ---: | --- | --- | --- |
| The name of the current head of the … government is / unparsed | 5 | 3 | yes | 4 yes, 0 no: D017+ D036+ D039+ P053+ | |
| The original language of … is / was written in the language of | 4 | 4 | mixed (1 yes, 3 no) | 4 yes, 1 no: D002+ D003+ D007+ D014+ P059- | |
| **total** | 9 | 7 | | | |
