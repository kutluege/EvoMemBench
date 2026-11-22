---
name: pair-labelling
description: Guideline for labelling pairs of fact-store sentences with the six conflict labels (same_referent, same_relation, context_overlap, values_incompatible, update_conflict, strict_conflict) the way the human annotator of the pilot labelled them. Use when labelling batches under stage0_results/conflict_pairs/model_annotation/, or when checking such labels.
---

# Labelling fact pairs the way the human pilot annotator did

This guideline was written from the decisions of one human annotator on a pilot
set of pairs from this dataset (labelled 2026-11-22). Section 2 states the rules
their labels follow; section 4 lists their labelled pairs verbatim. Where a rule
and your own intuition disagree, the rule wins: the purpose of this pass is to
extend that annotator's reading to more pairs, not to produce a second opinion.

Each rule says whether it was **observed** in the human's labels or **inferred**
because the pilot had no such pair. Inferred rules come from the written rubric
the human worked under (section 1) and are the weaker part of this guideline.

## 1. The task and the rubric the human worked under

A pair is two sentences from a fact store. Most sentences follow a template with
a subject, a relation and a value ("X is a citizen of Y", "The author of X is
Y"). Many are counterfactual on purpose. Never judge whether a sentence is true;
judge only how the two sentences relate.

Answer `yes` or `no` for each of:

- `same_referent`: both sentences are about the same entity.
- `same_relation`: both assert the same attribute or relation.
- `context_overlap`: the two propositions apply under compatible validity
  conditions (time, place, condition).
- `values_incompatible`: the two values cannot both occupy the same slot.
- `update_conflict`: in a memory store that keeps one current value per
  (entity, attribute) slot, one sentence replaces the other's value.
- `strict_conflict`: the two sentences cannot both be true at the same time.

## 2. How the human decided

### same_referent

- **Observed.** `yes` when the two sentences have the same subject string.
  This holds for role and position names too: "placekicker", "center" are one
  referent across two sentences even when the two sports differ (P001, P008).
  Do not split a subject into word senses.
- **Observed.** `no` when the subjects are different entities, even when
  everything else matches: two books by one author (P026), two shows on one
  broadcaster (P057), two people with one citizenship (P019), two events in one
  sport (P050), two people at two universities (P009). The subject is the entity
  the sentence is about, not the value on the right.
- **Observed.** A historical state and the modern country or region are
  different entities: "Kingdom of England" and "England" are not the same
  referent (P004). Related places are different entities (Ireland / England,
  P018; Paris / Germany, P029).
- **Inferred.** Spelling variants and abbreviations of one name are the same
  referent.

### same_relation

- **Observed.** `yes` when both sentences assert the same attribute, whether or
  not the subjects are the same (P009, P019, P026 are all `yes`). This label is
  about the attribute only.
- **Observed.** A paraphrase of the same attribute is the same relation: "The
  Prime Minister of Sweden is …" and "The name of the current head of the Sweden
  government is …" (P053).
- **Observed.** `no` when the attributes differ, even with the same subject and
  a shared word: "was founded in the city of" vs "was founded by" (P000);
  "speaks the language of" vs "died in the city of" (P043).

### context_overlap

- **Observed.** `yes` in every pilot pair. The sentences carry no explicit time,
  place or condition, and the human did not read one into them. In particular a
  historical state as a value does not make the contexts disjoint: "a citizen of
  Kingdom of England" and "a citizen of Poland" overlap (P006).
- **Inferred.** Answer `no` only if both sentences state explicit qualifiers
  that exclude each other (two different stated years, for example). Expect this
  to be very rare; write a note when you do.

### values_incompatible

Compare the two values. The human judged this from the values and the relation,
independently of whether the subjects match.

- **Observed.** If `same_relation` is `no`, answer `no`: values of different
  attributes are not compared (P000, P043).
- **Observed.** Same relation, same value: `no` (P019, P026, P050, P057).
- **Observed.** Same relation, two different values: `yes`. This holds when the
  relation can naturally have several values: languages spoken (P007, P013,
  P024, P030, P041), citizenship (P006, P045), sports (P001, P008, P032, P042),
  music genres (P035, P039), "famous for" (P003, P022, P038), field of work
  (P016), city worked in (P047), performer (P028). The human did not answer `no`
  because the two values could coexist in the real world; that distinction is
  carried by `strict_conflict` instead.
- **Observed.** It also holds when the subjects differ: different subjects with
  different values is `yes` here (P004, P009, P018, P029), and
  `update_conflict` is then `no` because the referent differs.
- **Observed. The exception: one value contains the other.** When one value is
  a kind, part, denomination or subgenre of the other, the values are
  compatible, `no`: "Catholic Church" and "Christianity" (P005, P010, P012,
  P017); "rock music" and "rap rock" (P055). Two values under a common parent
  that do not contain each other are incompatible, `yes`: "punk rock" and
  "alternative rock" (P035); "jazz" and "post-punk" (P039); "association
  football" and "rugby union" (P032).
- **Inferred.** Two names for the same thing (alias, abbreviation, spelling
  variant) are compatible, `no`. A city and the country or region it lies in,
  where a template lets both appear, is containment, `no`.
- **Inferred.** A historical state and the modern country as two values: treat
  them as different entities, as the human did for subjects (P004), so `yes`;
  write the note `uncovered: historical vs modern value`.

### update_conflict

- **Observed, without exception.** `yes` exactly when `same_referent`,
  `same_relation`, `context_overlap` and `values_incompatible` are all `yes`.
  Otherwise `no`. Derive it; do not judge it separately.

### strict_conflict

`yes` only when `update_conflict` is `yes` **and** the relation holds a single
value at a time. If `update_conflict` is `no`, this is `no`.

The human applied "single value" narrowly: only relations that are unique by
definition. Whether the two particular values look far-fetched together does
not matter; the relation decides.

| Relation | Single value? | Basis |
|---|---|---|
| headquarters located in the city of | yes | observed (P014) |
| was created in the country of | yes | observed (P023, P025) |
| head of government, Prime Minister of | yes | observed (P048, P053, P056) |
| is associated with the sport of | no | observed (P001, P008, P032, P042) |
| is famous for | no | observed (P003, P022, P038) |
| is a citizen of | no | observed (P006, P045) |
| speaks the language of | no | observed (P007, P013, P024, P030, P041) |
| works in the field of | no | observed (P016) |
| was performed by | no | observed (P028) |
| type of music played | no | observed (P035, P039) |
| worked in the city of | no | observed (P047) |
| head of state | yes | inferred, like head of government |
| capital of | yes | inferred |
| located in the continent of | yes | inferred |
| born in the city of, died in the city of | yes | inferred |
| was founded in the city of | yes | inferred |
| chief executive officer, chairperson, head coach, Governor, director of | yes | inferred, one office holder at a time |
| original broadcaster of | yes | inferred |
| original language of | yes | inferred |
| is married to | yes | inferred, one at a time |
| author of | no | inferred, like "was performed by" |
| was founded by, was created by, was developed by | no | inferred, like "was performed by" |
| company that produced | no | inferred |
| university where educated | no | inferred |
| plays the position of | no | inferred, like sport |
| is employed by | no | inferred, like city worked in |
| child | no | inferred |
| official language of | no | inferred, like language spoken |
| was written in the language of | no | inferred |
| is affiliated with the religion of | no | inferred |

For a sentence that paraphrases one of these relations, use the row of the
relation it paraphrases. For a relation not in the table, apply the same test
(unique by definition, or not) and start the note with `uncovered:`.

## 3. Order of work for one pair

1. Find subject, relation and value in each sentence.
2. `same_referent` from the subjects alone.
3. `same_relation` from the attributes alone.
4. `context_overlap`: `yes` unless explicit qualifiers exclude each other.
5. `values_incompatible`: `no` if the relations differ; otherwise compare the
   values (same or containing: `no`; different: `yes`).
6. `update_conflict` = all four of the above are `yes`.
7. `strict_conflict` = `update_conflict` is `yes` and the relation is single
   valued in the table.

## 4. The human's labelled pairs

`ref` = same_referent, `rel` = same_relation, `ctx` = context_overlap,
`incompat` = values_incompatible, `update` = update_conflict, `strict` =
strict_conflict.

<!-- EXAMPLES:BEGIN (generated from the human sheet; do not edit by hand) -->
- **P000** A: "Christianity was founded in the city of Taipei." / B: "Christianity was founded by Jesus Christ."
  ref=yes, rel=no, ctx=yes, incompat=no, update=no, strict=no.
- **P001** A: "placekicker is associated with the sport of American football." / B: "placekicker is associated with the sport of rugby."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P003** A: "João Gilberto is famous for The Girl from Ipanema." / B: "João Gilberto is famous for Angel."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P004** A: "Kingdom of England is located in the continent of North America." / B: "England is located in the continent of Europe."
  ref=no, rel=yes, ctx=yes, incompat=yes, update=no, strict=no.
- **P005** A: "Henri Grégoire is affiliated with the religion of Catholic Church." / B: "Henri Grégoire is affiliated with the religion of Christianity."
  ref=yes, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P006** A: "John Evelyn is a citizen of Kingdom of England." / B: "John Evelyn is a citizen of Poland."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P007** A: "William Waynflete speaks the language of English." / B: "William Waynflete speaks the language of Latin."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P008** A: "center is associated with the sport of basketball." / B: "center is associated with the sport of rugby union."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P009** A: "The univeristy where Samuel Beckett was educated is Trinity College Dublin." / B: "The univeristy where Brian O'Nolan was educated is University College Dublin."
  ref=no, rel=yes, ctx=yes, incompat=yes, update=no, strict=no.
- **P010** A: "Kingdom of Etruria is affiliated with the religion of Catholic Church." / B: "Kingdom of Etruria is affiliated with the religion of Christianity."
  ref=yes, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P012** A: "John E. Sununu is affiliated with the religion of Catholic Church." / B: "John E. Sununu is affiliated with the religion of Christianity."
  ref=yes, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P013** A: "Ronald D. Moore speaks the language of English." / B: "Ronald D. Moore speaks the language of Dutch."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P014** A: "The headquarters of Blizzard Entertainment is located in the city of Irvine." / B: "The headquarters of Blizzard Entertainment is located in the city of Knoxville."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P016** A: "William Shakespeare works in the field of playwright." / B: "William Shakespeare works in the field of businessperson."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P017** A: "John E. Sununu is affiliated with the religion of Catholic Church." / B: "John E. Sununu is affiliated with the religion of Christianity."
  ref=yes, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P018** A: "Ireland is located in the continent of Europe." / B: "England is located in the continent of South America."
  ref=no, rel=yes, ctx=yes, incompat=yes, update=no, strict=no.
- **P019** A: "Gladys George is a citizen of United States of America." / B: "Estelle Getty is a citizen of United States of America."
  ref=no, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P022** A: "Allen Ginsberg is famous for Howl." / B: "Allen Ginsberg is famous for Natya Shastra."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P023** A: "Jump5 was created in the country of United States of America." / B: "Jump5 was created in the country of Republic of Cyprus."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P024** A: "Joseph Wright of Derby speaks the language of English." / B: "Joseph Wright of Derby speaks the language of Russian."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P025** A: "bluegrass music was created in the country of United States of America." / B: "bluegrass music was created in the country of Indonesia."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P026** A: "The author of The Call of Cthulhu is H. P. Lovecraft." / B: "The author of Little Women is H. P. Lovecraft."
  ref=no, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P028** A: "Nature Boy was performed by Nat King Cole." / B: "Nature Boy was performed by Donovan."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P029** A: "Paris is located in the continent of Europe." / B: "Germany is located in the continent of Africa."
  ref=no, rel=yes, ctx=yes, incompat=yes, update=no, strict=no.
- **P030** A: "Neil Simon speaks the language of English." / B: "Neil Simon speaks the language of Japanese."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P032** A: "Antonio Conte is associated with the sport of association football." / B: "Antonio Conte is associated with the sport of rugby union."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P035** A: "The type of music that Mike Watt plays is punk rock." / B: "The type of music that Mike Watt plays is alternative rock."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P038** A: "Hugh Hefner is famous for Playboy." / B: "Hugh Hefner is famous for The Vampyre."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P039** A: "The type of music that Michael Mantler plays is jazz." / B: "The type of music that Michael Mantler plays is post-punk."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P041** A: "T. S. Eliot speaks the language of English." / B: "T. S. Eliot speaks the language of French."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P042** A: "Alta IF is associated with the sport of association football." / B: "Alta IF is associated with the sport of baseball."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P043** A: "Fyodor Dostoyevsky speaks the language of Russian." / B: "Fyodor Dostoyevsky died in the city of Los Angeles."
  ref=yes, rel=no, ctx=yes, incompat=no, update=no, strict=no.
- **P045** A: "Max Eastman is a citizen of United States of America." / B: "Max Eastman is a citizen of Austria."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P047** A: "Laurence Olivier worked in the city of London." / B: "Laurence Olivier worked in the city of Washington, D.C.."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=no.
- **P048** A: "The Prime Minister of Sweden is Stefan Löfven." / B: "The Prime Minister of Sweden is Pedro Pierluisi."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P050** A: "2009 WNBA season is associated with the sport of association football." / B: "2004 NBA Draft is associated with the sport of association football."
  ref=no, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P053** A: "The Prime Minister of Sweden is Pedro Pierluisi." / B: "The name of the current head of the Sweden government is Gro Harlem Brundtland."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P055** A: "The type of music that John McVie plays is rock music." / B: "The type of music that John McVie plays is rap rock."
  ref=yes, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
- **P056** A: "The Prime Minister of Malta is Joseph Muscat." / B: "The Prime Minister of Malta is Pietro Parolin."
  ref=yes, rel=yes, ctx=yes, incompat=yes, update=yes, strict=yes.
- **P057** A: "The origianl broadcaster of The Drew Carey Show is American Broadcasting Company." / B: "The origianl broadcaster of China Beach is American Broadcasting Company."
  ref=no, rel=yes, ctx=yes, incompat=no, update=no, strict=no.
<!-- EXAMPLES:END -->
