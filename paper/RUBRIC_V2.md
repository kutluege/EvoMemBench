# Pair labels: annotator instructions, rubric v2

**DRAFT, 23 Nov 2026, for both authors to approve.** Rubric v1 is the text in
`hnav/labeling/audit_human_review.py`; the seed sheet and the disagreement review were filled
under it. This version is used from stage 5 of `PROTOCOL_ANNOTATION.md` on. Lines marked
**[R1]–[R4]** are choices the authors still have to confirm; the `strict_conflict` paragraph
depends on the decision table (`stage0_results/conflict_pairs/strict_review/DECISION_TABLE.md`).
A Turkish display translation is made when the stage 5 page is built; this English text stays
the reference.

## What changed from v1, and why

| Point | v1 | v2 |
|---|---|---|
| Different values | "Values that can coexist are compatible" | Two different values are different, whether or not both could be true. Whether they can both be true is asked separately, under `strict_conflict`. |
| Conditions | "Compatible or overlapping validity conditions" | "No" only when the sentences themselves state excluding qualifiers. |
| Same entity | "The same real-world entity" | The subject as written. |
| Same attribute | "Even if phrased differently" | The same, with the office titles spelled out. |
| `strict_conflict` | Two definitions that disagree | One definition, applied through the decision table. |

The first row is where the 282 disputed "update-only" pairs come from: GPT-5 mini answered
"compatible" on them, mostly giving a multi-valued relation or subsumption as its reason, while
the first author read the same row by slot.

## Instructions

You are shown pairs of sentences from a fact store. Each sentence says that a subject has a
value for an attribute ("X is a citizen of Y", "The capital of X is Y"). Many sentences are
false on purpose. **Do not judge whether a sentence is true.** Judge only how the two sentences
relate. Work alone; do not consult the other annotator, any earlier sheet or any machine label.

Go through four checks, then answer the two questions.

1. **Same entity?** Compare the two subjects as they are written.
   - The same name is the same entity, even when the name could belong to several real things
     (two people called David Crane; "center" as a position in two sports).
   - Two names are the same entity only when one is a spelling variant or the full form of
     the other.
   - A historical state and the present-day country are different entities (Kingdom of
     England, England). Related places are different entities (London, Great Britain).
   - The value on the right plays no part in this check.
2. **Same attribute?** Compare what is being said about the subject.
   - Two wordings of one attribute are the same attribute: "The Prime Minister of X is" and
     "The name of the current head of the X government is"; **[R1]** "was written in the
     language of" and "The original language of … is".
   - **[R2]** "The President of X is" and "The name of the current head of state in X is" are
     the same attribute. "Head of state" and "head of government" are different attributes,
     even for a country where one person is both.
   - A shared word does not make the same attribute: "was founded in the city of" and "was
     founded by" are different.
3. **Same conditions?** Yes, unless both sentences state qualifiers that exclude each other
   (two different stated years, two stated places of validity). Do not infer a condition from
   what you know about the values: "a citizen of ancient Rome" carries no stated condition.
4. **Two different values?** Compare the two values.
   - Yes when they are different things, **whether or not both could be true together**: two
     languages, two citizenships, two sports.
   - No when they are the same value, or two names for the same value ("Catholicism",
     "Catholic Church"; "football", "association football").
   - No when one value contains the other. **[R3]** Containment means exactly one of: a part
     of ("Europe", "Eurasia"), a kind of ("rock music", "hard rock"), a branch or denomination
     of ("Christianity", "Methodism").
   - Yes when the two values sit under a common parent without one containing the other
     ("Catholic Church", "Methodism"; "punk rock", "alternative rock").
   - **[R4]** If you do not know whether one value contains the other, answer yes and say so
     in the notes.

**`update_conflict`** is yes exactly when all four checks are yes: in a store that keeps one
current value per entity and attribute, one sentence replaces the other's value. This is yes
for a relation that naturally has several values, too.

**`strict_conflict`** is asked only when `update_conflict` is yes: can the two sentences both
be true of the entity at the same time? If they cannot, answer yes. *[This paragraph is
completed from the decision table: which relations hold one value at a time (D1, D2), and
whether two values that exclude each other count for the others (D4–D6).]* In no case judge
whether either sentence is true of the real person or thing; judge only whether the two values
can hold together.

Answer yes or no to both questions for every pair; no blanks, no "unsure". Use the notes for
anything you want to flag.

## Examples (invented; none is in the dataset)

| Sentence A | Sentence B | update | Why |
|---|---|---|---|
| Mira Halden is a citizen of Norway. | Mira Halden is a citizen of Chile. | yes | Same entity and attribute, two different values. That both could be true does not matter here. |
| Mira Halden is a citizen of Norway. | Tomas Reik is a citizen of Chile. | no | Different entities. |
| Mira Halden is a citizen of Norway. | Mira Halden was born in the city of Oslo. | no | Different attributes. |
| Orvin Castle is located in the continent of Europe. | Orvin Castle is located in the continent of Eurasia. | no | Eurasia contains Europe. |
| Lund Quartet plays jazz. | Lund Quartet plays bebop. | no | Bebop is a kind of jazz. |
| Lund Quartet plays jazz. | Lund Quartet plays country music. | yes | Neither contains the other. |
| The Prime Minister of Varda is Ana Brel. | The name of the current head of the Varda government is Jon Mast. | yes | Two wordings of one attribute, two values. |
| The name of the current head of state in Varda is Ana Brel. | The name of the current head of the Varda government is Jon Mast. | no | Different attributes. |

## What the authors still have to confirm

- **[R1]** "was written in the language of" and "The original language of … is" are one
  attribute. The first author answered so on the seed sheet (P059) and four times in the
  disagreement review.
- **[R2]** "President of" is "head of state"; "Prime Minister of" is "head of government".
  No human answer exists for the first; the model workers decided it on their own.
- **[R3]** The containment list. The first author's earlier answers treat Catholic Church /
  Christianity, Christianity / Methodism, rock music / rap rock and rock music / hardcore punk
  as containment, but country music / bluegrass music as two different values. Under [R3] as
  written, bluegrass is a kind of country music and the last pair would be "no".
- **[R4]** Unknown containment counts as different.
- The six decisions D1–D6 of the decision table, which complete the `strict_conflict` paragraph.
