#!/usr/bin/env python3
"""Independent audit of the pair labels by two annotators: stage 5 of the annotation protocol.  [offline]

    python hnav/labeling/audit_validation.py build --rubric-en <file> --rubric-tr <file> [--dry-run]
    python hnav/labeling/audit_validation.py score --sheet-a <filled.csv> [--sheet-b <filled.csv>]

``build`` draws the sample of ``paper/PROTOCOL_ANNOTATION.md`` and writes one
blind sheet, a labelling page, and a key. Both annotators fill the same sheet,
each alone. One row is one distinct sentence pair:

    disputed        every sentence pair on which the model's update_conflict
                    differs from the released label (the rows of stage 4)
    core            pairs all sources call an update conflict
    lookalike       evaluation-set negatives at cosine >= 0.94, all sources "no"
    update_only     the released label and the model say yes, GPT-5 mini said no
    quarantined     GPT-5 mini said yes, the released label and the model say no
    test_set        pairs of the new test set, if a file of them is given

Outside ``disputed`` a sentence pair is eligible only if the model agrees with
the released label on every pair id that carries its text, and no human has
labelled it before. The page asks two questions, update_conflict and
strict_conflict, and records the seconds spent on each pair and the time the
pair was completed; both go into the exported file.

``score`` gives Cohen's kappa between the annotators, each annotator's agreement
with every machine source, the number of agreement-stratum rows on which a
human contradicts the agreed label with an upper bound, whom the annotators
side with on the disputed rows, and the timing.

The page cannot be built from a rubric that is still a draft: ``build`` refuses
a rubric file that contains "DRAFT" or an open "[R" marker. Nothing here
changes the gold dataset.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import pathlib
import random
import statistics
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.labeling.agreement_stats import agreement, cohen_kappa, table2x2, wilson  # noqa: E402
from hnav.labeling.audit_compare_laya import read_jsonl  # noqa: E402
from hnav.labeling.audit_disagreement_review import text_key  # noqa: E402
from hnav.labeling.audit_human_pilot import I18N, PAGE_TEMPLATE, blind_rows, build_id  # noqa: E402
from hnav.labeling.audit_human_review import SHEET_COLS  # noqa: E402
from hnav.labeling.audit_strict_review import read_model  # noqa: E402

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
MODEL_LABELS = DIR / "model_annotation" / "MODEL_LABELS.csv"
PILOT_KEY = DIR / "human_pilot" / "pilot_key.json"
REVIEW_KEY = DIR / "disagreement_review" / "disagreement_key.json"
REVIEW_SHEET = DIR / "disagreement_review" / "disagreement_sheet.filled.csv"
OUT = DIR / "validation"
STEM = "validation_sheet"
SHEET = OUT / f"{STEM}.csv"
PAGE = OUT / "validation_label.html"
KEY = OUT / "validation_key.json"
OUT_JSON = OUT / "VALIDATION_SUMMARY.json"
OUT_MD = OUT / "VALIDATION_SUMMARY.md"

SEED = 20261126
LABELS = ["update_conflict", "strict_conflict"]
TIMING = ["seconds", "answered_at"]
COLS = SHEET_COLS[:4] + LABELS + ["notes"] + TIMING
QUOTAS = {"core": 40, "lookalike": 40, "update_only": 15, "quarantined": 15}
TIER_OF = {"core": "core", "lookalike": "negative", "update_only": "update_only_fork",
           "quarantined": "discovered_unverified"}
LOOKALIKE_MIN_COS = 0.94
AGREEMENT_STRATA = list(QUOTAS)
FAST_SECONDS = 3.0


# ── the page: the pilot page plus per-pair timing ────────────────────────────

_PATCHES = [
    ("  var answers = {}, at = 0, lang = D.lang;\n",
     "  var answers = {}, at = 0, lang = D.lang, times = {}, shownAt = Date.now();\n"),
    ("  function save() { try { localStorage.setItem(storeKey, JSON.stringify(answers)); } catch (e) {} }\n",
     "  function save() { try { localStorage.setItem(storeKey, JSON.stringify(answers)); } catch (e) {} }\n"
     "  // Time on each pair: summed over visits while the tab is visible; the moment it was completed.\n"
     "  try { times = JSON.parse(localStorage.getItem(storeKey + \"-t\") || \"{}\") || {}; } catch (e) { times = {}; }\n"
     "  function trec(rid) { if (!times[rid]) { times[rid] = { s: 0, at: \"\" }; } return times[rid]; }\n"
     "  function saveT() { try { localStorage.setItem(storeKey + \"-t\", JSON.stringify(times)); } catch (e) {} }\n"
     "  function tick() {\n"
     "    var now = Date.now();\n"
     "    if (shownAt) { trec(rows[at].review_id).s += (now - shownAt) / 1000; }\n"
     "    shownAt = now;\n"
     "    saveT();\n"
     "  }\n"
     "  function stamp(rid) {\n"
     "    tick();\n"
     "    if (complete(rid) && !trec(rid).at) { trec(rid).at = new Date().toISOString(); saveT(); }\n"
     "  }\n"
     "  document.addEventListener(\"visibilitychange\", function () {\n"
     "    if (document.hidden) { tick(); shownAt = 0; } else { shownAt = Date.now(); }\n"
     "  });\n"
     "  window.addEventListener(\"beforeunload\", function () { if (shownAt) { tick(); } });\n"),
    ("          a[c] = o[0];\n          save();\n",
     "          a[c] = o[0];\n          stamp(r.review_id);\n          save();\n"),
    ("  function go(i) { at = Math.max(0, Math.min(rows.length - 1, i)); render(); window.scrollTo(0, 0); }\n",
     "  function go(i) { tick(); at = Math.max(0, Math.min(rows.length - 1, i)); render(); window.scrollTo(0, 0); }\n"),
    ("    var lines = [sheetCols.join(\",\")];\n",
     "    tick();\n    var lines = [sheetCols.join(\",\")];\n"),
    ("        if (c === \"review_id\" || c === \"subset\" || c === \"fact_a\" || c === \"fact_b\") { return cell(r[c]); }\n",
     "        if (c === \"review_id\" || c === \"subset\" || c === \"fact_a\" || c === \"fact_b\") { return cell(r[c]); }\n"
     "        if (c === \"seconds\") { return cell(times[r.review_id] ? Math.round(times[r.review_id].s * 10) / 10 : \"\"); }\n"
     "        if (c === \"answered_at\") { return cell(times[r.review_id] ? times[r.review_id].at : \"\"); }\n"),
]


def page_template() -> str:
    """The pilot page with timing added. Fails loudly if the pilot template has drifted."""
    t = PAGE_TEMPLATE
    for old, new in _PATCHES:
        if t.count(old) != 1:
            raise SystemExit(f"the pilot page template no longer contains exactly one {old.strip()[:60]!r}; "
                             f"update _PATCHES in audit_validation.py")
        t = t.replace(old, new)
    return t


def check_rubric(text: str, path: str) -> str:
    for mark in ("DRAFT", "[R"):
        if mark in text:
            raise SystemExit(f"{path}: the rubric still contains {mark!r}; the page is built only "
                             f"from an approved rubric")
    return text


def _i18n(rubric_en: str, rubric_tr: str) -> dict:
    out = copy.deepcopy(I18N)
    out["en"].update({
        "title": "Label validation: blind labelling",
        "sub": "Answer two questions for every pair. Do not check whether either sentence is true "
               "in the real world. Work alone; the page records the time spent on each pair.",
        "rubric": rubric_en})
    out["en"]["short"] = {
        "update_conflict": "Same entity, same attribute, same conditions, and two different values "
                           "(not two names for one value, neither containing the other). Whether "
                           "both could be true does not matter here.",
        "strict_conflict": "Only if the answer above is yes: the two sentences cannot both be true "
                           "of this entity at the same time. If the answer above is no, answer no."}
    out["tr"].update({
        "title": "Etiket doğrulaması: kör etiketleme",
        "sub": "Her çift için iki soruyu yanıtlayın. Cümlelerin gerçek dünyada doğru olup "
               "olmadığını kontrol etmeyin. Tek başınıza çalışın; sayfa her çifte harcanan süreyi "
               "kaydeder. Yanıtlar dosyaya İngilizce (yes/no) kaydedilir.",
        "rubric": rubric_tr})
    out["tr"]["short"] = {
        "update_conflict": "Aynı varlık, aynı özellik, aynı koşullar ve iki farklı değer (aynı "
                           "değerin iki adı değil, biri diğerini kapsamıyor). İkisinin birlikte "
                           "doğru olabilmesi burada önemli değil.",
        "strict_conflict": "Yalnızca yukarıdaki yanıt evetse: iki cümle bu varlık için aynı anda "
                           "doğru olamaz. Yukarıdaki yanıt hayırsa hayır deyin."}
    return out


def render_page(blind: list[dict], lang: str, rubric_en: str, rubric_tr: str) -> str:
    i18n = _i18n(rubric_en, rubric_tr)
    data = {"build_id": build_id(blind), "rows": blind, "label_cols": LABELS, "sheet_cols": COLS,
            "lang": lang, "langs": sorted(i18n), "i18n": i18n}
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return page_template().replace("__STEM__", STEM).replace("__DATA__", blob)


# ── selection ────────────────────────────────────────────────────────────────

def _sources(g: dict, m: dict | None) -> dict:
    j = g.get("judge") or {}
    return {"gold_update": bool(g["gold_update"]), "gold_strict": bool(g.get("gold_strict")),
            "judge_update": bool(j.get("update_conflict")), "judge_strict": bool(j.get("strict_conflict")),
            "parser_same_key": bool((g.get("parser") or {}).get("same_key")),
            "model_update": None if m is None else m["update"],
            "model_strict_first_guideline": None if m is None else m["strict"]}


def select(gold: list[dict], model: dict[str, dict], disputed: dict[str, dict],
           seen_pair_ids: set[str], extra: list[dict] | None = None, seed: int = SEED,
           quotas: dict[str, int] | None = None) -> tuple[list[dict], dict]:
    """Rows of the validation sheet and, per stratum, how many were eligible and drawn.

    ``disputed`` holds the rows of the stage 4 key (review_id -> shown_pair_id
    and, if known, the first annotator's stage 4 answer). ``seen_pair_ids`` are
    pair ids a human has labelled before; their sentence pairs are not eligible
    for the agreement strata.
    """
    quotas = QUOTAS if quotas is None else quotas
    by_id = {g["pair_id"]: g for g in gold}
    by_text: dict[frozenset, list[dict]] = {}
    for g in gold:
        by_text.setdefault(text_key(g), []).append(g)
    seen_texts = {text_key(by_id[p]) for p in seen_pair_ids if p in by_id}

    rows, drawn = [], {}
    for rid in sorted(disputed):
        g = by_id[disputed[rid]["shown_pair_id"]]
        rows.append({"stratum": "disputed", "shown_pair_id": g["pair_id"], "subset": g["subset"],
                     "fact_a": g["fact_a"], "fact_b": g["fact_b"],
                     "pair_ids": sorted(x["pair_id"] for x in by_text[text_key(g)]),
                     "sources": _sources(g, model.get(g["pair_id"])),
                     "stage4": {"review_id": rid, "update_conflict": disputed[rid].get("update_conflict")}})
    drawn["disputed"] = {"eligible": len(disputed), "requested": len(disputed), "drawn": len(disputed)}
    seen_texts |= {text_key(by_id[r["shown_pair_id"]]) for r in rows}

    rng = random.Random(seed)
    for stratum in AGREEMENT_STRATA:
        tier, pool = TIER_OF[stratum], []
        for t, copies in by_text.items():
            if t in seen_texts or any(g["tier"] != tier for g in copies):
                continue
            if any(g["pair_id"] not in model
                   or model[g["pair_id"]]["update"] != bool(g["gold_update"]) for g in copies):
                continue
            ok = sorted((g for g in copies
                         if stratum != "lookalike"
                         or (g.get("in_eval_set") and g["cosine_similarity"] >= LOOKALIKE_MIN_COS)),
                        key=lambda g: g["pair_id"])
            if ok:
                pool.append((ok[0], copies))
        pool.sort(key=lambda x: x[0]["pair_id"])
        rng.shuffle(pool)
        k = min(quotas.get(stratum, 0), len(pool))
        for g, copies in pool[:k]:
            rows.append({"stratum": stratum, "shown_pair_id": g["pair_id"], "subset": g["subset"],
                         "fact_a": g["fact_a"], "fact_b": g["fact_b"],
                         "pair_ids": sorted(x["pair_id"] for x in copies),
                         "sources": _sources(g, model[g["pair_id"]]), "stage4": None})
        drawn[stratum] = {"eligible": len(pool), "requested": quotas.get(stratum, 0), "drawn": k}

    for x in extra or []:
        rows.append({"stratum": "test_set", "shown_pair_id": x["id"], "subset": x.get("subset", "new"),
                     "fact_a": x["fact_a"], "fact_b": x["fact_b"], "pair_ids": [x["id"]],
                     "sources": {"constructed_update": bool(x["constructed_update"]),
                                 "constructed_strict": x.get("constructed_strict")},
                     "stage4": None})
    if extra:
        drawn["test_set"] = {"eligible": len(extra), "requested": len(extra), "drawn": len(extra)}

    rows.sort(key=lambda r: (r["stratum"], r["shown_pair_id"]))
    rng.shuffle(rows)                               # review_id order carries no stratum
    for i, r in enumerate(rows):
        r["review_id"] = f"V{i:03d}"
    return rows, drawn


# ── sheets ───────────────────────────────────────────────────────────────────

def write_sheet(path: pathlib.Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def read_sheet(path: pathlib.Path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"{path}: missing columns {missing}")
        rows = {}
        for i, r in enumerate(reader, start=2):
            rid = (r.get("review_id") or "").strip()
            if not rid or rid in rows:
                raise SystemExit(f"{path}:{i}: empty or duplicate review_id {rid!r}")
            rec = {}
            for c in LABELS:
                v = (r.get(c) or "").strip().lower()
                if v not in ("yes", "no"):
                    raise SystemExit(f"{path}:{i}:{c}: expected yes/no, got {r.get(c)!r}")
                rec[c] = v == "yes"
            s = (r.get("seconds") or "").strip()
            try:
                rec["seconds"] = float(s) if s else None
            except ValueError:
                raise SystemExit(f"{path}:{i}:seconds: not a number: {s!r}")
            rec["answered_at"] = (r.get("answered_at") or "").strip()
            rec["notes"] = (r.get("notes") or "").strip()
            rows[rid] = rec
    return rows


# ── build ────────────────────────────────────────────────────────────────────

def build(args) -> int:
    gold = list(read_jsonl(pathlib.Path(args.gold)))
    model = read_model(pathlib.Path(args.model_labels))
    seen = set()
    pk = pathlib.Path(args.pilot_key)
    if pk.exists():
        seen |= {v["pair_id"] for v in json.loads(pk.read_text(encoding="utf-8"))["rows"].values()}
    disputed = {}
    rk, rs = pathlib.Path(args.review_key), pathlib.Path(args.review_sheet)
    if rk.exists():
        stage4 = {}
        if rs.exists():
            with open(rs, newline="", encoding="utf-8") as f:
                stage4 = {r["review_id"]: (r.get("update_conflict") or "").strip().lower() == "yes"
                          for r in csv.DictReader(f)}
        for rid, v in json.loads(rk.read_text(encoding="utf-8"))["rows"].items():
            disputed[rid] = {"shown_pair_id": v["shown_pair_id"], "update_conflict": stage4.get(rid)}
            seen |= {p["pair_id"] for p in v["pairs"]}
    extra = list(read_jsonl(pathlib.Path(args.extra))) if args.extra else None
    rows, drawn = select(gold, model, disputed, seen, extra, seed=args.seed)
    print(f"validation sample: {len(rows)} sentence pairs")
    for s, d in drawn.items():
        note = "" if d["drawn"] == d["requested"] else "  <-- fewer than requested"
        print(f"  {s}: eligible {d['eligible']}, requested {d['requested']}, drawn {d['drawn']}{note}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    texts = {}
    for name, p in (("en", args.rubric_en), ("tr", args.rubric_tr)):
        if not p:
            raise SystemExit("build needs --rubric-en and --rubric-tr (the approved rubric)")
        texts[name] = check_rubric(pathlib.Path(p).read_text(encoding="utf-8"), p)
    blind = blind_rows(rows)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / KEY.name).write_text(json.dumps({
        "what": "review_id -> sentence pair, stratum and machine labels; not opened by an "
                "annotator before both sheets are frozen",
        "seed": args.seed, "build_id": build_id(blind), "n_rows": len(rows), "strata": drawn,
        "rows": {r["review_id"]: {k: r[k] for k in ("stratum", "shown_pair_id", "pair_ids",
                                                    "sources", "stage4")} for r in rows}},
        indent=1, ensure_ascii=False), encoding="utf-8")
    write_sheet(out / SHEET.name, blind)
    (out / PAGE.name).write_text(render_page(blind, args.lang, texts["en"], texts["tr"]),
                                 encoding="utf-8")
    print(f"wrote {out / SHEET.name}, {out / PAGE.name}, {out / KEY.name}")
    return 0


# ── score ────────────────────────────────────────────────────────────────────

def _rate(k: int, n: int) -> dict:
    return {"n": n, "k": k, "rate": (k / n) if n else None, "wilson95": list(wilson(k, n))}


UPDATE_SOURCES = ["gold_update", "judge_update", "parser_same_key", "model_update", "constructed_update"]
STRICT_SOURCES = ["gold_strict", "judge_strict", "model_strict_first_guideline", "constructed_strict"]


def _against_sources(sheet: dict, key: dict, ids: list[str]) -> dict:
    out = {}
    for field, names in (("update_conflict", UPDATE_SOURCES), ("strict_conflict", STRICT_SOURCES)):
        for name in names:
            sel = [r for r in ids if key[r]["sources"].get(name) is not None]
            if sel:
                out[f"{field} vs {name}"] = _rate(
                    sum(sheet[r][field] == bool(key[r]["sources"][name]) for r in sel), len(sel))
    return out


def _timing(sheet: dict, ids: list[str]) -> dict:
    s = [sheet[r]["seconds"] for r in ids if sheet[r]["seconds"] is not None]
    return {"rows_with_time": len(s), "median_seconds": statistics.median(s) if s else None,
            "total_minutes": round(sum(s) / 60, 1) if s else None,
            "rows_under_3_seconds": sum(x < FAST_SECONDS for x in s),
            "rows_without_completion_time": sum(not sheet[r]["answered_at"] for r in ids)}


def score_sheets(key: dict[str, dict], sheet_a: dict[str, dict],
                 sheet_b: dict[str, dict] | None = None) -> dict:
    sheets = {"A": sheet_a} if sheet_b is None else {"A": sheet_a, "B": sheet_b}
    for name, sh in sheets.items():
        if set(sh) != set(key):
            extra, missing = sorted(set(sh) - set(key)), sorted(set(key) - set(sh))
            raise SystemExit(f"sheet {name}: review_ids differ from the key "
                             f"(extra {extra[:5]}, missing {missing[:5]})")
    ids = sorted(key)
    strata = sorted({key[r]["stratum"] for r in ids})
    rep: dict = {"n_rows": len(ids), "annotators": len(sheets),
                 "by_stratum_n": dict(Counter(key[r]["stratum"] for r in ids)), "annotator": {}}

    agree_ids = [r for r in ids if key[r]["stratum"] in AGREEMENT_STRATA]
    disputed_ids = [r for r in ids if key[r]["stratum"] == "disputed"]
    for name, sh in sheets.items():
        contra = sorted(r for r in agree_ids
                        if sh[r]["update_conflict"] != key[r]["sources"]["gold_update"])
        with_gold = sum(sh[r]["update_conflict"] == key[r]["sources"]["gold_update"]
                        for r in disputed_ids)
        rep["annotator"][name] = {
            "update_yes": sum(sh[r]["update_conflict"] for r in ids),
            "strict_yes": sum(sh[r]["strict_conflict"] for r in ids),
            "strict_without_update": sorted(r for r in ids
                                            if sh[r]["strict_conflict"] and not sh[r]["update_conflict"]),
            "against_sources": _against_sources(sh, key, ids),
            "agreement_strata": {"n": len(agree_ids), "contradicts_agreed_label": contra,
                                 "error_rate": _rate(len(contra), len(agree_ids))},
            "disputed": {"n": len(disputed_ids), "sides_with_released_label": with_gold,
                         "sides_with_model": len(disputed_ids) - with_gold},
            "timing": _timing(sh, ids)}

    if sheet_b is not None:
        hh = {}
        for group, sel in [("all", ids)] + [(s, [r for r in ids if key[r]["stratum"] == s]) for s in strata]:
            hh[group] = {}
            for c in LABELS:
                x, y = [sheet_a[r][c] for r in sel], [sheet_b[r][c] for r in sel]
                hh[group][c] = {"n": len(sel), "agreement": agreement(x, y),
                                "kappa": cohen_kappa(x, y), "table_A_B": table2x2(x, y)}
        rep["human_human"] = hh
        both_contra = sorted(r for r in agree_ids
                             if sheet_a[r]["update_conflict"] == sheet_b[r]["update_conflict"]
                             != key[r]["sources"]["gold_update"])
        same = [r for r in disputed_ids if sheet_a[r]["update_conflict"] == sheet_b[r]["update_conflict"]]
        with_gold = sum(sheet_a[r]["update_conflict"] == key[r]["sources"]["gold_update"] for r in same)
        rep["both_annotators"] = {
            "agreement_strata_both_contradict": {"review_ids": both_contra,
                                                 "error_rate": _rate(len(both_contra), len(agree_ids))},
            "disputed": {"n": len(disputed_ids), "annotators_agree": len(same),
                         "sides_with_released_label": with_gold,
                         "sides_with_model": len(same) - with_gold}}
    return rep


def _f(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(_f(v, nd) for v in x) + "]"
    return str(x)


def render_md(rep: dict) -> str:
    L = ["# Label validation by two annotators — summary", ""]
    L.append(f"- sentence pairs: {rep['n_rows']} {rep['by_stratum_n']}; annotators: {rep['annotators']}")
    L.append("- Both annotators are authors. The gold dataset is unchanged.")
    L.append("")
    if "human_human" in rep:
        L.append("## Agreement between the annotators")
        L.append("")
        L.append("| rows | field | n | agreement | κ |")
        L.append("| --- | --- | ---: | ---: | ---: |")
        for group, fields in rep["human_human"].items():
            for c, s in fields.items():
                L.append(f"| {group} | {c} | {s['n']} | {_f(s['agreement'])} | {_f(s['kappa'])} |")
        L.append("")
        b = rep["both_annotators"]
        e, d = b["agreement_strata_both_contradict"], b["disputed"]
        L.append(f"Rows on which all machine sources agreed and both annotators contradict them: "
                 f"{e['error_rate']['k']} of {e['error_rate']['n']} "
                 f"(Wilson 95 % {_f(e['error_rate']['wilson95'])}).")
        L.append(f"Disputed rows: the annotators agree on {d['annotators_agree']} of {d['n']}; there, "
                 f"{d['sides_with_released_label']} side with the released label and "
                 f"{d['sides_with_model']} with the model.")
        L.append("")
    for name, a in rep["annotator"].items():
        L.append(f"## Annotator {name}")
        L.append("")
        t, g, d = a["timing"], a["agreement_strata"], a["disputed"]
        L.append(f"- update_conflict yes on {a['update_yes']}, strict_conflict yes on {a['strict_yes']}; "
                 f"strict without update on {len(a['strict_without_update'])} rows")
        L.append(f"- agreement strata: contradicts the agreed label on {g['error_rate']['k']} of "
                 f"{g['n']} (Wilson 95 % {_f(g['error_rate']['wilson95'])})")
        L.append(f"- disputed rows: {d['sides_with_released_label']} with the released label, "
                 f"{d['sides_with_model']} with the model, of {d['n']}")
        L.append(f"- time: median {_f(t['median_seconds'], 1)} s per pair over {t['rows_with_time']} "
                 f"rows, {_f(t['total_minutes'], 1)} min in all; {t['rows_under_3_seconds']} rows "
                 f"under 3 s; {t['rows_without_completion_time']} rows without a completion time")
        L.append("")
        L.append("| comparison | n | agree | rate | Wilson 95 % |")
        L.append("| --- | ---: | ---: | ---: | --- |")
        for k, s in a["against_sources"].items():
            L.append(f"| {k} | {s['n']} | {s['k']} | {_f(s['rate'])} | {_f(s['wilson95'])} |")
        L.append("")
    return "\n".join(L)


def score(args) -> int:
    key_doc = json.loads(pathlib.Path(args.key).read_text(encoding="utf-8"))
    a = read_sheet(pathlib.Path(args.sheet_a))
    b = read_sheet(pathlib.Path(args.sheet_b)) if args.sheet_b else None
    rep = score_sheets(key_doc["rows"], a, b)
    rep["build_id"] = key_doc.get("build_id")
    pathlib.Path(args.out_json).write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    pathlib.Path(args.out_md).write_text(render_md(rep), encoding="utf-8")
    print(f"scored {rep['n_rows']} sentence pairs, {rep['annotators']} annotator(s); "
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
    b.add_argument("--review-key", default=str(REVIEW_KEY))
    b.add_argument("--review-sheet", default=str(REVIEW_SHEET))
    b.add_argument("--extra", default=None, help="JSONL of test-set pairs to add as a stratum")
    b.add_argument("--rubric-en", default=None)
    b.add_argument("--rubric-tr", default=None)
    b.add_argument("--out-dir", default=str(OUT))
    b.add_argument("--seed", type=int, default=SEED)
    b.add_argument("--lang", choices=sorted(I18N), default="en")
    b.add_argument("--dry-run", action="store_true", help="print the strata and write nothing")
    b.set_defaults(func=build)
    s = sub.add_parser("score")
    s.add_argument("--key", default=str(KEY))
    s.add_argument("--sheet-a", required=True)
    s.add_argument("--sheet-b", default=None)
    s.add_argument("--out-json", default=str(OUT_JSON))
    s.add_argument("--out-md", default=str(OUT_MD))
    s.set_defaults(func=score)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
