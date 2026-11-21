---
name: nlp-journal
description: >
  Submission standards for the paper "Read-Time Removal of Superseded Facts in Agent
  Memory Using Embedding Geometry", targeted at the journal Natural Language Processing
  (Cambridge University Press). Use when editing anything under paper/ (manuscript,
  figures, captions, supplement, end-matter statements, cover letter), when planning,
  running or reporting an experiment whose result is meant for the paper (new test set,
  baselines, human annotation, second encoder, latency), or when changing code that
  produces a number the manuscript reports.
---

# Working toward the Natural Language Processing (Cambridge) submission

The paper is being prepared for *Natural Language Processing* (Cambridge University Press,
formerly *Natural Language Engineering*). The authors' target date is 7 January 2027. This
skill says how journal expectations change the way you write the manuscript, design
experiments and touch code in this repository.

## 1. Source, trust levels and precedence

The source is the readiness plan at the repository root:
`Natural Language Processing (Cambridge)_ Submission Readiness Plan for Read-Time Removal of Superseded Facts.md`
(research compiled 2026-11-21). Read it when you need the evidence behind a rule, the cut
table (Part 5), the checklist (Part 7) or the open questions (Part 10). Every claim in it
carries one of three labels, and the label decides how you may use the claim:

| Label | Meaning | How to use it |
|---|---|---|
| **[J]** | Stated by the journal or Cambridge | A rule. Re-check it on the journal's live author instructions before submission; the plan is a snapshot and the journal changes its workflow in 2027. |
| **[S n/8]** | Seen in n of 8 sampled papers | An observation from a small sample with several fields unverified. It can motivate a choice. It is never "the journal requires". |
| **[I]** | The researcher's inference | Advice. The authors decide. This covers the ranking of fixes, the day estimates, the likely editors and the risk list. |

Never promote an [S] or [I] claim to a journal requirement in the manuscript, the cover
letter, a commit message or a report to the user.

Precedence when sources disagree:

1. `CLAUDE.md` hard invariants and `HNAV_AGENT_BRIEF.md`.
2. Registered protocols and preregistrations (`paper/PROTOCOL_GENERALISATION.md` once
   registered, `stage0_results/**/**PREREG*.md`).
3. Decisions the user has recorded in the repository (dated "user decision" notes).
4. This skill.
5. Suggestions in the readiness plan.

If a journal-driven change would need an invariant broken, a registered protocol bypassed
or a recorded decision reversed, stop and report it to the user. Do not resolve it yourself.

`THESIS_CLAIMS.md` binds thesis-facing documents. This skill binds `paper/`. The paper may
use different wording from the thesis; that never changes thesis documents or code.

## 2. Which manuscript file

**The current manuscript is not in this repository.** The latest version is a PDF the
user keeps outside the repository, `nlpCambrdige-main.pdf`: 34 pages, built on 2026-10-09
in the journal's class. The readiness plan reviewed that version, and the plan's section
numbers are that PDF's numbers (Related Work is §2 with five subsections, cost is §4.9,
plan statistics is §6.6, limitations is §8.5).

The LaTeX files committed under `paper/` are older (2026-09-23) and are not the submission
source:

- `hnav1stone.tex` is the closest ancestor. It has no Related Work section, numeric
  citations, seven keywords and a generic article class.
- `hnav_geo_manuscript.tex` is an earlier lineage in the achemso class. `PROVENANCE.md`
  and `REVIEW_RESPONSE.md` name this file, so their section numbers do not match the
  current PDF; map their rows by content.

Consequences:

- Do not edit a committed `.tex` file as if it were the current manuscript, and do not
  rebuild the current text from the PDF. Ask the user for the current LaTeX source, or for
  it to be committed under `paper/`, before making manuscript edits.
- Until the source is available, deliver manuscript work as a list of proposed changes
  keyed to the PDF's section titles and page numbers, with the replacement text written
  out.
- If the PDF is not available in the session either, say so. Do not review the old `.tex`
  files in its place without telling the user which version you read.
- Once a source file is confirmed, edit that one file only.

## 3. Journal rules that constrain the manuscript [J]

- **Length:** an Article is about 8,000–12,000 words. Whether tables, captions, references
  and appendices count is unknown (Part 10). The plan's working target is a body of about
  11,500 words [I].
- **Abstract:** approximately 300 words. **Keywords:** 3–5.
- **First page:** title, every author's name and email address.
- **File:** one PDF with figures and tables embedded. The journal LaTeX class is strongly
  encouraged and is not in this repository yet; LaTeX source is required after acceptance.
- **Citations:** author–date, "et al." for three or more authors, grouped citations
  ordered by date, minimum capitalisation in titles.
- **Headings:** at most three numbered levels.
- **Numbers:** written out up to 100 unless they are precise measurements; "per cent", not
  "%"; commas in numbers of four or more digits.
- **Figures and tables:** every figure cited in order; self-explanatory captions; every
  table has a source; table headings in sentence case; figures meet WCAG 2.1 AA and each
  has alt text.
- **Mandatory statements:** competing interests, funding, data availability, ethics, and
  a declaration of AI use. CRediT and acknowledgements are optional.
- **Supplementary material** is published as submitted, not copyedited, and is part of the
  formal record.
- **Review** is single-anonymised, so author names stay in the manuscript.

State of the current PDF (built 2026-10-09), read from its extracted text on 2026-11-21.
Re-check each point against the version in front of you:

- Already in line: journal class, author–date citations, five keywords, three heading
  levels, a single "Protocol deviations" paragraph in §5.1, and `sh_64k` described as
  frozen transfer in the abstract, §5.1, the limitations and the conclusion.
- Abstract: about 325 words, above the "approximately 300" guideline.
- Length: about 15,000 words from the introduction to the conclusion, counting captions
  and table text, against a guideline of 8,000–12,000.
- First page: only the corresponding author's email address is printed.
- Open `[CONFIRM: …]` items: the GPT-5 mini snapshot and dates of use, one vLLM version
  string, the AI-assistance declaration, funding, competing interests, the public release
  and archival DOI, ethics, CRediT roles, access dates in two model-card references, and
  the Holm (1979) reference.
- Register: the method is still named H-Nav-GEO, project vocabulary is still frequent
  (campaign, arms, page, pool, plan, quarantined tier), and Figure 1 prints artifact file
  names in its source line.
- Figures are not in the repository (`paper/figures/` does not exist).

## 4. Writing the manuscript

### Register

Write a paper, not a project log. The plan's sharpest criticism is that the text reads as
an internal engineering report [I].

- Replace project vocabulary in the manuscript text, tables, figures and captions with
  standard terms. The plan names these to remove: "H-Nav", campaign, arms, page, pool,
  plan, A/A floor, CES, `gold_update`, quarantined, "the runner refuses". It offers
  "condition", "retrieved context" and "deletion set" as replacements. Agree the rest of
  the mapping with the user once, then apply one mapping everywhere.
- Renaming the method is the authors' decision. Do not invent a name and apply it. The
  committed `.tex` files define the name once, in a `\geo` macro; if the current source
  keeps that macro, the rename is a one-line change once they choose.
- The vocabulary change applies to the manuscript and its figures only. Never rename code
  identifiers, directories, artifact keys, JSON fields or thesis documents to match, and
  keep `paper/PROVENANCE.md` mapping the paper's wording to the real artifact names.
- Development history, secondary analyses and artifact-freezing detail move to the
  supplement with one sentence left in the main text (plan Part 5).

### Claims

- Say only what a committed artifact supports. Do not write "human-validated", an
  agreement figure, "fact-disjoint test" or a baseline comparison until the result exists
  in the repository. The plan's cover-letter points 3 and 4 assume results that had not
  been produced on 2026-11-21.
- `sh_64k` overlaps calibration. Call it "frozen transfer" or "partial overlap", never
  "held-out". Write "ABTT cosine", never "whitened cosine".
- Keep every disclosure when cutting for length: the missed preregistered endpoint (the
  plan asks for it in the end-to-end results section and in the abstract's final clause,
  not only in the design section), the void flag and harmful deletions on `sh_64k`, the
  rerun of the voided gemma-3 cell, the development use of `sh_64k` and the reference
  model, and the single-LLM labelling. A disclosure may move; it may not disappear.
  Protocol deviations belong in one "Protocol and deviations" paragraph in the
  experimental-design section [I].
- Explain why the work is English-only. The journal particularly encourages multilingual
  and low-resource work [J].
- Report cost or latency as a measured number if the paper claims the method is cheap.

### Numbers

- Every number in the manuscript is traced in `paper/PROVENANCE.md`. A new number comes
  from a committed artifact or from `paper/derive_revision_numbers.py`, and its
  provenance row lands in the same commit. The current PDF has numbers that were added
  after `PROVENANCE.md` was last updated; a number with no provenance row is an open item
  to report, not one to assume correct.
- Restyling ("per cent", words for small counts, thousands commas) must not change a
  value or its precision. Measurements, table cells and statistics keep their digits.
- The supplement is held to the same provenance standard as the body, because it cannot
  be corrected after publication except by a formal correction.

### References

- Before a reference enters the bibliography, check that it exists and that it supports
  the sentence citing it. The plan's list of papers from this journal (Part 4) is a lead
  list; several of its fields are marked "nv" (not verified), and its one-line summaries
  are not grounds for a citation.
- Replace a preprint with the peer-reviewed version where one exists, after checking the
  venue and year yourself.

### Figures and tables

- No file names, logos or internal labels in graphics. No information carried by colour
  alone. Text large enough to read at print size. Draft alt text for every figure.
- Outstanding graphic corrections are listed under "Figures to regenerate" in
  `paper/REVIEW_RESPONSE.md`; they are still open until the regenerated files are seen.

### End matter and declarations

- Never fill a `\confirm{...}` placeholder with a guess. Funding, grant numbers, competing
  interests, CRediT roles, licences, the archival DOI, software versions and dates of AI
  use are facts only the authors hold. Draft the sentence, leave the fact marked, and list
  the open items in your report.
- Exact wordings the journal gives [J]: "Competing interests: The author(s) declare none"
  and "Ethical approval was not required." Use each only if the authors confirm it is true.
  Human annotators add a consent note to the ethics statement.
- AI declaration [J]: tool name and version, dates of use, how others can access it, and a
  full description. Use that analysed or labelled data goes in the methods section (the
  LLM judge of the conflict dataset, and the Laya second reader if it is reported).
  Writing assistance goes in the acknowledgements. An AI tool cannot be an author.
  The commit history of this repository records AI-assisted code and manuscript drafting;
  tell the authors so that their declaration is complete.

## 5. Experiments meant for the paper

### What the plan asks for and what the repository already has

| Plan item | Repository state | What to do |
|---|---|---|
| Human validation of the LLM labels, with agreement figures ("must" [I]) | `hnav/labeling/audit_laya.py`, `audit_compare_laya.py`, `audit_human_review.py`, `agreement_stats.py`. The review set was fixed by a user decision on 2026-09-30: targeted, two blind annotators. | Use the existing design. The plan suggests a different sample (a stratified 400–600 pairs); raise the difference with the user and do not redesign on the plan's authority. Ingest never modifies the gold dataset or its frozen tier counts. |
| Fact-disjoint test set as the headline ("must" [I]) and end-to-end baselines ("must" [I]) | `paper/PROTOCOL_GENERALISATION.md`, a draft that was not registered on 2026-11-21. | The protocol governs sizes, arms, endpoints and decision rules, not the plan's sketch. Generate no record and no question until the registered version is committed. |
| Generative "extract then keep newest" comparator, second encoder, latency ("should" [I]) | Not in the protocol draft. | Each needs the user's decision: add it to the protocol before registration, or run it later and label it post hoc. |
| LongMemEval, record-level retrieval ("can drop" [I]) | — | Do not start them. Name them as future work if the text needs it. |

### Rules for any paper-facing experiment

- The `CLAUDE.md` invariants apply unchanged: fit on calibration only, never tune on a
  test set, gold answers stay in the offline tier, `sh_262k` stays excluded, stop at every
  gate.
- Fix the question, the endpoint, the statistical test and the decision rule in a
  committed protocol before any data exists. After registration, a change is a dated
  amendment and an unlisted analysis is labelled post hoc.
- Give each baseline the same fitting rule, calibration data and effort as the method, and
  name the strongest baseline before any test output is read. A weak baseline is the
  objection reviewers raise first [I].
- Report every outcome, including a negative or null one. A cell is void only for an
  instrument fault, and the fault is stated.
- Keep the repository's statistical practice: paired exact tests with multiplicity
  correction, intervals on rates, results stratified by subset and never pooled, and the
  number of runs per cell stated.
- Commit the outputs together with what a reader needs to reproduce them (model
  identifiers, serving versions, prompts, seeds, hashes). Smoke outputs are never
  reported.
- Do not edit a committed artifact, a void record or a measured number to suit the
  journal framing.

## 6. Code changes

- The method under test is a frozen artifact with a recorded fingerprint and operating
  point. A journal-motivated change must not alter its behaviour. New baselines and
  conditions go in new modules or pipeline directories.
- After a change that could reach a reported number, run `pytest hnav/tests/ -q` and
  `python paper/derive_revision_numbers.py`, and compare with the manuscript. If a number
  moves, stop and report it; do not update the manuscript to match.
- The code and data will be released with an archival DOI. Keep the release honest and
  clean: no secrets, no machine-specific absolute paths, a licence note for data derived
  from MemoryAgentBench (verify the licence; do not assume it), and a documented path from
  the committed artifacts to every table. A new `.gz` under
  `stage0_results/conflict_pairs/` needs its `!name.gz` line or it never reaches a commit.
- Commit manuscript work with the `Paper:` prefix and audit-chain work with `Audit:`.

## 7. Actions that belong to the authors

Do not do these yourself; prepare the material and hand it over:

- submitting to ScholarOne, or writing to the editorial office or to ULAKBİM;
- making the repository public, minting a DOI or posting a preprint;
- registering a protocol (the registration commit is the authors' act; draft it if asked);
- choosing the method's name, the annotators, or which "should" items to run;
- confirming open-access funding eligibility, which the plan could not verify.

## 8. Before reporting the manuscript as ready

Walk the plan's Part 7 checklist against the built PDF, not against the source. Report
each item as done, open or unverifiable. List every remaining `\confirm{...}`, every
[J] rule you could not re-check on the live journal page, and the Part 10 questions that
are still unanswered.
