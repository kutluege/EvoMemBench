#!/usr/bin/env python3
"""Blind human review of the pairs on which the gold label and the model annotator differ.  [offline]

After the model annotator pass (``audit_model_annotator.py``) every gold pair
carries two ``update_conflict`` answers: the dataset's ``gold_update`` and the
model's label. They differ on a few dozen pairs. This script puts exactly
those pairs in front of a human, without saying which source said what.

    python hnav/labeling/audit_disagreement_review.py build [--lang tr]
    python hnav/labeling/audit_disagreement_review.py score --sheet <filled.csv> [--sheet-b <filled.csv>]

``build`` writes a blind CSV sheet, the same self-contained labelling page as
the pilot (English or Turkish display, English record), the instructions and a
key. ``score`` counts, pair by pair, whether the annotator's ``update_conflict``
matches the gold label or the model label, with Wilson intervals, and gives
human-human agreement if a second sheet is supplied.

One row per sentence pair, not per pair id. The subsets share facts, so the
same two sentences occur under several pair ids; a human is shown them once and
the answer is applied to every pair id with that text. The key lists all of
them, including copies on which gold and model agree, because identical text
can sit in different tiers (the judge was called once per pair id).

What this review is and is not (design of 2026-11-23):
  * an adjudication of the disputed pairs only. It says nothing about the pairs
    on which gold and model agree; both can be wrong there, and that needs a
    random sample of agreement pairs, which this sheet does not contain;
  * the model was calibrated on the pilot annotator's reading, and some of
    these sentence pairs were labelled in the pilot and shown to the model as
    examples. ``score`` therefore reports pilot-seen and new texts separately,
    and a review by the pilot annotator is not independent of the model;
  * NOT a relabelling. The gold dataset and its frozen tier counts are never
    touched.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import pathlib
import random
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.labeling.agreement_stats import agreement, cohen_kappa, table2x2  # noqa: E402
from hnav.labeling.audit_compare_laya import read_jsonl  # noqa: E402
from hnav.labeling.audit_human_pilot import (  # noqa: E402
    I18N, RUBRIC_TR, _f, _rate, blind_rows, build_id, render_page)
from hnav.labeling.audit_human_review import (  # noqa: E402
    LABEL_COLS, RUBRIC, read_sheet, write_sheet)
from hnav.labeling.audit_model_annotator import rubric_violations  # noqa: E402

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
MODEL_LABELS = DIR / "model_annotation" / "MODEL_LABELS.csv"
PILOT_KEY = DIR / "human_pilot" / "pilot_key.json"
OUT = DIR / "disagreement_review"
STEM = "disagreement_sheet"
SHEET = OUT / f"{STEM}.csv"
PAGE = OUT / "disagreement_label.html"
KEY = OUT / "disagreement_key.json"
README = OUT / "disagreement_README.md"
OUT_JSON = OUT / "DISAGREEMENT_SUMMARY.json"
OUT_MD = OUT / "DISAGREEMENT_SUMMARY.md"

SEED = 20261123
TIERS = ["core", "update_only_fork", "rejected", "discovered_unverified", "negative"]

NOTE = """
---

## Disagreement review sheet

Every sentence pair in this sheet has received two different `update_conflict`
answers from two earlier label sources. The sheet does not say which source
said what, and about half of the pairs go each way. Label each pair on its own
reading, exactly as the instructions above say. Each sentence pair appears
once, even if it occurs in several subsets.

Who should fill it: preferably someone who did not label the pilot. One of the
two sources was calibrated on the pilot annotator's labels, so that
annotator's review is not independent of it.

Two ways to fill it:

1. Open `disagreement_label.html` in a browser, answer every question for
   every pair, and press "Download CSV". Progress is kept in the browser.
2. Or fill `disagreement_sheet.csv` directly and save it as comma-separated
   UTF-8.

Hand the downloaded file over as it is. Opening and re-saving it in a
spreadsheet program can wrap every row in extra quotes, which the scorer
rejects.

Then score it:

    python hnav/labeling/audit_disagreement_review.py score --sheet <the filled file>

Do not open `disagreement_key.json`, the gold dataset or anything under
`model_annotation/` before you have finished.
"""

NOTE_TR = """
---

## Ayrışma incelemesi sayfası (çeviri)

Bu sayfadaki her cümle çifti, daha önceki iki etiket kaynağından iki farklı
`update_conflict` yanıtı almıştır. Sayfa hangi kaynağın ne dediğini söylemez ve
çiftlerin yaklaşık yarısı bir yönde, yarısı öbür yöndedir. Her çifti yukarıdaki
yönergeye göre, kendi okumanızla etiketleyin. Bir cümle çifti birden çok alt
kümede geçse bile bir kez gösterilir.

Kim doldurmalı: tercihen pilotu etiketlememiş biri. İki kaynaktan biri pilot
etiketleyicinin etiketlerine göre kalibre edildi; bu yüzden o etiketleyicinin
incelemesi o kaynaktan bağımsız değildir.

İndirilen dosyayı olduğu gibi verin. Bir tablo programında açıp yeniden
kaydetmek her satırı fazladan tırnağa sarabilir; puanlayıcı bunu kabul etmez.

Bitirmeden önce `disagreement_key.json` dosyasını, altın veri setini ve
`model_annotation/` altındaki hiçbir şeyi açmayın.
"""


def _i18n() -> dict:
    """The pilot page's texts with this review's titles and key file name."""
    out = copy.deepcopy(I18N)
    for lang, title, rubric, old in (
            ("en", "Disagreement review: blind labelling", RUBRIC, "human_review_key.json"),
            ("tr", "Ayrışma incelemesi: kör etiketleme", RUBRIC_TR, "pilot_key.json")):
        if old not in rubric:
            raise SystemExit(f"the {lang} rubric no longer names {old}; update _i18n")
        out[lang]["title"] = title
        out[lang]["rubric"] = rubric.replace(old, KEY.name)
    return out


# ── inputs ───────────────────────────────────────────────────────────────────

def read_model_update(path: pathlib.Path) -> dict[str, bool]:
    """pair_id -> the model annotator's ``update_conflict``."""
    out: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            v = (r.get("update_conflict") or "").strip().lower()
            if v not in ("yes", "no"):
                raise SystemExit(f"{path}:{i}: update_conflict is {v!r}, expected yes/no")
            if r["pair_id"] in out:
                raise SystemExit(f"{path}:{i}: duplicate pair_id {r['pair_id']}")
            out[r["pair_id"]] = v == "yes"
    return out


def read_pilot_ids(path: pathlib.Path) -> dict[str, str]:
    """pair_id -> pilot review_id for the pairs a human labelled in the pilot."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {v["pair_id"]: rid for rid, v in doc["rows"].items()}


# ── selection ────────────────────────────────────────────────────────────────

def text_key(g: dict) -> frozenset:
    return frozenset((g["fact_a"], g["fact_b"]))


def select(gold: list[dict], model_update: dict[str, bool], pilot_ids: dict[str, str],
           seed: int = SEED) -> list[dict]:
    """One row per distinct sentence pair on which gold and model differ for some pair id.

    A row carries the blind columns (taken from the disputed pair id that sorts
    first) and ``pairs``: every gold pair id with that text, disputed or not.
    """
    by_text: dict[frozenset, list[dict]] = {}
    for g in gold:
        by_text.setdefault(text_key(g), []).append(g)

    rows = []
    for copies in by_text.values():
        copies = sorted(copies, key=lambda g: g["pair_id"])
        pairs = []
        for g in copies:
            m = model_update.get(g["pair_id"])
            pairs.append({"pair_id": g["pair_id"], "subset": g["subset"], "tier": g["tier"],
                          "in_eval_set": bool(g.get("in_eval_set")),
                          "gold_update": bool(g["gold_update"]), "model_update": m,
                          "disputed": m is not None and m != bool(g["gold_update"]),
                          "pilot_review_id": pilot_ids.get(g["pair_id"])})
        if not any(p["disputed"] for p in pairs):
            continue
        shown = next(g for g, p in zip(copies, pairs) if p["disputed"])
        rows.append({"shown_pair_id": shown["pair_id"], "subset": shown["subset"],
                     "fact_a": shown["fact_a"], "fact_b": shown["fact_b"], "pairs": pairs,
                     "seen_in_pilot": sorted(p["pilot_review_id"] for p in pairs
                                             if p["pilot_review_id"])})
    rows.sort(key=lambda r: r["shown_pair_id"])
    random.Random(seed).shuffle(rows)               # review_id order carries no tier information
    for i, r in enumerate(rows):
        r["review_id"] = f"D{i:03d}"
    return rows


def disputed_pairs(rows: list[dict]) -> list[dict]:
    return [p for r in rows for p in r["pairs"] if p["disputed"]]


# ── build ────────────────────────────────────────────────────────────────────

def build(args) -> int:
    gold = list(read_jsonl(pathlib.Path(args.gold)))
    model_update = read_model_update(pathlib.Path(args.model_labels))
    unknown = sorted(set(model_update) - {g["pair_id"] for g in gold})
    if unknown:
        raise SystemExit(f"{len(unknown)} model-labelled pairs are not in the gold dataset, "
                         f"e.g. {unknown[:3]}")
    pilot_key = pathlib.Path(args.pilot_key)
    pilot_ids = read_pilot_ids(pilot_key) if pilot_key.exists() else {}
    rows = select(gold, model_update, pilot_ids, seed=args.seed)
    if not rows:
        raise SystemExit("gold and model agree on every labelled pair; nothing to review")
    blind = blind_rows(rows)
    dis = disputed_pairs(rows)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / KEY.name).write_text(json.dumps({
        "what": "review_id -> sentence pair and every gold pair id with that text; "
                "the annotator does not open this file before finishing",
        "seed": args.seed, "build_id": build_id(blind),
        "n_rows": len(rows), "n_disputed_pairs": len(dis),
        "disputed_by_tier": Counter(p["tier"] for p in dis),
        "disputed_in_eval_set": sum(p["in_eval_set"] for p in dis),
        "disputed_gold_yes_model_no": sum(p["gold_update"] for p in dis),
        "disputed_gold_no_model_yes": sum(not p["gold_update"] for p in dis),
        "rows_seen_in_pilot": sum(bool(r["seen_in_pilot"]) for r in rows),
        "rows": {r["review_id"]: {"shown_pair_id": r["shown_pair_id"],
                                  "seen_in_pilot": r["seen_in_pilot"], "pairs": r["pairs"]}
                 for r in rows}}, indent=1, ensure_ascii=False, default=dict), encoding="utf-8")
    write_sheet(out / SHEET.name, blind)
    (out / PAGE.name).write_text(render_page(blind, args.lang, i18n=_i18n(), file_stem=STEM),
                                 encoding="utf-8")
    (out / README.name).write_text(
        RUBRIC.replace("human_review_key.json", KEY.name) + NOTE
        + "\n---\n\n## Türkçe çeviri (display translation)\n\n"
        + RUBRIC_TR.replace("pilot_key.json", KEY.name) + NOTE_TR, encoding="utf-8")
    print(f"disagreement review: {len(rows)} sentence pairs covering {len(dis)} disputed pair ids; "
          f"by tier {dict(Counter(p['tier'] for p in dis))}")
    print(f"wrote {out / SHEET.name}, {out / PAGE.name}, {out / KEY.name}, {out / README.name}")
    return 0


# ── score ────────────────────────────────────────────────────────────────────

def _sides(sel: list[tuple[str, dict]], sheet: dict[str, dict]) -> dict:
    """``sel`` holds (review_id, disputed pair). Gold and model differ, so the human matches one."""
    k = sum(sheet[rid]["update_conflict"] == p["gold_update"] for rid, p in sel)
    return {"n": len(sel), "sides_with_gold": _rate(k, len(sel)),
            "sides_with_model": _rate(len(sel) - k, len(sel))}


def score_sheet(sheet: dict[str, dict], key: dict[str, dict],
                sheet_b: dict[str, dict] | None = None) -> dict:
    for name, sh in (("sheet", sheet), ("sheet-b", sheet_b)):
        if sh is not None and set(sh) != set(key):
            extra, missing = sorted(set(sh) - set(key)), sorted(set(key) - set(sh))
            raise SystemExit(f"{name}: review_ids differ from the key "
                             f"(extra {extra[:5]}, missing {missing[:5]})")
    ids = sorted(key)
    dis = [(rid, p) for rid in ids for p in key[rid]["pairs"] if p["disputed"]]
    for rid, p in dis:
        if p["model_update"] == p["gold_update"]:
            raise SystemExit(f"{p['pair_id']}: marked disputed but gold and model agree")
    seen = {rid for rid in ids if key[rid]["seen_in_pilot"]}

    rep: dict = {"n_rows": len(ids), "n_disputed_pairs": len(dis),
                 "annotators": 2 if sheet_b else 1,
                 "rows_seen_in_pilot": len(seen),
                 "human_update_yes_rows": sum(sheet[r]["update_conflict"] for r in ids),
                 "human_strict_yes_rows": sum(sheet[r]["strict_conflict"] for r in ids),
                 "rows_departing_from_rubric": sorted(r for r in ids if rubric_violations(sheet[r]))}

    groups = [("all disputed pairs", dis),
              ("in evaluation set", [x for x in dis if x[1]["in_eval_set"]]),
              ("outside evaluation set", [x for x in dis if not x[1]["in_eval_set"]]),
              ("gold yes, model no", [x for x in dis if x[1]["gold_update"]]),
              ("gold no, model yes", [x for x in dis if not x[1]["gold_update"]]),
              ("text new to the pilot", [x for x in dis if x[0] not in seen]),
              ("text labelled in the pilot", [x for x in dis if x[0] in seen])]
    groups += [(t, [x for x in dis if x[1]["tier"] == t]) for t in TIERS
               if any(x[1]["tier"] == t for x in dis)]
    rep["update_conflict_by_group"] = {name: _sides(sel, sheet) for name, sel in groups}

    # identical text under pair ids that carry opposite gold labels
    mixed = [r for r in ids if len({p["gold_update"] for p in key[r]["pairs"]}) > 1]
    rep["rows_with_opposite_gold_labels"] = {
        "n": len(mixed), "human_update_yes": sum(sheet[r]["update_conflict"] for r in mixed),
        "review_ids": mixed}

    if sheet_b:
        hh = {}
        for c in LABEL_COLS:
            x = [sheet[r][c] for r in ids]
            y = [sheet_b[r][c] for r in ids]
            hh[c] = {"n": len(ids), "agreement": agreement(x, y), "kappa": cohen_kappa(x, y),
                     "table_A_B": table2x2(x, y)}
        rep["human_human"] = hh
        both = [(rid, p) for rid, p in dis
                if sheet[rid]["update_conflict"] == sheet_b[rid]["update_conflict"]]
        rep["both_annotators"] = {"n_disputed_pairs": len(dis), "annotators_agree": len(both),
                                  "annotators_split": len(dis) - len(both),
                                  "where_they_agree": _sides(both, sheet)}
    return rep


def render_md(rep: dict) -> str:
    L = ["# Human review of gold-model disagreements — summary", ""]
    L.append(f"- sentence pairs reviewed: {rep['n_rows']}, covering {rep['n_disputed_pairs']} "
             f"disputed pair ids; annotators: {rep['annotators']}")
    L.append(f"- annotator A: update_conflict yes on {rep['human_update_yes_rows']} sentence pairs, "
             f"strict_conflict yes on {rep['human_strict_yes_rows']}; rows departing from the "
             f"rubric's derivation rules: {len(rep['rows_departing_from_rubric'])}")
    L.append(f"- {rep['rows_seen_in_pilot']} of the sentence pairs were labelled in the pilot and "
             "shown to the model as examples; on those the model label repeats a human label.")
    L.append("- Only disputed pairs were reviewed. Nothing here bears on the pairs on which gold "
             "and model agree. The gold dataset is unchanged.")
    L.append("")
    L.append("## update_conflict: whom annotator A sides with (pair ids)")
    L.append("")
    L.append("| group | n | sides with gold | Wilson 95 % | sides with model | Wilson 95 % |")
    L.append("| --- | ---: | ---: | --- | ---: | --- |")
    for name, b in rep["update_conflict_by_group"].items():
        g, m = b["sides_with_gold"], b["sides_with_model"]
        L.append(f"| {name} | {b['n']} | {g['k']} | {_f(g['wilson95'])} | {m['k']} | "
                 f"{_f(m['wilson95'])} |")
    L.append("")
    L.append("Gold and model differ on every pair here, so the two counts sum to n. Pair ids "
             "that share a sentence pair share one human answer and are not independent.")
    L.append("")
    mx = rep["rows_with_opposite_gold_labels"]
    L.append(f"Sentence pairs whose pair ids carry opposite gold labels: {mx['n']} "
             f"(annotator A says update_conflict on {mx['human_update_yes']}).")
    L.append("")
    if "human_human" in rep:
        L.append("## Human–human agreement (independent, blind; sentence pairs)")
        L.append("")
        L.append("| field | n | agreement | κ |")
        L.append("| --- | ---: | ---: | ---: |")
        for c, s in rep["human_human"].items():
            L.append(f"| {c} | {s['n']} | {_f(s['agreement'])} | {_f(s['kappa'])} |")
        L.append("")
        b = rep["both_annotators"]
        w = b["where_they_agree"]
        L.append(f"On update_conflict the two annotators give the same answer for "
                 f"{b['annotators_agree']} of {b['n_disputed_pairs']} disputed pair ids; there, "
                 f"{w['sides_with_gold']['k']} side with gold and {w['sides_with_model']['k']} "
                 f"with the model.")
        L.append("")
    return "\n".join(L)


def score(args) -> int:
    key_doc = json.loads(pathlib.Path(args.key).read_text(encoding="utf-8"))
    sheet = read_sheet(pathlib.Path(args.sheet))
    sheet_b = read_sheet(pathlib.Path(args.sheet_b)) if args.sheet_b else None
    rep = score_sheet(sheet, key_doc["rows"], sheet_b)
    rep["build_id"] = key_doc.get("build_id")
    rep["seed"] = key_doc.get("seed")
    pathlib.Path(args.out_json).write_text(json.dumps(rep, indent=1, default=dict), encoding="utf-8")
    pathlib.Path(args.out_md).write_text(render_md(rep), encoding="utf-8")
    print(f"scored {rep['n_rows']} sentence pairs ({rep['n_disputed_pairs']} disputed pair ids); "
          f"wrote {args.out_md}, {args.out_json}")
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--gold", default=str(GOLD))
    b.add_argument("--model-labels", default=str(MODEL_LABELS))
    b.add_argument("--pilot-key", default=str(PILOT_KEY))
    b.add_argument("--out-dir", default=str(OUT))
    b.add_argument("--seed", type=int, default=SEED)
    b.add_argument("--lang", choices=sorted(I18N), default="en",
                   help="language the labelling page opens in (display only)")
    b.set_defaults(func=build)
    s = sub.add_parser("score")
    s.add_argument("--key", default=str(KEY))
    s.add_argument("--sheet", required=True)
    s.add_argument("--sheet-b", default=None)
    s.add_argument("--out-json", default=str(OUT_JSON))
    s.add_argument("--out-md", default=str(OUT_MD))
    s.set_defaults(func=score)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
