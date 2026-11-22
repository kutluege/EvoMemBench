#!/usr/bin/env python3
"""Human reference labels for ``strict_conflict`` under the rule of 2026-11-23.  [offline]

The first rubric defined ``strict_conflict`` twice: "the two sentences cannot
both be true at the same time", and "update_conflict is yes and the relation
admits a single value at a time". The two differ when a relation can hold
several values but the two values at hand exclude each other (citizenship of
the United States and of ancient Rome). The annotator's decision of 2026-11-23
keeps the first: a pair is a strict conflict when the two sentences cannot both
be true of the entity at the same time, whatever the relation.

    python hnav/labeling/audit_strict_review.py build [--lang tr]
    python hnav/labeling/audit_strict_review.py score --sheet <filled.csv>

``build`` writes a one-question sheet over sentence pairs that already count as
update conflicts: every such pair a human has labelled before (their earlier
``strict_conflict`` answers were given under the ambiguous rubric), and a sample
of pairs no human has seen, at least one per relation. ``score`` reports how
the new answers relate to the earlier human answers and to the model
annotator's labels, which followed the relation-only reading.

What this sheet is and is not:
  * the reference for a second model pass on ``strict_conflict`` only. Half of
    it is meant as worked examples for the guideline, half as a held-out check;
  * one annotator, who also wrote the rule. It gives no agreement figure;
  * no NLI score is shown or stored here. The method under study verifies with
    an NLI model, so labels must not be informed by one;
  * NOT a relabelling. The gold dataset and its ``gold_strict`` are untouched.
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

from hnav.labeling.agreement_stats import largest_remainder  # noqa: E402
from hnav.labeling.audit_compare_laya import read_jsonl  # noqa: E402
from hnav.labeling.audit_disagreement_review import text_key  # noqa: E402
from hnav.labeling.audit_human_pilot import I18N, blind_rows, build_id, render_page  # noqa: E402
from hnav.labeling.audit_human_review import SHEET_COLS, read_sheet  # noqa: E402

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
MODEL_LABELS = DIR / "model_annotation" / "MODEL_LABELS.csv"
PILOT_KEY = DIR / "human_pilot" / "pilot_key.json"
PILOT_SHEET = DIR / "human_pilot" / "pilot_sheet.filled.csv"
REVIEW_KEY = DIR / "disagreement_review" / "disagreement_key.json"
REVIEW_SHEET = DIR / "disagreement_review" / "disagreement_sheet.filled.csv"
OUT = DIR / "strict_review"
STEM = "strict_sheet"
SHEET = OUT / f"{STEM}.csv"
PAGE = OUT / "strict_label.html"
KEY = OUT / "strict_key.json"
README = OUT / "strict_README.md"
OUT_JSON = OUT / "STRICT_REVIEW_SUMMARY.json"
OUT_MD = OUT / "STRICT_REVIEW_SUMMARY.md"

SEED = 20261123
N_NEW = 50
LABEL = "strict_conflict"
COLS = SHEET_COLS[:4] + [LABEL, "notes"]

RUBRIC_STRICT = """# Strict-conflict review — annotator instructions

Every pair in this sheet already counts as an update conflict: both sentences
are about the same entity and the same attribute, and they give two different
values, neither of which contains the other. One question is left.

`strict_conflict`: can the two sentences both be true of that entity at the
same time?

- Answer **yes** (a strict conflict) when they cannot: if one is true, the
  other is definitely false. This holds when the attribute has one value at a
  time (a capital, a birthplace, a head of government). It also holds when the
  attribute can have several values but these two exclude each other, for
  example citizenship of two states that never existed in the same period.
- Answer **no** when both could hold together, however unlikely the
  combination: two languages spoken, two children, two employers, two fields
  of work.

Judge only whether the two values can hold together. Do **not** judge whether
either sentence is true of the real person or thing; many sentences are
counterfactual on purpose. "Confucius is a citizen of the United States" and
"Confucius is a citizen of Canada" are both false in fact, but the two values
can hold together, so the answer is no.

If a pair is hard to decide, use this test: told that the first sentence is
true, would you say the second is definitely false? If so, answer yes.

Answer yes or no for every pair (no blanks, no "unsure"); use `notes` for
anything you want to flag. Do not open `strict_key.json`, your earlier sheets
or anything under `model_annotation/` before you have finished. Hand the
downloaded file over as it is, without re-saving it in a spreadsheet program.
"""

RUBRIC_STRICT_TR = """# Katı çatışma incelemesi — etiketleyici yönergesi

Bu sayfadaki her çift zaten bir güncelleme çatışması sayılıyor: iki cümle de
aynı varlık ve aynı özellik hakkında, ve biri diğerini kapsamayan iki farklı
değer veriyor. Geriye tek soru kalıyor.

`strict_conflict`: iki cümle o varlık için aynı anda doğru olabilir mi?

- Olamıyorsa **evet** (katı çatışma) deyin: biri doğruysa diğeri kesinlikle
  yanlıştır. Özellik aynı anda tek değer alıyorsa böyledir (başkent, doğum
  yeri, hükümet başkanı). Özellik birden çok değer alabildiği halde bu iki
  değer birbirini dışlıyorsa da böyledir; örneğin hiç aynı dönemde var olmamış
  iki devletin vatandaşlığı.
- İkisi birlikte geçerli olabiliyorsa, birliktelik ne kadar olası görünmese de
  **hayır** deyin: konuşulan iki dil, iki çocuk, iki işveren, iki çalışma alanı.

Yalnızca iki değerin birlikte geçerli olup olamayacağına bakın. Cümlelerin
gerçek kişi ya da şey için doğru olup olmadığına **bakmayın**; cümlelerin çoğu
bilerek karşıolgusaldır. "Confucius is a citizen of the United States" ile
"Confucius is a citizen of Canada" gerçekte ikisi de yanlıştır, ama iki değer
birlikte geçerli olabilir; yanıt hayırdır.

Karar vermek zorsa şu sınamayı kullanın: ilk cümlenin doğru olduğu söylense,
ikincinin kesinlikle yanlış olduğunu söyler miydiniz? Öyleyse evet deyin.

Her çift için evet ya da hayır deyin (boş bırakmayın, "emin değilim" yok);
belirtmek istediğiniz her şey için notlar alanını kullanın. Bitirmeden önce
`strict_key.json` dosyasını, önceki sayfalarınızı ve `model_annotation/`
altındaki hiçbir şeyi açmayın. İndirilen dosyayı olduğu gibi verin; bir tablo
programında yeniden kaydetmeyin.
"""


def _i18n() -> dict:
    out = copy.deepcopy(I18N)
    out["en"].update({
        "title": "Strict-conflict review: blind labelling",
        "sub": "Every pair here is already an update conflict. Decide one thing: can the two "
               "sentences both be true of that entity at the same time? Do not check whether "
               "either is true in the real world.",
        "rubric": RUBRIC_STRICT})
    out["en"]["short"] = {LABEL: "Yes: the two sentences cannot both be true of this entity at the "
                                 "same time. No: both could hold together."}
    out["tr"].update({
        "title": "Katı çatışma incelemesi: kör etiketleme",
        "sub": "Buradaki her çift zaten bir güncelleme çatışması. Tek bir şeye karar verin: iki "
               "cümle o varlık için aynı anda doğru olabilir mi? Cümlelerin gerçek dünyada doğru "
               "olup olmadığını kontrol etmeyin. Yanıtlar dosyaya İngilizce (yes/no) kaydedilir.",
        "rubric": RUBRIC_STRICT_TR})
    out["tr"]["short"] = {LABEL: "Evet: iki cümle bu varlık için aynı anda doğru olamaz. "
                                 "Hayır: ikisi birlikte geçerli olabilir."}
    return out


# ── inputs ───────────────────────────────────────────────────────────────────

def relation_of(g: dict) -> str:
    """The parser's template of each sentence; one name when both sentences share it."""
    p = g.get("parser") or {}
    a = ((p.get("fact_a_parsed") or {}).get("relation") or "unparsed").strip(" |")
    b = ((p.get("fact_b_parsed") or {}).get("relation") or "unparsed").strip(" |")
    return a if a == b else " / ".join(sorted((a, b)))


def read_model(path: pathlib.Path) -> dict[str, dict]:
    """pair_id -> {"update": bool, "strict": bool} from the model annotator's labels."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            vals = {}
            for name, col in (("update", "update_conflict"), ("strict", LABEL)):
                v = (r.get(col) or "").strip().lower()
                if v not in ("yes", "no"):
                    raise SystemExit(f"{path}:{i}: {col} is {v!r}, expected yes/no")
                vals[name] = v == "yes"
            out[r["pair_id"]] = vals
    return out


def human_by_text(gold_by_id: dict[str, dict], sources: list[tuple[dict, dict, str]]) -> dict:
    """Earlier human labels per sentence pair.

    ``sources`` holds (key rows, filled sheet, name of the key's pair-id field)
    in the order the sheets were filled. A text labelled twice keeps the later
    ``update`` answer and every ``strict`` answer in ``prior``.
    """
    out: dict[frozenset, dict] = {}
    for key_rows, sheet, field in sources:
        for rid in sorted(key_rows):
            t = text_key(gold_by_id[key_rows[rid][field]])
            rec = out.setdefault(t, {"prior": []})
            rec["update"] = sheet[rid]["update_conflict"]
            rec["prior"].append({"review_id": rid, "strict": sheet[rid][LABEL]})
    return out


# ── selection ────────────────────────────────────────────────────────────────

def select(gold: list[dict], model: dict[str, dict], human: dict, seed: int = SEED,
           n_new: int = N_NEW) -> list[dict]:
    """Sentence pairs that count as update conflicts: all with an earlier human label, plus a sample.

    A text counts as an update conflict by the human answer if there is one,
    otherwise by the model label. The sample of unseen texts takes one per
    relation and shares the remaining seats in proportion to relation size.
    """
    by_text: dict[frozenset, list[dict]] = {}
    for g in gold:
        by_text.setdefault(text_key(g), []).append(g)

    prior, pool = [], {}
    for t, copies in by_text.items():
        copies = sorted(copies, key=lambda g: g["pair_id"])
        labelled = [g for g in copies if g["pair_id"] in model]
        shown = (labelled or copies)[0]
        row = {"shown_pair_id": shown["pair_id"], "subset": shown["subset"],
               "fact_a": shown["fact_a"], "fact_b": shown["fact_b"],
               "relation": relation_of(shown), "pair_ids": [g["pair_id"] for g in copies],
               "model_strict": model[shown["pair_id"]]["strict"] if labelled else None}
        if t in human:
            if human[t]["update"]:
                prior.append(dict(row, stratum="labelled_before", prior=human[t]["prior"]))
        elif labelled and model[shown["pair_id"]]["update"]:
            pool.setdefault(row["relation"], []).append(dict(row, stratum="new", prior=[]))

    rng = random.Random(seed)
    rels = sorted(pool)
    for r in rels:
        pool[r].sort(key=lambda x: x["shown_pair_id"])
        rng.shuffle(pool[r])
    seats = {r: 1 for r in rels} if n_new >= len(rels) else {r: 0 for r in rels}
    spare = n_new - sum(seats.values())
    for r, k in zip(rels, largest_remainder([len(pool[r]) for r in rels], max(spare, 0))):
        seats[r] = min(seats[r] + k, len(pool[r]))
    new = [x for r in rels for x in pool[r][:seats[r]]]

    rows = sorted(prior + new, key=lambda x: x["shown_pair_id"])
    rng.shuffle(rows)                               # review_id order carries no stratum
    for i, r in enumerate(rows):
        r["review_id"] = f"S{i:03d}"
    return rows


# ── build ────────────────────────────────────────────────────────────────────

def write_sheet(path: pathlib.Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def read_strict_sheet(path: pathlib.Path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"{path}: missing columns {missing}")
        rows = {}
        for i, r in enumerate(reader, start=2):
            rid = (r.get("review_id") or "").strip()
            v = (r.get(LABEL) or "").strip().lower()
            if not rid or rid in rows:
                raise SystemExit(f"{path}:{i}: empty or duplicate review_id {rid!r}")
            if v not in ("yes", "no"):
                raise SystemExit(f"{path}:{i}:{LABEL}: expected yes/no, got {r.get(LABEL)!r}")
            rows[rid] = {LABEL: v == "yes", "notes": (r.get("notes") or "").strip()}
    return rows


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
    human = human_by_text(gold_by_id, sources)
    rows = select(gold, model, human, seed=args.seed, n_new=args.n_new)
    if not rows:
        raise SystemExit("no update-conflict pair to review")
    blind = blind_rows(rows)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / KEY.name).write_text(json.dumps({
        "what": "review_id -> sentence pair, its relation, earlier human answers and the model's "
                "strict_conflict under the relation-only rule; not opened before finishing",
        "rule": "strict_conflict = the two sentences cannot both be true of the entity at the "
                "same time (decision of 2026-11-23)",
        "seed": args.seed, "build_id": build_id(blind), "n_rows": len(rows),
        "by_stratum": Counter(r["stratum"] for r in rows),
        "relations_in_new": len({r["relation"] for r in rows if r["stratum"] == "new"}),
        "rows": {r["review_id"]: {k: r[k] for k in ("shown_pair_id", "relation", "stratum", "prior",
                                                    "model_strict", "pair_ids")} for r in rows}},
        indent=1, ensure_ascii=False, default=dict), encoding="utf-8")
    write_sheet(out / SHEET.name, blind)
    (out / PAGE.name).write_text(render_page(blind, args.lang, i18n=_i18n(), file_stem=STEM,
                                             label_cols=[LABEL]), encoding="utf-8")
    (out / README.name).write_text(
        RUBRIC_STRICT + "\n---\n\n## Türkçe çeviri (display translation)\n\n" + RUBRIC_STRICT_TR,
        encoding="utf-8")
    print(f"strict review: {len(rows)} sentence pairs; {dict(Counter(r['stratum'] for r in rows))}")
    print(f"wrote {out / SHEET.name}, {out / PAGE.name}, {out / KEY.name}, {out / README.name}")
    return 0


# ── score ────────────────────────────────────────────────────────────────────

def score_sheet(sheet: dict[str, dict], key: dict[str, dict]) -> dict:
    if set(sheet) != set(key):
        extra, missing = sorted(set(sheet) - set(key)), sorted(set(key) - set(sheet))
        raise SystemExit(f"sheet: review_ids differ from the key (extra {extra[:5]}, "
                         f"missing {missing[:5]})")
    ids = sorted(key)
    yes = {r: sheet[r][LABEL] for r in ids}
    rep: dict = {"n_rows": len(ids), "strict_yes": sum(yes.values()),
                 "by_stratum": {s: {"n": sum(key[r]["stratum"] == s for r in ids),
                                    "strict_yes": sum(yes[r] for r in ids if key[r]["stratum"] == s)}
                                for s in ("labelled_before", "new")}}

    before = [r for r in ids if key[r]["prior"]]
    changed = [r for r in before if key[r]["prior"][-1]["strict"] != yes[r]]
    rep["against_own_earlier_answer"] = {
        "n": len(before), "same": len(before) - len(changed),
        "no_to_yes": sorted(r for r in changed if yes[r]),
        "yes_to_no": sorted(r for r in changed if not yes[r])}

    with_model = [r for r in ids if key[r]["model_strict"] is not None]
    rep["against_model_relation_only_rule"] = {
        "n": len(with_model),
        "same": sum(key[r]["model_strict"] == yes[r] for r in with_model),
        "human_yes_model_no": sorted(r for r in with_model if yes[r] and not key[r]["model_strict"]),
        "human_no_model_yes": sorted(r for r in with_model if not yes[r] and key[r]["model_strict"])}

    by_rel: dict[str, dict] = {}
    for r in ids:
        b = by_rel.setdefault(key[r]["relation"], {"n": 0, "strict_yes": 0})
        b["n"] += 1
        b["strict_yes"] += yes[r]
    rep["by_relation"] = dict(sorted(by_rel.items()))
    rep["relations_with_both_answers"] = sorted(k for k, b in by_rel.items()
                                                if 0 < b["strict_yes"] < b["n"])
    return rep


def render_md(rep: dict) -> str:
    L = ["# Strict-conflict review — summary", ""]
    L.append(f"- sentence pairs: {rep['n_rows']}; strict_conflict yes on {rep['strict_yes']}. "
             "One annotator, who also wrote the rule. The gold dataset is unchanged.")
    for s, b in rep["by_stratum"].items():
        L.append(f"- {s}: {b['strict_yes']} yes of {b['n']}")
    a, m = rep["against_own_earlier_answer"], rep["against_model_relation_only_rule"]
    L.append(f"- against the annotator's own earlier answer (ambiguous rubric): {a['same']} of "
             f"{a['n']} the same; no to yes {len(a['no_to_yes'])}, yes to no {len(a['yes_to_no'])}")
    L.append(f"- against the model's labels (relation-only rule): {m['same']} of {m['n']} the same; "
             f"human yes / model no {len(m['human_yes_model_no'])}, human no / model yes "
             f"{len(m['human_no_model_yes'])}")
    L.append("")
    L.append("## By relation")
    L.append("")
    L.append("| relation | n | strict yes |")
    L.append("| --- | ---: | ---: |")
    for k, b in rep["by_relation"].items():
        L.append(f"| {k} | {b['n']} | {b['strict_yes']} |")
    L.append("")
    L.append(f"Relations with both answers (the value pair decides, not the relation): "
             f"{len(rep['relations_with_both_answers'])}.")
    L.append("")
    return "\n".join(L)


def score(args) -> int:
    key_doc = json.loads(pathlib.Path(args.key).read_text(encoding="utf-8"))
    rep = score_sheet(read_strict_sheet(pathlib.Path(args.sheet)), key_doc["rows"])
    rep["build_id"] = key_doc.get("build_id")
    pathlib.Path(args.out_json).write_text(json.dumps(rep, indent=1, ensure_ascii=False),
                                           encoding="utf-8")
    pathlib.Path(args.out_md).write_text(render_md(rep), encoding="utf-8")
    print(f"scored {rep['n_rows']} sentence pairs; wrote {args.out_md}, {args.out_json}")
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

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
    b.add_argument("--out-dir", default=str(OUT))
    b.add_argument("--seed", type=int, default=SEED)
    b.add_argument("--n-new", type=int, default=N_NEW)
    b.add_argument("--lang", choices=sorted(I18N), default="en",
                   help="language the labelling page opens in (display only)")
    b.set_defaults(func=build)
    s = sub.add_parser("score")
    s.add_argument("--key", default=str(KEY))
    s.add_argument("--sheet", required=True)
    s.add_argument("--out-json", default=str(OUT_JSON))
    s.add_argument("--out-md", default=str(OUT_MD))
    s.set_defaults(func=score)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
