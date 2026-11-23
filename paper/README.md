# paper/

The paper "Read-time removal of superseded facts in agent memory using embedding
geometry" (E. Kutlu, Ş. Özönder), being prepared for *Natural Language Processing*
(Cambridge University Press). The journal was chosen on 2026-11-22.

## What is current

| Path | What it is |
|---|---|
| `nlp_cambridge/main_nlp.tex` | **The submission source.** Edit this file and no other. |
| `nlp_cambridge/main_nlp.pdf` | Build of 2026-10-09 (Tectonic, 34 pages). Stale after any edit until rebuilt. |
| `nlp_cambridge/refs_nlp.bib`, `main_nlp.bbl`, `nlplike-links.bst` | Bibliography: 87 entries, author–date. |
| `nlp_cambridge/CUP-JNL-NLP.cls`, `cup_logo.*` | The journal's class files, unmodified. |
| `nlp_cambridge/figures/` | The seven figure PDFs. Their generating files are not in this repository. |
| `nlp_cambridge/SUBMISSION_REPORT.md` | How the source was converted to the journal class, and its open items. |
| `nlp_cambridge/template_original/` | The journal's guide and samples, for reference. |
| `journal/READINESS_PLAN.md` | Research on what the journal expects and what the paper still needs (2026-11-21). |
| `journal/FORMAT_BRIEF.md` | The format and conversion brief the source was built from (2026-10-09). |
| `journal/SKILL.md` | Working rules for manuscript edits, paper-facing experiments and code. Loaded through `.claude/skills/nlp-journal/`. |
| `journal/DEVIR_NOTU.md` | Handoff note of 24 November 2026 (Turkish): decisions, done, to do, open decisions, working rules. Start here when resuming on another machine. |
| `journal/WEEKLY_PLAN.md` | The week-by-week plan to submission on 14 January 2027, revised 23 November 2026: the five claims, what each still needs, and the tasks of Weeks 0–7. |
| `journal/WEEKLY_PLAN_NOTES.md` | Open decisions and proposed work items, input to the week-by-week plan. Where the two differ, `WEEKLY_PLAN.md` is the later one. |
| `journal/YAPILANLAR.md` | Dated log of work completed for the submission (Turkish). Only finished, checked work is entered. |
| `PROTOCOL_GENERALISATION.md` | Protocol for the new-set evaluation. Draft, not registered. |
| `PROTOCOL_GENERALISATION_ADDITIONS.md` | Additions proposed for that protocol before registration: two baselines, the generative comparator, cost, the hosted reference model and the wording rule for it. Draft. |
| `RUBRIC_V2.md` | Annotator instructions, second version. Draft for the authors to approve. |
| `PROTOCOL_ANNOTATION.md` | Protocol for the pair labels: human seed, model at scale, human review of disagreements, independent audit. Draft, not registered; stages 1–4 are a record of work already done. |

Build: `pdflatex main_nlp`, `bibtex main_nlp`, `pdflatex main_nlp`, `pdflatex main_nlp`,
run inside `nlp_cambridge/`.

## Where the source came from

`nlp_cambridge/` and `journal/FORMAT_BRIEF.md` were imported on 2026-11-22 from the
authors' paper repository `tezim_paper`, commit `1e39c8d`
(`submissions/02_NLP_Cambridge/` and `journalformats/02_NLP_Cambridge.md`). Not imported:
the versions for the five other journals, the journal-independent base draft
(`integrated/`), the literature notes, and the two zip archives (the upload package and
the journal's original template zip), which this repository's ignore rules exclude.

From the import date this folder is the working copy. A change made in `tezim_paper`
after `1e39c8d` is not here until it is imported again.

## Older files, kept as dated records

| Path | Status |
|---|---|
| `hnav_geo_draft.tex` | First draft, 2026-09-17. |
| `hnav_geo_manuscript.tex` | Revision after the internal review, 2026-09-23. `PROVENANCE.md` and `REVIEW_RESPONSE.md` refer to this file's section numbers. |
| `hnav1stone.tex` | Parallel revision, 2026-09-23; the closest ancestor of the submission source. |
| `PROVENANCE.md`, `derive_revision_numbers.py` | Map from manuscript numbers to committed artifacts. Still the provenance record; not yet updated for numbers added after 2026-09-23. |
| `REVIEW_RESPONSE.md` | Response to the internal review of the first draft. |
| `FIGURE_PACKAGE_BRIEF.md` | The brief the figures were drawn from. |

Do not edit the older `.tex` files and do not copy text from them into the submission
source.
