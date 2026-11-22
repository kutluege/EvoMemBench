#!/usr/bin/env python3
"""Pilot human pass over the pairs the template parser and the LLM judge dispute.  [offline]

The full human review (``audit_human_review.py``) needs the Laya second reader,
which has to run on the GPU box first. This pilot needs nothing but the
committed gold dataset. It draws a small blind sheet from the three tiers in
which the parser's tag and the judge's verdict point in opposite directions:

    update_only_fork       parser: same key (an update)   judge: values compatible
    rejected               parser: same key               judge: not the same slot
    discovered_unverified  parser: different keys         judge: update conflict

plus a few control pairs from the balanced evaluation set (``core`` and
``negative``), where parser and judge agree, to check how the annotator reads
the rubric on undisputed cases.

    python hnav/labeling/audit_human_pilot.py build
    python hnav/labeling/audit_human_pilot.py score --sheet <filled.csv> [--sheet-b <filled.csv>]

``build`` writes a blind CSV sheet, a self-contained HTML page that fills the
same sheet in a browser (no Excel, no network), the rubric and a key.
``score`` compares the filled sheet with the judge and the parser per tier,
with Wilson intervals, and with a second annotator if one is given.

What this pilot is and is not (design of 2026-11-22):
  * a first human reading of the disputed tiers and a test of the rubric and
    the sheet before the full two-annotator review;
  * NOT the paper's agreement study. The sample is a few dozen pairs, drawn
    only from disputed tiers, and a single annotator gives no agreement
    figure. Nothing here estimates the judge's accuracy on the whole dataset;
  * NOT a relabelling. The gold dataset and its frozen tier counts are never
    touched, exactly as in ``audit_human_review.py``.

The sheet reuses the full review's columns and rubric, so pilot labels stay
comparable with later ones. A pilot pair may reappear in the full review set;
``pilot_key.json`` records which pairs were shown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.labeling.agreement_stats import (  # noqa: E402
    agreement, cohen_kappa, largest_remainder, table2x2, wilson)
from hnav.labeling.audit_compare_laya import read_jsonl  # noqa: E402
from hnav.labeling.audit_human_review import (  # noqa: E402
    LABEL_COLS, RUBRIC, SHEET_COLS, read_sheet, write_sheet)

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
OUT = DIR / "human_pilot"
SHEET = OUT / "pilot_sheet.csv"
PAGE = OUT / "pilot_label.html"
KEY = OUT / "pilot_key.json"
README = OUT / "pilot_README.md"
OUT_JSON = OUT / "PILOT_SUMMARY.json"
OUT_MD = OUT / "PILOT_SUMMARY.md"

SEED = 20261122
N_DISPUTED = 50
N_CONTROL = 10
DISPUTED_TIERS = ["update_only_fork", "rejected", "discovered_unverified"]
CONTROL_TIERS = ["core", "negative"]

PILOT_NOTE = """
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
"""

# One line per column for the labelling page, taken from the rubric above.
SHORT = {
    "same_referent": "Both sentences are about the same real-world entity.",
    "same_relation": "Both assert the same attribute or relation, even if phrased differently.",
    "context_overlap": "The propositions apply under compatible or overlapping validity conditions.",
    "values_incompatible": "The two values cannot both occupy the same slot under the same context.",
    "update_conflict": "With one current value per (entity, attribute) slot, one sentence replaces "
                       "the other's value. Yes exactly when the four checks above are all yes.",
    "strict_conflict": "The two sentences cannot both be true at the same time in the real world.",
}


# ── selection ────────────────────────────────────────────────────────────────

def parser_says_update(g: dict) -> bool:
    return bool((g.get("parser") or {}).get("same_key"))


def select_pilot(gold: list[dict], seed: int = SEED, n_disputed: int = N_DISPUTED,
                 n_control: int = N_CONTROL) -> list[dict]:
    """Return pilot rows: {review_id, pair_id, subset, tier, stratum, fact_a, fact_b}.

    Disputed seats are apportioned across the three disputed tiers in
    proportion to tier size; control seats are split evenly between ``core``
    and ``negative`` pairs of the balanced evaluation set.
    """
    rng = random.Random(seed)
    chosen: list[tuple[dict, str]] = []

    pools = {t: sorted((g for g in gold if g["tier"] == t), key=lambda g: g["pair_id"])
             for t in DISPUTED_TIERS}
    total = sum(len(p) for p in pools.values())
    seats = largest_remainder([len(pools[t]) for t in DISPUTED_TIERS], min(n_disputed, total))
    for t, k in zip(DISPUTED_TIERS, seats):
        pool = pools[t]
        rng.shuffle(pool)
        for g in pool[:k]:
            if parser_says_update(g) == bool(g["judge"]["update_conflict"]):
                raise SystemExit(f"{g['pair_id']} ({t}): parser and judge agree, so the pair is "
                                 f"not disputed; the tier definitions have drifted")
            chosen.append((g, "disputed"))

    cpools = {t: sorted((g for g in gold if g["tier"] == t and g.get("in_eval_set")),
                        key=lambda g: g["pair_id"]) for t in CONTROL_TIERS}
    cseats = largest_remainder([1 if cpools[t] else 0 for t in CONTROL_TIERS], n_control)
    for t, k in zip(CONTROL_TIERS, cseats):
        pool = cpools[t]
        rng.shuffle(pool)
        for g in pool[:k]:
            chosen.append((g, "control"))

    rows = [{"pair_id": g["pair_id"], "subset": g["subset"], "tier": g["tier"], "stratum": s,
             "fact_a": g["fact_a"], "fact_b": g["fact_b"]} for g, s in chosen]
    rows.sort(key=lambda r: r["pair_id"])
    rng.shuffle(rows)                               # review_id order carries no tier information
    for i, r in enumerate(rows):
        r["review_id"] = f"P{i:03d}"
    return rows


def blind_rows(rows: list[dict]) -> list[dict]:
    return [{c: r[c] for c in ("review_id", "subset", "fact_a", "fact_b")} for r in rows]


def build_id(blind: list[dict]) -> str:
    blob = json.dumps(blind, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


# ── labelling page ───────────────────────────────────────────────────────────

PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pilot review: blind labelling</title>
<style>
:root{--bg:#faf9f6;--fg:#1d1c1a;--muted:#67645e;--line:#d8d4ca;--card:#ffffff;--yes:#1d6b47;--no:#8c302b;--accent:#28497c;--on:#ffffff}
@media (prefers-color-scheme:dark){:root{--bg:#171716;--fg:#eceae4;--muted:#a3a098;--line:#3b3a36;--card:#20201e;--yes:#3f9a6f;--no:#c5625b;--accent:#8cafe8;--on:#111110}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:820px;margin:0 auto;padding:20px 16px 64px}
h1{font-size:1.25rem;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 16px;font-size:.95rem}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0}
.bar .grow{flex:1 1 auto;color:var(--muted);font-variant-numeric:tabular-nums}
button{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:7px 12px;cursor:pointer}
button:hover{border-color:var(--accent)}
button:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.primary{background:var(--accent);border-color:var(--accent);color:var(--on)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:12px 0}
.fact{font-size:1.1rem;margin:0 0 10px}
.fact:last-child{margin:0}
.tag{display:inline-block;min-width:1.5em;font-weight:600;color:var(--accent)}
.q{display:grid;grid-template-columns:1fr auto;gap:6px 14px;align-items:start;padding:11px 0;border-top:1px solid var(--line)}
.q:first-child{border-top:0;padding-top:0}
.q code{font:600 .95rem ui-monospace,Consolas,monospace}
.q p{margin:2px 0 0;color:var(--muted);font-size:.93rem}
.yn{display:flex;gap:6px}
.yn button{min-width:58px}
.yn button[aria-pressed="true"].y{background:var(--yes);border-color:var(--yes);color:#fff}
.yn button[aria-pressed="true"].n{background:var(--no);border-color:var(--no);color:#fff}
textarea{width:100%;min-height:56px;font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px}
label{display:block;color:var(--muted);font-size:.93rem;margin-bottom:4px}
#status{min-height:1.5em;color:var(--muted);font-size:.93rem}
details{margin-top:20px}
summary{cursor:pointer;color:var(--accent)}
pre{white-space:pre-wrap;font:inherit;font-size:.93rem;color:var(--fg);margin:10px 0 0}
@media (max-width:520px){.q{grid-template-columns:1fr}}
</style>
</head>
<body>
<main>
<h1>Pilot review: blind labelling</h1>
<p class="sub">Decide whether the two sentences express conflicting propositions. Do not check whether either is true in the real world. Answer all six questions for every pair.</p>

<div class="bar">
  <span class="grow" id="progress"></span>
  <button id="prev" type="button">Previous</button>
  <button id="next" type="button">Next</button>
  <button id="todo" type="button">Next unanswered</button>
</div>

<div class="card" id="facts"></div>
<div class="card" id="questions"></div>
<div class="card">
  <label for="notes">Notes (optional)</label>
  <textarea id="notes"></textarea>
</div>

<div class="bar">
  <span class="grow" id="status"></span>
  <button id="download" type="button" class="primary">Download CSV</button>
</div>

<details>
  <summary>Full instructions</summary>
  <pre id="rubric"></pre>
</details>
</main>

<script id="data" type="application/json">__DATA__</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById("data").textContent);
  var rows = D.rows, cols = D.label_cols, sheetCols = D.sheet_cols;
  var storeKey = "pilot-review-" + D.build_id;
  var answers = {}, at = 0;

  try { answers = JSON.parse(localStorage.getItem(storeKey) || "{}") || {}; } catch (e) { answers = {}; }
  function save() { try { localStorage.setItem(storeKey, JSON.stringify(answers)); } catch (e) {} }
  function rec(rid) { if (!answers[rid]) { answers[rid] = {}; } return answers[rid]; }
  function complete(rid) {
    var a = answers[rid] || {};
    return cols.every(function (c) { return a[c] === "yes" || a[c] === "no"; });
  }
  function nDone() { return rows.filter(function (r) { return complete(r.review_id); }).length; }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text !== undefined) { e.textContent = text; }
    return e;
  }

  function render() {
    var r = rows[at], a = rec(r.review_id);
    document.getElementById("progress").textContent =
      "Pair " + (at + 1) + " of " + rows.length + " (" + r.review_id + ", " + r.subset + ")  |  " +
      nDone() + " complete";

    var f = document.getElementById("facts");
    f.textContent = "";
    [["A", r.fact_a], ["B", r.fact_b]].forEach(function (p) {
      var line = el("p", "fact");
      line.appendChild(el("span", "tag", p[0]));
      line.appendChild(document.createTextNode(p[1]));
      f.appendChild(line);
    });

    var q = document.getElementById("questions");
    q.textContent = "";
    cols.forEach(function (c) {
      var row = el("div", "q"), left = el("div"), yn = el("div", "yn");
      left.appendChild(el("code", "", c));
      left.appendChild(el("p", "", D.short[c] || ""));
      [["yes", "y", "Yes"], ["no", "n", "No"]].forEach(function (o) {
        var b = el("button", o[1], o[2]);
        b.type = "button";
        b.setAttribute("aria-pressed", a[c] === o[0] ? "true" : "false");
        b.setAttribute("aria-label", c + ": " + o[2]);
        b.addEventListener("click", function () {
          a[c] = o[0];
          save();
          render();
        });
        yn.appendChild(b);
      });
      row.appendChild(left);
      row.appendChild(yn);
      q.appendChild(row);
    });
    document.getElementById("notes").value = a.notes || "";
  }

  function go(i) { at = Math.max(0, Math.min(rows.length - 1, i)); render(); window.scrollTo(0, 0); }

  document.getElementById("notes").addEventListener("input", function (ev) {
    rec(rows[at].review_id).notes = ev.target.value;
    save();
  });
  document.getElementById("prev").addEventListener("click", function () { go(at - 1); });
  document.getElementById("next").addEventListener("click", function () { go(at + 1); });
  document.getElementById("todo").addEventListener("click", function () {
    for (var k = 1; k <= rows.length; k++) {
      var i = (at + k) % rows.length;
      if (!complete(rows[i].review_id)) { go(i); return; }
    }
    document.getElementById("status").textContent = "Every pair is complete.";
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.target && ev.target.tagName === "TEXTAREA") { return; }
    if (ev.key === "ArrowLeft") { go(at - 1); }
    if (ev.key === "ArrowRight") { go(at + 1); }
  });

  function cell(v) { return '"' + String(v === undefined || v === null ? "" : v).replace(/"/g, '""') + '"'; }
  document.getElementById("download").addEventListener("click", function () {
    var lines = [sheetCols.join(",")];
    rows.forEach(function (r) {
      var a = answers[r.review_id] || {};
      lines.push(sheetCols.map(function (c) {
        if (c === "review_id" || c === "subset" || c === "fact_a" || c === "fact_b") { return cell(r[c]); }
        return cell(a[c]);
      }).join(","));
    });
    var missing = rows.length - nDone();
    var name = missing ? "pilot_sheet.partial.csv" : "pilot_sheet.filled.csv";
    var blob = new Blob([lines.join("\r\n") + "\r\n"], { type: "text/csv;charset=utf-8" });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    document.getElementById("status").textContent = missing
      ? "Saved " + name + ". " + missing + " pairs are incomplete; the scorer rejects blank cells."
      : "Saved " + name + ". All " + rows.length + " pairs are complete.";
  });

  document.getElementById("rubric").textContent = D.rubric;
  for (var i = 0; i < rows.length; i++) { if (!complete(rows[i].review_id)) { at = i; break; } }
  render();
})();
</script>
</body>
</html>
"""


def render_page(blind: list[dict]) -> str:
    data = {"build_id": build_id(blind), "rows": blind, "label_cols": LABEL_COLS,
            "sheet_cols": SHEET_COLS, "short": SHORT, "rubric": RUBRIC}
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return PAGE_TEMPLATE.replace("__DATA__", blob)


# ── build ────────────────────────────────────────────────────────────────────

def build(args) -> int:
    gold = list(read_jsonl(pathlib.Path(args.gold)))
    rows = select_pilot(gold, seed=args.seed, n_disputed=args.n_disputed, n_control=args.n_control)
    blind = blind_rows(rows)
    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / KEY.name).write_text(json.dumps({
        "what": "review_id -> pair; the annotator does not open this file before finishing",
        "seed": args.seed, "n": len(rows), "build_id": build_id(blind),
        "by_stratum": Counter(r["stratum"] for r in rows),
        "by_tier": Counter(r["tier"] for r in rows),
        "rows": {r["review_id"]: {"pair_id": r["pair_id"], "tier": r["tier"], "stratum": r["stratum"]}
                 for r in rows}}, indent=1, ensure_ascii=False, default=dict), encoding="utf-8")
    write_sheet(out / SHEET.name, blind)
    (out / PAGE.name).write_text(render_page(blind), encoding="utf-8")
    (out / README.name).write_text(RUBRIC + PILOT_NOTE, encoding="utf-8")
    print(f"pilot set: {len(rows)} pairs; by tier {dict(Counter(r['tier'] for r in rows))}")
    print(f"wrote {out / SHEET.name}, {out / PAGE.name}, {out / KEY.name}, {out / README.name}")
    return 0


# ── score ────────────────────────────────────────────────────────────────────

def _rate(k: int, n: int) -> dict:
    return {"n": n, "k": k, "rate": (k / n) if n else None, "wilson95": wilson(k, n)}


def score_sheet(sheet: dict[str, dict], key: dict[str, dict], gold: dict[str, dict],
                sheet_b: dict[str, dict] | None = None) -> dict:
    for name, sh in (("sheet", sheet), ("sheet-b", sheet_b)):
        if sh is not None and set(sh) != set(key):
            extra, missing = sorted(set(sh) - set(key)), sorted(set(key) - set(sh))
            raise SystemExit(f"{name}: review_ids differ from the key "
                             f"(extra {extra[:5]}, missing {missing[:5]})")
    ids = sorted(key)
    rep: dict = {"n_reviewed": len(ids), "annotators": 2 if sheet_b else 1,
                 "by_stratum_n": Counter(key[r]["stratum"] for r in ids)}

    groups = [("disputed", [r for r in ids if key[r]["stratum"] == "disputed"]),
              ("control", [r for r in ids if key[r]["stratum"] == "control"])]
    groups += [(t, [r for r in ids if key[r]["tier"] == t])
               for t in DISPUTED_TIERS + CONTROL_TIERS if any(key[r]["tier"] == t for r in ids)]
    by_group = {}
    for name, sel in groups:
        g = [gold[key[r]["pair_id"]] for r in sel]
        human = [sheet[r]["update_conflict"] for r in sel]
        by_group[name] = {
            "n": len(sel),
            "human_update_yes": sum(human),
            "human_strict_yes": sum(sheet[r]["strict_conflict"] for r in sel),
            "agrees_with_judge": _rate(sum(h == bool(x["judge"]["update_conflict"])
                                           for h, x in zip(human, g)), len(sel)),
            "agrees_with_parser": _rate(sum(h == parser_says_update(x)
                                            for h, x in zip(human, g)), len(sel)),
        }
    rep["update_conflict_by_group"] = by_group

    rep["field_agreement_with_judge"] = {
        c: _rate(sum(sheet[r][c] == bool(gold[key[r]["pair_id"]]["judge"][c]) for r in ids), len(ids))
        for c in LABEL_COLS}

    if sheet_b:
        hh = {}
        for c in LABEL_COLS:
            x = [sheet[r][c] for r in ids]
            y = [sheet_b[r][c] for r in ids]
            hh[c] = {"n": len(ids), "agreement": agreement(x, y), "kappa": cohen_kappa(x, y),
                     "table_A_B": table2x2(x, y)}
        rep["human_human"] = hh
    return rep


def _f(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, (tuple, list)):
        return "[" + ", ".join(_f(v, nd) for v in x) + "]"
    return str(x)


def render_md(rep: dict) -> str:
    L = ["# Pilot human review of parser–judge disputes — summary", ""]
    L.append(f"- pairs reviewed: {rep['n_reviewed']} ({dict(rep['by_stratum_n'])}); "
             f"annotators: {rep['annotators']}")
    L.append("- This is a pilot. The pairs come from disputed tiers only, so nothing here estimates "
             "the judge's accuracy on the dataset, and one annotator gives no agreement figure. "
             "The gold dataset is unchanged.")
    L.append("")
    L.append("## update_conflict: whom the annotator sides with")
    L.append("")
    L.append("| group | n | human yes | agrees with judge | Wilson 95 % | agrees with parser | Wilson 95 % |")
    L.append("| --- | ---: | ---: | ---: | --- | ---: | --- |")
    for name, b in rep["update_conflict_by_group"].items():
        j, p = b["agrees_with_judge"], b["agrees_with_parser"]
        L.append(f"| {name} | {b['n']} | {b['human_update_yes']} | {j['k']} | {_f(j['wilson95'])} | "
                 f"{p['k']} | {_f(p['wilson95'])} |")
    L.append("")
    L.append("In a disputed tier the parser and the judge disagree on every pair, so the two "
             "counts sum to n.")
    L.append("")
    L.append("## Agreement with the judge, field by field (all pairs)")
    L.append("")
    L.append("| field | n | agree | rate | Wilson 95 % |")
    L.append("| --- | ---: | ---: | ---: | --- |")
    for c, s in rep["field_agreement_with_judge"].items():
        L.append(f"| {c} | {s['n']} | {s['k']} | {_f(s['rate'])} | {_f(s['wilson95'])} |")
    L.append("")
    if "human_human" in rep:
        L.append("## Human–human agreement (independent, blind)")
        L.append("")
        L.append("| field | n | agreement | κ |")
        L.append("| --- | ---: | ---: | ---: |")
        for c, s in rep["human_human"].items():
            L.append(f"| {c} | {s['n']} | {_f(s['agreement'])} | {_f(s['kappa'])} |")
        L.append("")
    return "\n".join(L)


def score(args) -> int:
    key_doc = json.loads(pathlib.Path(args.key).read_text(encoding="utf-8"))
    key = key_doc["rows"]
    sheet = read_sheet(pathlib.Path(args.sheet))
    sheet_b = read_sheet(pathlib.Path(args.sheet_b)) if args.sheet_b else None
    wanted = {v["pair_id"] for v in key.values()}
    gold = {g["pair_id"]: g for g in read_jsonl(pathlib.Path(args.gold)) if g["pair_id"] in wanted}
    missing = sorted(wanted - set(gold))
    if missing:
        raise SystemExit(f"{len(missing)} pilot pairs are not in the gold dataset, e.g. {missing[:3]}")
    rep = score_sheet(sheet, key, gold, sheet_b)
    rep["build_id"] = key_doc.get("build_id")
    rep["seed"] = key_doc.get("seed")
    pathlib.Path(args.out_json).write_text(json.dumps(rep, indent=1, default=dict), encoding="utf-8")
    pathlib.Path(args.out_md).write_text(render_md(rep), encoding="utf-8")
    print(f"scored {rep['n_reviewed']} pairs; wrote {args.out_md}, {args.out_json}")
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--gold", default=str(GOLD))
    b.add_argument("--out-dir", default=str(OUT))
    b.add_argument("--seed", type=int, default=SEED)
    b.add_argument("--n-disputed", type=int, default=N_DISPUTED)
    b.add_argument("--n-control", type=int, default=N_CONTROL)
    b.set_defaults(func=build)
    s = sub.add_parser("score")
    s.add_argument("--gold", default=str(GOLD))
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
