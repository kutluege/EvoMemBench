# Human review — annotator instructions

You are labelling pairs of sentences from a fact store. Do **not** check whether
either sentence is true in the real world; decide whether the two sentences
express conflicting propositions. Work alone, do not consult the other
annotator, and do not open `human_review_key.json`.

For each pair, first identify what each sentence asserts — subject, attribute
(relation), value, and any validity context (time, place, population,
organization, condition) — then answer yes/no in each column:

- `same_referent`: both sentences are about the same real-world entity
  (aliases, abbreviations and different surface strings can name one entity).
- `same_relation`: both assert the same attribute or relation, even if phrased
  differently.
- `context_overlap`: the propositions apply under compatible or overlapping
  validity conditions.
- `values_incompatible`: the two values cannot both occupy the same slot under
  the same context. Paraphrases, aliases, one value containing the other, and
  values that can coexist are **compatible** (answer no). Do not answer yes
  merely because the strings differ.
- `update_conflict`: under a memory-store convention with one current value
  per (entity, attribute) slot, one sentence replaces the other's value. This
  is yes exactly when the four checks above are all yes, even if the relation
  is naturally multi-valued (citizenships, children, languages, ...).
- `strict_conflict`: the two sentences cannot both be true at the same time in
  the real world. This is yes only when `update_conflict` is yes **and** the
  relation admits a single value at a time.

Write `yes` or `no` in every label cell (no blanks, no "unsure"); use `notes`
for anything you want to flag. Save the file with the same columns.

---

## Pilot sheet

This sheet is a pilot: a small number of pairs, labelled before the full
review, to test these instructions. Two ways to fill it:

1. Open `pilot_label.html` in a browser, answer every question for every
   pair, and press "Download CSV". Progress is kept in the browser.
2. Or fill `pilot_sheet.csv` directly and save it as comma-separated UTF-8.

Then score it:

    python hnav/labeling/audit_human_pilot.py score --sheet <the filled file>

Do not open `pilot_key.json` before you have finished.
