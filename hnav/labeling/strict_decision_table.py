#!/usr/bin/env python3
"""Decision table for ``strict_conflict``: stage 0 of the annotation protocol.  [offline]

``strict_conflict`` is decided by rule, not by labelling pairs one at a time:
the authors say, relation by relation, whether the relation holds one value at
a time, and whether two values of a multi-valued relation that exclude each
other count as a strict conflict. This script prepares the table they fill.

    python hnav/labeling/strict_decision_table.py build

``build`` writes ``decision_table.csv`` (one row per relation, an empty
``decision`` column) and ``DECISION_TABLE.md`` (the same rows grouped by the
argument that would make a relation single-valued, with the evidence beside
each). The evidence is: how many update-conflict pairs the relation has, what
the model annotator answered under the first guideline's table, and the
annotator's own earlier answers.

The relations are grouped so that one argument gets one answer. The audit of
23 November found the same argument ("more than one is conceivable") answered
both ways across relations; deciding by group prevents that. A group decision
can be overridden for a single relation, with a reason.

Nothing here labels a pair. Applying the filled table is a separate step.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.labeling.audit_compare_laya import read_jsonl  # noqa: E402
from hnav.labeling.audit_disagreement_review import text_key  # noqa: E402
from hnav.labeling.audit_human_review import read_sheet  # noqa: E402
from hnav.labeling.audit_strict_review import (  # noqa: E402
    LABEL, PILOT_KEY, PILOT_SHEET, REVIEW_KEY, REVIEW_SHEET, read_model, read_strict_sheet,
    relation_of)

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
MODEL_LABELS = DIR / "model_annotation" / "MODEL_LABELS.csv"
STRICT_KEY = DIR / "strict_review" / "strict_key.json"
STRICT_SHEET = DIR / "strict_review" / "strict_sheet.filled.csv"
OUT = DIR / "strict_review"
TABLE = OUT / "decision_table.csv"
VIEW = OUT / "DECISION_TABLE.md"

# Rows of the 23 November strict sheet that the annotator labelled himself
# (his statement of that day). The other 91 rows were filled by a language
# model and are evidence of nothing.
OWN_STRICT_ROWS = [f"S{i:03d}" for i in range(12)]

COLS = ["relation", "group", "pair_ids", "sentence_pairs", "model_first_guideline",
        "own_answers_yes", "own_answers_no", "own_answer_ids", "decision", "reason"]

GROUPS = {
    "A": ("One by definition",
          "The relation names a single event or a single origin: nothing can be born, die or be "
          "founded in two places, and \"original\" picks one. If yes, two different values "
          "cannot both be true."),
    "B": ("One holder or one seat at a time",
          "An office, a seat or a status that is normally held by one value at a time, although "
          "a second one is conceivable (co-chief executives, two capitals, dual headquarters, "
          "polygamy, a country on two continents). The whole group needs one answer to the "
          "question: does \"conceivable\" make it multi-valued?"),
    "C": ("Several values are normal",
          "A person has several languages, citizenships, employers, children; a work has several "
          "authors or performers. Two different values can both be true, so the relation alone "
          "never makes a strict conflict. Decision D4 says what happens when the two particular "
          "values exclude each other."),
    "P": ("Two wordings of one relation",
          "The two sentences use different templates for the same attribute. They follow the "
          "decision of the relation they paraphrase; the only question is whether the two "
          "wordings are the same relation at all, which rubric v2 settles."),
}

RELATION_GROUP = {
    "was born in the city of": "A",
    "died in the city of": "A",
    "was founded in the city of": "A",
    "was created in the country of": "A",
    "The original language of | is": "A",
    "The origianl broadcaster of | is": "A",
    "The name of the current head of state in | is": "B",
    "The name of the current head of the | government is": "B",
    "The Governor of | is": "B",
    "The chief executive officer of | is": "B",
    "The chairperson of | is": "B",
    "The head coach of | is": "B",
    "The director of | is": "B",
    "The capital of | is": "B",
    "The headquarters of | is located in the city of": "B",
    "is married to": "B",
    "is located in the continent of": "B",
    "unparsed": "B",                       # office titles: Prime Minister, President, Attorney General
    "is a citizen of": "C",
    "speaks the language of": "C",
    "is associated with the sport of": "C",
    "plays the position of": "C",
    "is affiliated with the religion of": "C",
    "The type of music that | plays is": "C",
    "works in the field of": "C",
    "is famous for": "C",
    "is employed by": "C",
    "The univeristy where | was educated is": "C",
    "worked in the city of": "C",
    "'s child is": "C",
    "The author of | is": "C",
    "was performed by": "C",
    "was created by": "C",
    "was founded by": "C",
    "was developed by": "C",
    "The company that produced | is": "C",
    "The official language of | is": "C",
    "was written in the language of": "C",
}


# The six rule decisions. They head the CSV as rows of group "D", so that the
# filled file carries the whole rule.
DECISIONS = [
    ("D1", "Group A (one by definition): strict conflict?"),
    ("D2", "Group B (one holder or seat at a time): strict conflict, although a second holder is "
           "conceivable? One answer for the group."),
    ("D3", "Group C (several values are normal): the relation alone is never a strict conflict. "
           "Confirm."),
    ("D4", "In group C, are two values that exclude each other a strict conflict (for example "
           "citizenship of two states that never existed in the same period)? If yes, these "
           "pairs need a per-pair pass; if no, every group C pair is `no`."),
    ("D5", "If D4 is yes: does it apply only when the two values never existed in the same "
           "period (answer `period`), or also to values that exclude each other for another "
           "reason, such as two religions or two sports positions (answer `any`)?"),
    ("D6", "If D2 is no: does D4 then also apply to group B (two spouses who never lived at the "
           "same time)?"),
]

DISPLAY = {"unparsed": "office titles the parser does not read (Prime Minister of, President "
                       "of, Attorney General)"}


def group_of(relation: str) -> str:
    if " / " in relation:
        return "P"
    return RELATION_GROUP.get(relation, "?")


def _yn(b) -> str:
    return "" if b is None else ("yes" if b else "no")


# ── evidence ─────────────────────────────────────────────────────────────────

def own_answers(gold_by_id: dict[str, dict], sources: list[tuple[dict, dict, str]],
                strict_key: dict | None, strict_sheet: dict | None,
                own_rows: list[str]) -> dict[frozenset, list[tuple[str, bool]]]:
    """The annotator's own ``strict_conflict`` answers per sentence pair, in the order given.

    ``sources`` are six-field sheets as (key rows, filled sheet, pair-id field);
    only rows he called an update conflict count. From the strict sheet only
    ``own_rows`` are read.
    """
    out: dict[frozenset, list[tuple[str, bool]]] = {}
    for key_rows, sheet, field in sources:
        for rid in sorted(key_rows):
            if sheet[rid]["update_conflict"]:
                t = text_key(gold_by_id[key_rows[rid][field]])
                out.setdefault(t, []).append((rid, sheet[rid][LABEL]))
    if strict_key and strict_sheet:
        for rid in own_rows:
            if rid in strict_key and rid in strict_sheet:
                t = text_key(gold_by_id[strict_key[rid]["shown_pair_id"]])
                out.setdefault(t, []).append((rid, strict_sheet[rid][LABEL]))
    return out


def build_rows(gold: list[dict], model: dict[str, dict],
               own: dict[frozenset, list[tuple[str, bool]]]) -> list[dict]:
    """One row per relation that occurs among update conflicts or among the annotator's answers."""
    by_text: dict[frozenset, list[dict]] = {}
    for g in gold:
        by_text.setdefault(text_key(g), []).append(g)

    acc: dict[str, dict] = {}
    for t, copies in by_text.items():
        copies = sorted(copies, key=lambda g: g["pair_id"])
        rel = relation_of(copies[0])
        ids = [g["pair_id"] for g in copies if g["pair_id"] in model and model[g["pair_id"]]["update"]]
        if not ids and t not in own:
            continue
        a = acc.setdefault(rel, {"pair_ids": 0, "sentence_pairs": 0, "model": Counter(),
                                 "yes": 0, "no": 0, "ids": []})
        if ids:
            a["pair_ids"] += len(ids)
            a["sentence_pairs"] += 1
            a["model"].update(_yn(model[p]["strict"]) for p in ids)
        for rid, ans in own.get(t, []):
            a["yes" if ans else "no"] += 1
            a["ids"].append(f"{rid}{'+' if ans else '-'}")

    rows = []
    for rel, a in acc.items():
        m = a["model"]
        first = "" if not m else ("yes" if not m["no"] else "no" if not m["yes"]
                                  else f"mixed ({m['yes']} yes, {m['no']} no)")
        rows.append({"relation": rel, "group": group_of(rel), "pair_ids": a["pair_ids"],
                     "sentence_pairs": a["sentence_pairs"], "model_first_guideline": first,
                     "own_answers_yes": a["yes"], "own_answers_no": a["no"],
                     "own_answer_ids": " ".join(sorted(a["ids"])), "decision": "", "reason": ""})
    rows.sort(key=lambda r: ("ABCP?".index(r["group"]), -r["pair_ids"], r["relation"]))
    return rows


# ── output ───────────────────────────────────────────────────────────────────

def render_md(rows: list[dict]) -> str:
    L = ["# Decision table for `strict_conflict` — to be filled by both authors", ""]
    L.append("`strict_conflict` means: the two sentences cannot both be true of the entity at the "
             "same time. It is asked only of pairs that are already update conflicts (same "
             "entity, same attribute, two different values, neither containing the other).")
    L.append("")
    L.append("Fill the `decision` column of `decision_table.csv` with `yes` or `no`. A group "
             "decision covers every relation of the group; to make an exception, write the other "
             "answer on that relation's row with a reason. Counts are update-conflict pairs under "
             "the model annotator's labels. \"First guideline\" is what the model answered under "
             "the table of 22 November, which is not final. \"Own answers\" are the first "
             "author's earlier answers: `P` rows from the seed sheet and `D` rows from the "
             "disagreement review, both under the ambiguous first rubric, and `S` rows from the "
             "strict sheet; `+` is yes, `-` is no.")
    L.append("")
    L.append("## Decisions")
    L.append("")
    L.append("The first six rows of the CSV are these decisions; the relation rows follow.")
    L.append("")
    L.append("| | Decision | Answer |")
    L.append("| --- | --- | --- |")
    for code, text in DECISIONS:
        L.append(f"| {code} | {text} | |")
    L.append("")
    for g, (title, why) in GROUPS.items():
        sel = [r for r in rows if r["group"] == g]
        if not sel:
            continue
        L.append(f"## Group {g}: {title}")
        L.append("")
        L.append(why)
        L.append("")
        L.append("| relation | pair ids | sentence pairs | first guideline | own answers | decision |")
        L.append("| --- | ---: | ---: | --- | --- | --- |")
        for r in sel:
            own = f"{r['own_answers_yes']} yes, {r['own_answers_no']} no: {r['own_answer_ids']}" \
                if r["own_answer_ids"] else "—"
            name = DISPLAY.get(r["relation"], r["relation"]).replace("|", "…")
            L.append(f"| {name} | {r['pair_ids']} | {r['sentence_pairs']} | "
                     f"{r['model_first_guideline'] or '—'} | {own} | |")
        L.append(f"| **total** | {sum(r['pair_ids'] for r in sel)} | "
                 f"{sum(r['sentence_pairs'] for r in sel)} | | | |")
        L.append("")
    stray = [r["relation"] for r in rows if r["group"] == "?"]
    if stray:
        L.append(f"Relations without a group (assign one in `RELATION_GROUP`): {stray}")
        L.append("")
    return "\n".join(L)


def build(args) -> int:
    gold = list(read_jsonl(pathlib.Path(args.gold)))
    gold_by_id = {g["pair_id"]: g for g in gold}
    model = read_model(pathlib.Path(args.model_labels))
    sources = []
    for key_path, sheet_path, field in ((args.pilot_key, args.pilot_sheet, "pair_id"),
                                        (args.review_key, args.review_sheet, "shown_pair_id")):
        kp, sp = pathlib.Path(key_path), pathlib.Path(sheet_path)
        if kp.exists() and sp.exists():
            sources.append((json.loads(kp.read_text(encoding="utf-8"))["rows"], read_sheet(sp), field))
    sk, ss = pathlib.Path(args.strict_key), pathlib.Path(args.strict_sheet)
    strict_key = json.loads(sk.read_text(encoding="utf-8"))["rows"] if sk.exists() else None
    strict_sheet = read_strict_sheet(ss) if ss.exists() else None
    rows = build_rows(gold, model, own_answers(gold_by_id, sources, strict_key, strict_sheet,
                                               OWN_STRICT_ROWS))
    stray = [r["relation"] for r in rows if r["group"] == "?"]
    if stray:
        raise SystemExit(f"relations without a group: {stray}; add them to RELATION_GROUP")
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / TABLE.name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows({"relation": f"{code}: {text}", "group": "D"} for code, text in DECISIONS)
        w.writerows(rows)
    (out / VIEW.name).write_text(render_md(rows), encoding="utf-8")
    by = Counter(r["group"] for r in rows)
    print(f"decision table: {len(rows)} relations {dict(by)}; "
          f"{sum(r['pair_ids'] for r in rows)} update-conflict pair ids, "
          f"{sum(r['sentence_pairs'] for r in rows)} sentence pairs")
    print(f"wrote {out / TABLE.name}, {out / VIEW.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--gold", default=str(GOLD))
    b.add_argument("--model-labels", default=str(MODEL_LABELS))
    b.add_argument("--pilot-key", default=str(PILOT_KEY))
    b.add_argument("--pilot-sheet", default=str(PILOT_SHEET))
    b.add_argument("--review-key", default=str(REVIEW_KEY))
    b.add_argument("--review-sheet", default=str(REVIEW_SHEET))
    b.add_argument("--strict-key", default=str(STRICT_KEY))
    b.add_argument("--strict-sheet", default=str(STRICT_SHEET))
    b.add_argument("--out-dir", default=str(OUT))
    b.set_defaults(func=build)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
