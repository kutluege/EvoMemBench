"""Model annotator pass over the gold conflict pairs, calibrated on the human pilot.

Offline tier, stdlib only. Nothing here calls a model: the annotator is a
Claude Code subagent (`.claude/agents/pair-annotator.md`) that reads blind
batch sheets and writes label files; this module prepares its inputs and
scores its outputs. The gold dataset is read, never written.

What the pass is and is not
---------------------------
The human pilot (`audit_human_pilot.py`, 60 pairs, one annotator) is the only
human evidence. Its labels are written into a guideline with worked examples
(`.claude/skills/pair-labelling/SKILL.md`); the model annotator follows that
guideline. No model weights change: "calibrated on" means in-context
instructions and examples, nothing more. The resulting labels are a third
automatic reading next to the template parser and the GPT-5-mini judge. They
are not human labels and do not replace the two-annotator human study.

Held-out check
--------------
`split` sets aside part of the pilot before the guideline is written. The
guideline is first drafted from the calibration part only and the annotator
labels the held-out pairs blind; `ingest` reports that agreement. It is the
only number here that speaks to whether the annotator follows the human on
pairs it was not shown. Its n is small and it is reported with its interval.

Gate
----
The stage batches are labelled only if the held-out check passes
(`HELDOUT_GATE`, fixed before any model label existed): agreement with the
human on `update_conflict` of at least 0.85, and at least 0.80 on each of the
other five fields. The check is run with the same model and reasoning effort
as the stage batches. If it fails, the pass stops and the authors decide; the
guideline is not tuned against the held-out pairs.

Parallel workers
----------------
The stage batches are split among several identical subagents, each given a
disjoint list of batches (`assign`). A worker writes only its own batches'
label files, so workers cannot collide, and a stopped worker's finished
batches stay on disk.

Stages
------
stage 1   the balanced evaluation set (all positives and their cosine-matched
          negatives) plus the `rejected` and `discovered_unverified` tiers,
          minus the pilot pairs; shuffled together, so a batch does not reveal
          a pair's tier.
stage 2   every other audited negative. On their own these batches would be
          all one tier, so each one also carries `N_SENTINEL` sentinel rows:
          stage-1 pairs from the other tiers, under new review ids, mixed in
          at random positions. A worker cannot tell them apart, so a batch is
          never uniformly "no", and `ingest` compares each sentinel with the
          label the same pair received in stage 1. Sentinel rows are a check
          on the worker, not new labels; they are kept out of MODEL_LABELS.

Consistency
-----------
Many sentence pairs occur in more than one subset under different pair ids,
so the same text is labelled several times, usually by different workers.
`ingest` reports how often those repeats received identical labels, and how
the model's referent and relation labels line up with the parser's slots.

    python hnav/labeling/audit_model_annotator.py split --sheet <filled pilot csv>
    python hnav/labeling/audit_model_annotator.py batches [--stage 1|2|all]
    python hnav/labeling/audit_model_annotator.py status
    python hnav/labeling/audit_model_annotator.py assign --group stage1 --workers 9
    python hnav/labeling/audit_model_annotator.py ingest --sheet <filled pilot csv>
"""
from __future__ import annotations

import argparse
import csv
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
from hnav.labeling.audit_human_pilot import parser_says_update  # noqa: E402
from hnav.labeling.audit_human_review import (  # noqa: E402
    LABEL_COLS, SHEET_COLS, _parse_yn, read_sheet, write_sheet)

DIR = REPO / "stage0_results" / "conflict_pairs"
GOLD = DIR / "gold_conflict_dataset.jsonl.gz"
PILOT = DIR / "human_pilot"
PILOT_KEY = PILOT / "pilot_key.json"
PILOT_FILLED = PILOT / "pilot_sheet.filled.csv"
OUT = DIR / "model_annotation"

SEED = 20261122
N_HELDOUT = 20
BATCH_SIZE = 100
N_SENTINEL = 10
TIERS = ["core", "update_only_fork", "rejected", "discovered_unverified", "negative"]
STAGE_PREFIX = {1: "a", 2: "b"}
BATCH_COLS = ["review_id", "fact_a", "fact_b"]
OUT_COLS = ["review_id"] + LABEL_COLS + ["notes"]
ANNOTATOR = "claude-fable-5-2, reasoning effort medium, Claude Code subagents (parallel workers)"
HELDOUT_GATE = {"update_conflict": 0.85, "each_other_field": 0.80}


# ── small helpers ────────────────────────────────────────────────────────────

def _write_csv(path: pathlib.Path, cols: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def _read_csv(path: pathlib.Path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def _write_json(path: pathlib.Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _rate(k: int, n: int) -> dict:
    return {"n": n, "k": k, "rate": (k / n) if n else None, "wilson95": wilson(k, n)}


def rubric_violations(lab: dict) -> list[str]:
    """Where a label row departs from the two derivation rules of the written rubric."""
    out = []
    if lab["update_conflict"] != all(lab[c] for c in LABEL_COLS[:4]):
        out.append("update_conflict differs from the conjunction of the four checks")
    if lab["strict_conflict"] and not lab["update_conflict"]:
        out.append("strict_conflict without update_conflict")
    return out


def stage_of(g: dict) -> int:
    return 1 if (g["tier"] != "negative" or g.get("in_eval_set")) else 2


def _yn(b: bool) -> str:
    return "yes" if b else "no"


# ── split: calibration vs held-out pilot pairs ───────────────────────────────

def split_pilot(key_rows: dict[str, dict], seed: int = SEED, n_heldout: int = N_HELDOUT) -> list[str]:
    """Return the held-out pilot review ids, apportioned across tiers by tier size."""
    tiers = [t for t in TIERS if any(r["tier"] == t for r in key_rows.values())]
    pools = {t: sorted(rid for rid, r in key_rows.items() if r["tier"] == t) for t in tiers}
    seats = largest_remainder([len(pools[t]) for t in tiers], min(n_heldout, len(key_rows)))
    rng = random.Random(f"{seed}:heldout")
    held = []
    for t, k in zip(tiers, seats):
        pool = pools[t]
        rng.shuffle(pool)
        held += pool[:k]
    return sorted(held)


def examples_md(rows: list[dict]) -> str:
    """Worked examples for the guideline, one per human-labelled pair, verbatim."""
    short = {"same_referent": "ref", "same_relation": "rel", "context_overlap": "ctx",
             "values_incompatible": "incompat", "update_conflict": "update",
             "strict_conflict": "strict"}
    out = []
    for r in rows:
        labs = ", ".join(f"{short[c]}={r[c]}" for c in LABEL_COLS)
        note = f" Annotator note: {r['notes']}" if r.get("notes") else ""
        out.append(f"- **{r['review_id']}** A: \"{r['fact_a']}\" / B: \"{r['fact_b']}\"\n"
                   f"  {labs}.{note}")
    return "\n".join(out) + "\n"


def split(args) -> int:
    key = _read_json(args.key)
    labels = read_sheet(args.sheet)
    if set(labels) != set(key["rows"]):
        raise SystemExit(f"{args.sheet}: review ids differ from {args.key}")
    _, raw = _read_csv(args.sheet)
    facts = {r["review_id"].strip(): r for r in raw}
    held = split_pilot(key["rows"], args.seed, args.n_heldout)
    calib = sorted(set(labels) - set(held))

    def full(rid: str) -> dict:
        row = {"review_id": rid, "subset": facts[rid]["subset"], "fact_a": facts[rid]["fact_a"],
               "fact_b": facts[rid]["fact_b"], "notes": labels[rid]["notes"]}
        row.update({c: _yn(labels[rid][c]) for c in LABEL_COLS})
        return row

    out = args.out_dir
    cal_rows = [full(r) for r in calib]
    out.mkdir(parents=True, exist_ok=True)
    write_sheet(out / "calibration_human.csv", cal_rows)
    (out / "calibration_examples.md").write_text(examples_md(cal_rows), encoding="utf-8")
    (out / "all_pilot_examples.md").write_text(examples_md([full(r) for r in sorted(labels)]),
                                               encoding="utf-8")

    rng = random.Random(f"{args.seed}:heldout-order")
    order = list(held)
    rng.shuffle(order)
    hkey = {f"h{i + 1:03d}": {"pilot_id": rid, "pair_id": key["rows"][rid]["pair_id"]}
            for i, rid in enumerate(order)}
    _write_csv(out / "batches" / "heldout" / "batch_001.csv", BATCH_COLS,
               [{"review_id": h, "fact_a": facts[v["pilot_id"]]["fact_a"],
                 "fact_b": facts[v["pilot_id"]]["fact_b"]} for h, v in hkey.items()])
    _write_json(out / "heldout_key.json", {
        "what": "held-out pilot pairs; the annotator does not open this file",
        "seed": args.seed, "n_heldout": len(held), "n_calibration": len(calib),
        "by_tier_heldout": Counter(key["rows"][r]["tier"] for r in held),
        "by_tier_calibration": Counter(key["rows"][r]["tier"] for r in calib),
        "rows": hkey})

    viol = Counter(v for r in calib for v in rubric_violations(labels[r]))
    print(f"calibration {len(calib)} pairs -> {out / 'calibration_human.csv'}")
    print(f"held-out    {len(held)} pairs -> {out / 'batches' / 'heldout' / 'batch_001.csv'} (blind)")
    print("calibration rows departing from the written rubric's derivation rules:",
          dict(viol) or "none")
    return 0


# ── batches ──────────────────────────────────────────────────────────────────

def make_batches(gold: list[dict], exclude: set[str], stage: int, seed: int = SEED,
                 batch_size: int = BATCH_SIZE, sentinels: list[dict] | None = None,
                 n_sentinel: int = 0) -> list[list[dict]]:
    """Blind batches of `batch_size` new pairs, plus `n_sentinel` sentinel rows per batch."""
    pool = sorted((g for g in gold if stage_of(g) == stage and g["pair_id"] not in exclude),
                  key=lambda g: g["pair_id"])
    rng = random.Random(f"{seed}:stage{stage}")
    rng.shuffle(pool)                                     # order carries no tier information
    chunks = [pool[i:i + batch_size] for i in range(0, len(pool), batch_size)]
    if sentinels and n_sentinel:
        spool = sorted(sentinels, key=lambda g: g["pair_id"])
        srng = random.Random(f"{seed}:stage{stage}:sentinels")
        for chunk in chunks:
            chunk += srng.sample(spool, min(n_sentinel, len(spool)))
            srng.shuffle(chunk)
    out, i = [], 0
    for chunk in chunks:
        rows = []
        for g in chunk:
            i += 1
            rows.append({"review_id": f"{STAGE_PREFIX[stage]}{i:05d}", "pair_id": g["pair_id"],
                         "fact_a": g["fact_a"], "fact_b": g["fact_b"]})
        out.append(rows)
    return out


def batches(args) -> int:
    gold = list(read_jsonl(args.gold))
    pilot = {r["pair_id"] for r in _read_json(args.key)["rows"].values()}
    stages = [1, 2] if args.stage == "all" else [int(args.stage)]
    key_path = args.out_dir / "batch_key.json"
    key = _read_json(key_path) if key_path.exists() else {
        "what": "review_id -> pair_id; the annotator does not open this file",
        "seed": args.seed, "batch_size": args.batch_size, "stages": {}}
    if (key["seed"], key["batch_size"]) != (args.seed, args.batch_size):
        raise SystemExit(f"{key_path} was built with another seed or batch size")
    for s in stages:
        sent = []
        if s == 2 and args.n_sentinel:
            merged, _, _ = collect(args.out_dir)
            done1 = {m["pair_id"] for m in merged.values() if m["group"] == "stage1"}
            sent = [g for g in gold if g["pair_id"] in done1 and g["tier"] != "negative"]
            if not sent:
                raise SystemExit("stage 2 needs stage-1 labels for its sentinel rows; none found")
        bs = make_batches(gold, pilot, s, args.seed, args.batch_size, sent, args.n_sentinel)
        for i, rows in enumerate(bs, start=1):
            _write_csv(args.out_dir / "batches" / f"stage{s}" / f"batch_{i:03d}.csv", BATCH_COLS, rows)
        key["stages"][str(s)] = {
            f"batch_{i:03d}": {r["review_id"]: r["pair_id"] for r in rows}
            for i, rows in enumerate(bs, start=1)}
        print(f"stage {s}: {sum(map(len, bs))} rows in {len(bs)} batches"
              + (f" ({args.n_sentinel} sentinel rows per batch)" if sent else ""))
    _write_json(key_path, key)
    return 0


# ── label files ──────────────────────────────────────────────────────────────

def read_labels(path: pathlib.Path, expected_ids: set[str]) -> dict[str, dict]:
    """Read one label file written by the annotator. Raises ValueError on any defect."""
    cols, raw = _read_csv(path)
    missing = [c for c in OUT_COLS if c not in cols]
    if missing:
        raise ValueError(f"missing columns {missing}")
    rows: dict[str, dict] = {}
    for i, r in enumerate(raw, start=2):
        rid = (r.get("review_id") or "").strip()
        if rid in rows:
            raise ValueError(f"line {i}: duplicate review_id {rid}")
        try:
            rows[rid] = {c: _parse_yn(r.get(c, ""), f"line {i}:{c}") for c in LABEL_COLS}
        except SystemExit as e:
            raise ValueError(str(e)) from None
        rows[rid]["notes"] = (r.get("notes") or "").strip()
    if set(rows) != expected_ids:
        extra, lack = sorted(set(rows) - expected_ids), sorted(expected_ids - set(rows))
        raise ValueError(f"review ids differ from the batch (extra {extra[:5]}, missing {lack[:5]})")
    return rows


def batch_index(out_dir: pathlib.Path) -> list[tuple[str, str, dict[str, str]]]:
    """[(group, batch name, {review_id: pair_id})] for every batch that has been built."""
    idx = []
    hk = out_dir / "heldout_key.json"
    if hk.exists():
        idx.append(("heldout", "batch_001", {h: v["pair_id"] for h, v in _read_json(hk)["rows"].items()}))
    bk = out_dir / "batch_key.json"
    if bk.exists():
        for s, bs in sorted(_read_json(bk)["stages"].items()):
            idx += [(f"stage{s}", name, ids) for name, ids in sorted(bs.items())]
    return idx


def collect(out_dir: pathlib.Path) -> tuple[dict[str, dict], list[dict], dict[str, dict]]:
    """Read every label file.

    Returns ({review_id: labels + pair_id + group + batch}, per-batch status,
    sentinel rows in the same shape). A stage-2 row is a sentinel when its
    pair belongs to stage 1.
    """
    merged: dict[str, dict] = {}
    sentinels: dict[str, dict] = {}
    status = []
    index = batch_index(out_dir)
    stage1_pairs = {pid for group, _, ids in index if group == "stage1" for pid in ids.values()}
    for group, name, ids in index:
        path = out_dir / "labels" / group / f"{name}.csv"
        st = {"group": group, "batch": name, "n": len(ids), "state": "missing", "error": None}
        if path.exists():
            try:
                rows = read_labels(path, set(ids))
                for rid, lab in rows.items():
                    is_sentinel = group == "stage2" and ids[rid] in stage1_pairs
                    (sentinels if is_sentinel else merged)[rid] = dict(
                        lab, pair_id=ids[rid], group=group, batch=f"{group}/{name}")
                st["state"] = "done"
            except ValueError as e:
                st["state"], st["error"] = "invalid", str(e)
        status.append(st)
    return merged, status, sentinels


def status(args) -> int:
    _, st, _ = collect(args.out_dir)
    for g in sorted({s["group"] for s in st}):
        sel = [s for s in st if s["group"] == g]
        c = Counter(s["state"] for s in sel)
        print(f"{g}: {c['done']}/{len(sel)} batches done, {c['invalid']} invalid, {c['missing']} missing")
        for s in sel:
            if s["state"] == "invalid":
                print(f"  {g}/{s['batch']}: {s['error']}")
        nxt = [s["batch"] for s in sel if s["state"] != "done"][:3]
        if nxt:
            print(f"  next: {', '.join(nxt)}")
    return 0


def assign_batches(status_rows: list[dict], group: str, workers: int) -> list[list[str]]:
    """Split the batches of `group` that are not done into `workers` contiguous, disjoint lists."""
    todo = [s["batch"] for s in status_rows if s["group"] == group and s["state"] != "done"]
    sizes = largest_remainder([1] * workers, len(todo)) if todo else []
    out, i = [], 0
    for k in sizes:
        if k:
            out.append(todo[i:i + k])
        i += k
    return out


def assign(args) -> int:
    _, st, _ = collect(args.out_dir)
    parts = assign_batches(st, args.group, args.workers)
    if not parts:
        print(f"{args.group}: nothing left to assign")
    for i, part in enumerate(parts, start=1):
        print(f"worker {i}: group {args.group}; batches {', '.join(part)}")
    return 0


# ── ingest ───────────────────────────────────────────────────────────────────

def _pairwise(x: list[bool], y: list[bool]) -> dict:
    return {"n": len(x), "agreement": agreement(x, y), "kappa": cohen_kappa(x, y),
            "agree": _rate(sum(a == b for a, b in zip(x, y)), len(x)), "table": table2x2(x, y)}


def heldout_gate(hv: dict, n_scored: int, n_heldout: int) -> dict:
    """Pass/fail of the held-out check against HELDOUT_GATE. Incomplete labelling fails."""
    failed = [c for c in LABEL_COLS
              if hv[c]["agree"]["rate"] < (HELDOUT_GATE["update_conflict"] if c == "update_conflict"
                                           else HELDOUT_GATE["each_other_field"])]
    complete = n_scored == n_heldout
    return {"criteria": HELDOUT_GATE, "n_scored": n_scored, "n_heldout": n_heldout,
            "failed_fields": failed, "passed": complete and not failed}


def _six(m: dict) -> tuple:
    return tuple(m[c] for c in LABEL_COLS)


def repeated_text(merged: dict[str, dict], gold: dict[str, dict]) -> dict:
    """How consistently one sentence pair is labelled when it occurs under several pair ids."""
    groups: dict[frozenset, list[dict]] = {}
    for m in merged.values():
        g = gold[m["pair_id"]]
        groups.setdefault(frozenset((g["fact_a"], g["fact_b"])), []).append(m)
    rep_ = [v for v in groups.values() if len(v) > 1]
    cross = [v for v in rep_ if len({m["batch"] for m in v}) > 1]
    same = lambda v: len({_six(m) for m in v}) == 1                      # noqa: E731
    return {"n_rows": len(merged), "n_distinct_texts": len(groups),
            "repeated_texts": _rate(sum(map(same, rep_)), len(rep_)),
            "repeated_in_different_batches": _rate(sum(map(same, cross)), len(cross))}


def parser_slots(merged: dict[str, dict], gold: dict[str, dict]) -> dict:
    """Model labels against the parser's slots, on pairs where both sentences parse."""
    out = {"n_both_parse": 0,
           "same_referent_equals_same_subject": 0, "same_relation_equals_same_template": 0,
           "same_template_and_same_value": 0, "of_which_values_incompatible": 0,
           "same_template_different_value": 0, "of_which_values_compatible": 0}
    for m in merged.values():
        p = gold[m["pair_id"]]["parser"]
        if not p.get("both_parse"):
            continue
        out["n_both_parse"] += 1
        out["same_referent_equals_same_subject"] += m["same_referent"] == bool(p["same_subject"])
        out["same_relation_equals_same_template"] += m["same_relation"] == bool(p["same_relation"])
        if p["same_relation"]:
            if p["same_object"]:
                out["same_template_and_same_value"] += 1
                out["of_which_values_incompatible"] += m["values_incompatible"]
            else:
                out["same_template_different_value"] += 1
                out["of_which_values_compatible"] += not m["values_incompatible"]
    return out


def sentinel_check(sentinels: dict[str, dict], merged: dict[str, dict]) -> dict:
    """Sentinel rows of stage 2 against the stage-1 label of the same pair."""
    ref = {m["pair_id"]: m for m in merged.values() if m["group"] == "stage1"}
    rows = [(s, ref[s["pair_id"]]) for s in sentinels.values() if s["pair_id"] in ref]
    bad = Counter(s["batch"] for s, r in rows if _six(s) != _six(r))
    return {"n": len(rows),
            "all_six_identical": _rate(sum(_six(s) == _six(r) for s, r in rows), len(rows)),
            "update_conflict_identical": _rate(
                sum(s["update_conflict"] == r["update_conflict"] for s, r in rows), len(rows)),
            "n_batches": len({s["batch"] for s, _ in rows}),
            "batches_with_a_mismatch": dict(sorted(bad.items()))}


def score(merged: dict[str, dict], gold: dict[str, dict], human: dict[str, dict] | None,
          heldout_rows: dict[str, dict] | None, sentinels: dict[str, dict] | None = None) -> dict:
    rep: dict = {"annotator": ANNOTATOR, "n_labelled": len(merged),
                 "n_by_group": Counter(m["group"] for m in merged.values())}
    rep["repeated_text"] = repeated_text(merged, gold)
    rep["parser_slots"] = parser_slots(merged, gold)
    if sentinels:
        rep["sentinels"] = sentinel_check(sentinels, merged)

    if human is not None and heldout_rows:
        ids = sorted(h for h in heldout_rows if h in merged)
        if ids:
            rep["heldout_vs_human"] = {
                c: _pairwise([merged[h][c] for h in ids],
                             [human[heldout_rows[h]["pilot_id"]][c] for h in ids])
                for c in LABEL_COLS}
            rep["heldout_vs_human"]["all_six_fields_identical"] = _rate(
                sum(all(merged[h][c] == human[heldout_rows[h]["pilot_id"]][c] for c in LABEL_COLS)
                    for h in ids), len(ids))
            rep["heldout_gate"] = heldout_gate(rep["heldout_vs_human"], len(ids), len(heldout_rows))

    by_tier = {}
    for t in TIERS:
        sel = [m for m in merged.values() if gold[m["pair_id"]]["tier"] == t]
        if not sel:
            continue
        g = [gold[m["pair_id"]] for m in sel]
        upd = [m["update_conflict"] for m in sel]
        by_tier[t] = {
            "n": len(sel), "n_in_tier": sum(1 for x in gold.values() if x["tier"] == t),
            "model_update_yes": sum(upd),
            "model_strict_yes": sum(m["strict_conflict"] for m in sel),
            "update_agrees_with_judge": _rate(
                sum(u == bool(x["judge"]["update_conflict"]) for u, x in zip(upd, g)), len(sel)),
            "update_agrees_with_parser": _rate(
                sum(u == parser_says_update(x) for u, x in zip(upd, g)), len(sel)),
            "update_agrees_with_gold_update": _rate(
                sum(u == bool(x["gold_update"]) for u, x in zip(upd, g)), len(sel)),
            "strict_agrees_with_gold_strict": _rate(
                sum(m["strict_conflict"] == bool(x["gold_strict"]) for m, x in zip(sel, g)), len(sel)),
        }
    rep["by_tier"] = by_tier

    allm = list(merged.values())
    rep["field_vs_judge"] = {
        c: _pairwise([m[c] for m in allm], [bool(gold[m["pair_id"]]["judge"][c]) for m in allm])
        for c in LABEL_COLS} if allm else {}
    rep["rubric_departures"] = Counter(v for m in allm for v in rubric_violations(m))
    return rep


def _f(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, (tuple, list)):
        return "[" + ", ".join(_f(v, nd) for v in x) + "]"
    return str(x)


def render_md(rep: dict, status_rows: list[dict]) -> str:
    L = ["# Model annotator pass — summary", "",
         f"Annotator: {rep['annotator']}. Labels follow a guideline written from the human pilot; "
         "no model weights were changed. These are model labels, not human labels.", "",
         f"Pairs labelled: {rep['n_labelled']} ({dict(rep['n_by_group'])}).", ""]
    c = Counter((s["group"], s["state"]) for s in status_rows)
    L += ["## Coverage", "", "| group | batches done | invalid | missing |", "|---|---|---|---|"]
    for g in sorted({s["group"] for s in status_rows}):
        L.append(f"| {g} | {c[(g, 'done')]} | {c[(g, 'invalid')]} | {c[(g, 'missing')]} |")
    if "heldout_vs_human" in rep:
        hv = rep["heldout_vs_human"]
        L += ["", "## Held-out pilot pairs: model vs the human annotator", "",
              "Pairs the guideline was drafted without. One human annotator; small n.", "",
              "| field | n | agree | Wilson 95% | Cohen κ |", "|---|---|---|---|---|"]
        for f in LABEL_COLS:
            a = hv[f]["agree"]
            L.append(f"| {f} | {a['n']} | {a['k']} | {_f(a['wilson95'])} | {_f(hv[f]['kappa'])} |")
        a = hv["all_six_fields_identical"]
        L.append(f"| all six fields | {a['n']} | {a['k']} | {_f(a['wilson95'])} | — |")
        g = rep["heldout_gate"]
        L += ["", f"Gate (fixed in advance: update_conflict ≥ {g['criteria']['update_conflict']}, "
              f"every other field ≥ {g['criteria']['each_other_field']}; "
              f"{g['n_scored']} of {g['n_heldout']} held-out pairs scored): "
              + ("**passed**." if g["passed"] else
                 f"**not passed** (fields below the bar: {g['failed_fields'] or 'none; labelling incomplete'}).")]
    L += ["", "## By gold tier (`update_conflict` unless stated)", "",
          "| tier | labelled / in tier | model update yes | model strict yes | = judge | = parser "
          "| = gold_update | strict = gold_strict |", "|---|---|---|---|---|---|---|---|"]
    for t, b in rep["by_tier"].items():
        L.append(f"| {t} | {b['n']} / {b['n_in_tier']} | {b['model_update_yes']} | {b['model_strict_yes']} "
                 f"| {_f(b['update_agrees_with_judge']['rate'])} | {_f(b['update_agrees_with_parser']['rate'])} "
                 f"| {_f(b['update_agrees_with_gold_update']['rate'])} "
                 f"| {_f(b['strict_agrees_with_gold_strict']['rate'])} |")
    if rep["field_vs_judge"]:
        L += ["", "## Field-level agreement with the GPT-5-mini judge (all labelled pairs)", "",
              "| field | n | agreement | Cohen κ |", "|---|---|---|---|"]
        for f in LABEL_COLS:
            p = rep["field_vs_judge"][f]
            L.append(f"| {f} | {p['n']} | {_f(p['agreement'])} | {_f(p['kappa'])} |")
    rt, ps = rep["repeated_text"], rep["parser_slots"]
    L += ["", "## Consistency", "",
          f"- {rt['n_rows']} labelled rows are {rt['n_distinct_texts']} distinct sentence pairs "
          "(a pair can occur in several subsets under different ids).",
          f"- Sentence pairs labelled more than once: {rt['repeated_texts']['n']}; identical on all "
          f"six labels in {rt['repeated_texts']['k']}.",
          f"- Of these, labelled in different batches: {rt['repeated_in_different_batches']['n']}; "
          f"identical in {rt['repeated_in_different_batches']['k']}.",
          f"- Pairs where both sentences parse: {ps['n_both_parse']}. `same_referent` equals "
          f"\"same subject string\" in {ps['same_referent_equals_same_subject']}; `same_relation` "
          f"equals \"same template\" in {ps['same_relation_equals_same_template']}.",
          f"- Same template and same value: {ps['same_template_and_same_value']}, of which labelled "
          f"incompatible: {ps['of_which_values_incompatible']}. Same template and different value: "
          f"{ps['same_template_different_value']}, of which labelled compatible (alias or "
          f"containment): {ps['of_which_values_compatible']}."]
    if "sentinels" in rep:
        sc = rep["sentinels"]
        L += ["", "## Stage-2 sentinel rows", "",
              f"{sc['n']} sentinel rows in {sc['n_batches']} batches (stage-1 pairs relabelled under "
              f"new ids). All six labels equal to the stage-1 label: {sc['all_six_identical']['k']} "
              f"({_f(sc['all_six_identical']['rate'])}); `update_conflict` equal: "
              f"{sc['update_conflict_identical']['k']}. Batches with a mismatch: "
              f"{sc['batches_with_a_mismatch'] or 'none'}."]
    L += ["", "## Rows departing from the written rubric's derivation rules", "",
          str(dict(rep["rubric_departures"]) or "none"), ""]
    return "\n".join(L)


def ingest(args) -> int:
    merged, st, sentinels = collect(args.out_dir)
    bad = [s for s in st if s["state"] == "invalid"]
    for s in bad:
        print(f"INVALID {s['group']}/{s['batch']}: {s['error']}", file=sys.stderr)
    if not merged:
        raise SystemExit("no valid label files yet")
    gold = {g["pair_id"]: g for g in read_jsonl(args.gold)}
    hk = args.out_dir / "heldout_key.json"
    human = read_sheet(args.sheet) if args.sheet and pathlib.Path(args.sheet).exists() else None
    rep = score(merged, gold, human, _read_json(hk)["rows"] if hk.exists() else None, sentinels)
    rep["batches"] = st
    _write_csv(args.out_dir / "MODEL_LABELS.csv", ["review_id", "pair_id", "group"] + LABEL_COLS + ["notes"],
               [dict({c: _yn(m[c]) for c in LABEL_COLS}, review_id=rid, pair_id=m["pair_id"],
                     group=m["group"], notes=m["notes"]) for rid, m in sorted(merged.items())])
    _write_json(args.out_dir / "MODEL_ANNOTATION_SUMMARY.json", rep)
    md = render_md(rep, st)
    (args.out_dir / "MODEL_ANNOTATION_SUMMARY.md").write_text(md, encoding="utf-8")
    print(md)
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("split", "batches", "status", "assign", "ingest"):
        p = sub.add_parser(name)
        p.add_argument("--out-dir", type=pathlib.Path, default=OUT)
        p.add_argument("--gold", type=pathlib.Path, default=GOLD)
        p.add_argument("--key", type=pathlib.Path, default=PILOT_KEY)
        p.add_argument("--seed", type=int, default=SEED)
        if name in ("split", "ingest"):
            p.add_argument("--sheet", type=pathlib.Path, default=PILOT_FILLED)
        if name == "split":
            p.add_argument("--n-heldout", type=int, default=N_HELDOUT)
        if name == "assign":
            p.add_argument("--group", default="stage1")
            p.add_argument("--workers", type=int, default=9)
        if name == "batches":
            p.add_argument("--stage", choices=["1", "2", "all"], default="1")
            p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
            p.add_argument("--n-sentinel", type=int, default=N_SENTINEL,
                           help="sentinel rows per stage-2 batch (stage 1 has none)")
    args = ap.parse_args(argv)
    return {"split": split, "batches": batches, "status": status, "assign": assign,
            "ingest": ingest}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
