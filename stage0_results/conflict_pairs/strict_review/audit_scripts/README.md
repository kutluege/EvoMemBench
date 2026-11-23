# Scripts of the audit of the `strict_conflict` sheet, 23 November 2026

Written and run by a separate Claude Opus 5.5 subagent that audited
`../strict_sheet.filled.csv`. Kept as run, without tests, so that the numbers in
`paper/journal/YAPILANLAR.md` (entry "`strict_conflict` referans sayfası geldi") can be
recomputed: `python -I analyse.py <repo>` writes `rel_stats.json` next to itself, then
`python -I groups.py`. The grouping of relations inside `groups.py` is the auditor's judgement,
not a decision of the authors; the authors' grouping is `../DECISION_TABLE.md`.
