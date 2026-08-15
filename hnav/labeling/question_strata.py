#!/usr/bin/env python3
"""Question strata: does the queried key carry a conflict at all?  [T12]

**Offline only.** Reads the benchmark's ``questions``/``answers`` and the
committed run artifacts under ``stage0_results/t4_s2_evidence/``. Nothing under
``hnav/core/`` or ``hnav/adapters/`` may import this module; the AST scan in
``hnav/tests/test_leakage_audit.py`` enforces that for the whole tree.

Why this exists
---------------
The primary arena's headline accuracy (``m3_headroom.json``: 0.33 / 0.47 / 0.44
/ 0.20) is an average over two populations that behave nothing alike:

* **unique** — the queried ``(relation, subject)`` key has exactly one distinct
  value in the context. There is no conflict to resolve; the question is a
  plain lookup.
* **conflicted** — the key carries two or more distinct values, so answering
  requires applying the rule the prompt states ("the newer fact has larger
  serial number").
* **unmatched** — no key whose subject occurs in the question also carries the
  expected answer among its values. Two questions in ``sh_262k``; none on the
  calibration split.

Splitting the eight committed ``sh_6k`` runs this way shows the average is a
mixture: the unique stratum is answered perfectly and the conflicted stratum is
answered almost never. The error taxonomy says *how* it fails — overwhelmingly
by emitting the superseded value **of the right key**, not by retrieving the
wrong key and not by refusing.

Classification rule (imported, not re-derived)
----------------------------------------------
``hnav.labeling.counterfactual.map_questions_to_keys`` — "the key whose subject
appears in the question and whose object set intersects the expected answer" —
is the same rule the committed ``gold_rule.py`` established, and it is imported
here rather than re-implemented. The two differ in tie-break only:
``gold_rule.py`` searches conflicted keys first and falls back to all keys,
``map_questions_to_keys`` searches all keys in one pass. On all 400 single-hop
questions the two agree exactly; ``hnav/tests/test_question_strata.py`` pins that
agreement by re-implementing ``gold_rule``'s form as an independent oracle.
Facts are parsed by the validated ``conflict_analysis.parse`` (99.5%+ template
coverage), imported through the same path.

    python hnav/labeling/question_strata.py             # table + JSON
    python hnav/labeling/question_strata.py --no-write  # table only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.labeling.conflict_analysis import parse as parse_fact  # noqa: E402
from hnav.labeling.counterfactual import (map_questions_to_keys,  # noqa: E402
                                          normalize_answer, substring_exact_match)

DATA = REPO / "In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/data/Conflict_Resolution.json"
EVIDENCE = REPO / "stage0_results/t4_s2_evidence"
M3 = REPO / "stage0_results/final/m3_headroom.json"
OUT = REPO / "stage0_results/question_strata.json"

STRATA = ("unique", "conflicted", "unmatched")
ERROR_CLASSES = ("stale_value", "off_list", "empty")
SINGLE_HOP_PREFIX = "factconsolidation_sh_"

FACT_RE_LINE = re.compile(r"^\s*(\d+)\.\s+(.*)$", re.M)


# ── parsing ──────────────────────────────────────────────────────────────────
def key_members(item: dict) -> dict[tuple[str, str], list[tuple[int, str, str]]]:
    """``(relation, subject) -> [(serial, fact_text, object)]``, context order.

    The raw ``context`` is newline-separated ("Here is a list of facts:\\n0. ..."),
    so the line-anchored form is exact here — this is the raw dataset field, not
    a memorize chunk that has been through the benchmark's sentence joiner.
    """
    groups: dict[tuple[str, str], list[tuple[int, str, str]]] = {}
    for num, txt in FACT_RE_LINE.findall(item.get("context", "")):
        p = parse_fact(txt)
        if p is None:
            continue
        rel, subj, obj = p
        groups.setdefault((rel, subj), []).append((int(num), txt, obj))
    return groups


def stratum_of(record: dict) -> str:
    """``unique`` / ``conflicted`` / ``unmatched`` for one mapped question."""
    if record.get("key") is None:
        return "unmatched"
    return "conflicted" if record.get("conflicted") else "unique"


def classify_questions(item: dict) -> list[dict]:
    """Every question of one subset, stratified, with the key's value inventory.

    Extends ``map_questions_to_keys`` with what the error taxonomy needs:
    ``other_values`` (the key's values that are *not* the expected answer) and
    ``gold_is_latest`` (whether the expected answer sits on the highest serial,
    i.e. whether the benchmark's own stated rule would produce it).
    """
    groups = key_members(item)
    out = []
    for rec in map_questions_to_keys(item):
        rec = dict(rec)
        rec["stratum"] = stratum_of(rec)
        key = tuple(rec["key"]) if rec["key"] else None
        members = groups.get(key, []) if key else []
        truths = set(rec["truths"])
        seen: list[str] = []
        for _, _, obj in members:
            if obj.lower() not in truths and obj not in seen:
                seen.append(obj)
        rec["other_values"] = seen
        rec["n_members"] = len(members)
        rec["latest_serial"] = max((s for s, _, _ in members), default=None)
        rec["gold_is_latest"] = bool(
            members and rec["target_serial"] is not None
            and rec["target_serial"] == rec["latest_serial"])
        out.append(rec)
    return out


# ── error taxonomy ───────────────────────────────────────────────────────────
def error_class(output: str, record: dict) -> str:
    """Classify one **incorrect** model output for one question.

    ``empty``        nothing survives the evaluator's normalization;
    ``stale_value``  the output contains a non-expected value **of the same
                     key** — the model found the right key and picked a
                     superseded value from it;
    ``off_list``     anything else: a value that is not on the queried key's
                     list at all (a different key's object, or a world-knowledge
                     answer that never appears under this key).

    Substring containment with the benchmark's own ``normalize_answer`` is used
    on purpose: it is the same comparison ``substring_exact_match`` makes for
    the expected answer, so "correct" and "stale" are decided on one scale.
    """
    pred = normalize_answer(output or "")
    if not pred.strip():
        return "empty"
    for value in record.get("other_values", ()):
        norm = normalize_answer(value)
        if norm and norm in pred:
            return "stale_value"
    return "off_list"


# ── run artifacts ────────────────────────────────────────────────────────────
def subset_of_run(payload: dict) -> str:
    """Subset short name, taken from the run's own ``dataset_config``."""
    full = payload.get("dataset_config", {}).get("sub_dataset", "")
    return full.replace("factconsolidation_", "") or "unknown"


def score_run(payload: dict, records: list[dict]) -> dict:
    """Per-stratum accuracy and error taxonomy for one committed run.

    Grades are **recomputed** with H-Nav's transcription of the evaluator and
    compared against the ``substring_exact_match`` field the benchmark itself
    wrote; the agreement count is reported rather than assumed.
    """
    per = {s: {"n": 0, "correct": 0, "errors": Counter()} for s in STRATA}
    disagree, id_mismatch, off_list_samples = 0, 0, []
    sub = payload.get("dataset_config", {}).get("sub_dataset", "")

    for row in payload.get("data", []):
        qi = row.get("query_id")
        if qi is None or qi >= len(records):
            id_mismatch += 1
            continue
        if row.get("qa_pair_id") not in (None, f"{sub}_no{qi}"):
            id_mismatch += 1
        rec = records[qi]
        output = row.get("parsed_output", row.get("output", "")) or ""
        ok = substring_exact_match(output, rec["truths"])
        if bool(row.get("substring_exact_match")) != ok:
            disagree += 1
        bucket = per[rec["stratum"]]
        bucket["n"] += 1
        if ok:
            bucket["correct"] += 1
        else:
            cls = error_class(output, rec)
            bucket["errors"][cls] += 1
            if cls == "off_list":
                off_list_samples.append(
                    {"index": qi, "output": output, "truths": rec["truths"],
                     "other_values": rec["other_values"]})

    strata = {}
    for s in STRATA:
        b = per[s]
        strata[s] = {
            "n": b["n"], "correct": b["correct"],
            "accuracy": (b["correct"] / b["n"]) if b["n"] else None,
            "errors": {c: b["errors"].get(c, 0) for c in ERROR_CLASSES},
        }
    n = sum(per[s]["n"] for s in STRATA)
    correct = sum(per[s]["correct"] for s in STRATA)
    return {
        "subset": subset_of_run(payload),
        "n_rows": n,
        "accuracy_overall": (correct / n) if n else None,
        "strata": strata,
        "grade_check": {"n_compared": n, "n_disagreements": disagree,
                        "n_id_mismatches": id_mismatch},
        "off_list_outputs": off_list_samples,
        "recorded_averaged_substring_exact_match":
            payload.get("averaged_metrics", {}).get("substring_exact_match"),
    }


def load_runs(evidence_dir: Path = EVIDENCE) -> list[tuple[str, Path, dict]]:
    """``[(run_name, path, payload)]`` for every ``*_results.json`` present."""
    runs = []
    for path in sorted(Path(evidence_dir).glob("*_results.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        runs.append((path.name[: -len("_results.json")], path, payload))
    return runs


# ── implied conflicted-only accuracy from M3 ─────────────────────────────────
def implied_conflicted_accuracy(acc_native: float, n_unique: int,
                                n_conflicted: int, n_total: int) -> float | None:
    """Back out conflicted-only accuracy from a pooled accuracy.

    Assumes every unique-stratum question is answered correctly — measured to
    hold exactly (26/26) in all eight committed ``sh_6k`` runs, and an
    **assumption** everywhere else. A negative result falsifies the assumption
    for that subset and is returned as-is rather than clipped to zero.
    """
    if acc_native is None or not n_conflicted:
        return None
    return (acc_native * n_total - n_unique) / n_conflicted


def m3_native_accuracy(path: Path = M3) -> dict[str, float]:
    if not Path(path).exists():
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {row["subset"]: row.get("read", {}).get("accuracy_native")
            for row in payload if isinstance(row, dict) and "subset" in row}


# ── provenance ───────────────────────────────────────────────────────────────
def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


# ── assembly ─────────────────────────────────────────────────────────────────
def build(data_path: Path = DATA, evidence_dir: Path = EVIDENCE,
          m3_path: Path = M3, subsets: list[str] | None = None) -> dict:
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    m3 = m3_native_accuracy(m3_path)

    by_subset: dict[str, list[dict]] = {}
    subset_rows = []
    for item in data:
        full = item["metadata"]["qa_pair_ids"][0].rsplit("_no", 1)[0]
        if not full.startswith(SINGLE_HOP_PREFIX):
            continue
        name = full.replace("factconsolidation_", "")
        if subsets and name not in subsets:
            continue
        records = classify_questions(item)
        by_subset[name] = records
        counts = Counter(r["stratum"] for r in records)
        acc = m3.get(name)
        subset_rows.append({
            "subset": name,
            "n_questions": len(records),
            "counts": {s: counts.get(s, 0) for s in STRATA},
            "indices": {s: [r["index"] for r in records if r["stratum"] == s]
                        for s in STRATA},
            "n_conflicted_gold_is_latest":
                sum(1 for r in records
                    if r["stratum"] == "conflicted" and r["gold_is_latest"]),
            "m3_accuracy_native": acc,
            "implied_conflicted_only_accuracy": implied_conflicted_accuracy(
                acc, counts.get("unique", 0), counts.get("conflicted", 0),
                len(records)),
        })
    for row in subset_rows:
        imp = row["implied_conflicted_only_accuracy"]
        row["implied_assumption_violated"] = bool(imp is not None and imp < 0)

    runs = []
    for name, path, payload in load_runs(evidence_dir):
        sub = subset_of_run(payload)
        if sub not in by_subset:
            continue
        scored = score_run(payload, by_subset[sub])
        scored["run"] = name
        scored["file"] = str(Path(path).relative_to(REPO)).replace("\\", "/")
        runs.append(scored)

    totals = Counter()
    for r in runs:
        for s in STRATA:
            for c in ERROR_CLASSES:
                totals[c] += r["strata"][s]["errors"][c]
    uniq_acc = [r["strata"]["unique"]["accuracy"] for r in runs
                if r["strata"]["unique"]["n"]]
    conf_acc = [r["strata"]["conflicted"]["accuracy"] for r in runs
                if r["strata"]["conflicted"]["n"]]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git_head(),
        "provenance": {
            "dataset_file": str(Path(data_path).relative_to(REPO)).replace("\\", "/"),
            "dataset_sha256": _sha256(data_path),
            "evidence_dir": str(Path(evidence_dir).relative_to(REPO)).replace("\\", "/"),
            "n_run_files": len(runs),
            "fact_parser": "hnav.labeling.conflict_analysis.parse (imported; validated 99.5%+ coverage)",
            "question_to_key_rule": (
                "hnav.labeling.counterfactual.map_questions_to_keys (imported) — "
                "subject-in-question AND expected-answer-in-key-values, the rule "
                "gold_rule.py established; agreement with gold_rule's "
                "conflicted-first form is pinned on all 400 single-hop questions "
                "by hnav/tests/test_question_strata.py"),
            "grader": "hnav.labeling.counterfactual.substring_exact_match (recomputed, cross-checked against each run's own field)",
            "m3_file": str(Path(m3_path).relative_to(REPO)).replace("\\", "/")
                       if Path(m3_path).exists() else None,
            "m3_caveat": (
                "m3_headroom.py grades with H-Nav's own counterfactual prompt "
                "(labeling.counterfactual.build_prompt), NOT the benchmark's "
                "templated query used by the t4_s2 evidence runs. The implied "
                "conflicted-only accuracies are therefore m3-harness numbers."),
        },
        "definitions": {
            "unique": "queried (relation, subject) key has exactly one distinct value in the context",
            "conflicted": "queried key has >= 2 distinct values",
            "unmatched": "no key with the question's subject carries the expected answer",
            "stale_value": "incorrect output contains a non-expected value OF THE SAME KEY",
            "off_list": "incorrect output contains no value of the queried key",
            "empty": "output is empty after the evaluator's normalization",
        },
        "subsets": subset_rows,
        "runs": runs,
        "aggregate": {
            "n_runs": len(runs),
            "unique_accuracy_min": min(uniq_acc) if uniq_acc else None,
            "unique_accuracy_max": max(uniq_acc) if uniq_acc else None,
            "conflicted_accuracy_min": min(conf_acc) if conf_acc else None,
            "conflicted_accuracy_max": max(conf_acc) if conf_acc else None,
            "errors_total": {c: totals[c] for c in ERROR_CLASSES},
            "n_grade_disagreements":
                sum(r["grade_check"]["n_disagreements"] for r in runs),
        },
    }


# ── reporting ────────────────────────────────────────────────────────────────
def format_table(payload: dict) -> str:
    lines = ["=" * 92,
             " QUESTION STRATA - does the queried key carry a conflict at all?",
             "=" * 92, "",
             f"{'subset':<10}{'n':>5}{'unique':>9}{'confl':>8}{'unmatch':>9}"
             f"{'gold=latest':>13}{'m3 acc':>9}{'implied confl-only':>21}"]
    for row in payload["subsets"]:
        c = row["counts"]
        acc = row["m3_accuracy_native"]
        imp = row["implied_conflicted_only_accuracy"]
        flag = "  (!)" if row.get("implied_assumption_violated") else ""
        lines.append(
            f"{row['subset']:<10}{row['n_questions']:>5}{c['unique']:>9}"
            f"{c['conflicted']:>8}{c['unmatched']:>9}"
            f"{row['n_conflicted_gold_is_latest']:>13}"
            f"{(f'{acc:.3f}' if acc is not None else '-'):>9}"
            f"{(f'{imp:.3f}' if imp is not None else '-'):>21}{flag}")

    lines += ["", "-" * 92,
              " COMMITTED RUNS (stage0_results/t4_s2_evidence) - accuracy by stratum,"
              " taxonomy of errors", "-" * 92,
              f"{'run':<16}{'subset':<9}{'unique':>14}{'conflicted':>15}"
              f"{'stale':>8}{'off_list':>10}{'empty':>7}{'grade d':>9}"]
    for r in payload["runs"]:
        u, c = r["strata"]["unique"], r["strata"]["conflicted"]
        errs = Counter()
        for s in STRATA:
            for k, v in r["strata"][s]["errors"].items():
                errs[k] += v
        u_cell = "{}/{}".format(u["correct"], u["n"])
        c_cell = "{}/{}".format(c["correct"], c["n"])
        u_acc = "-" if u["accuracy"] is None else "{:.2f}".format(u["accuracy"])
        c_acc = "-" if c["accuracy"] is None else "{:.2f}".format(c["accuracy"])
        lines.append(
            f"{r['run']:<16}{r['subset']:<9}{u_cell:>9}{u_acc:>5}"
            f"{c_cell:>10}{c_acc:>5}"
            f"{errs['stale_value']:>8}{errs['off_list']:>10}{errs['empty']:>7}"
            f"{r['grade_check']['n_disagreements']:>9}")

    agg = payload["aggregate"]
    if agg["n_runs"]:
        lines += ["", " {} runs. unique accuracy {}-{}, conflicted accuracy "
                      "{:.3f}-{:.3f}".format(
                          agg["n_runs"], agg["unique_accuracy_min"],
                          agg["unique_accuracy_max"],
                          agg["conflicted_accuracy_min"],
                          agg["conflicted_accuracy_max"])]
    lines.append(f" errors across all runs: {agg['errors_total']}   "
                 f"(grade disagreements vs the benchmark's own field: "
                 f"{agg['n_grade_disagreements']})")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--subsets", nargs="*", default=None)
    ap.add_argument("--evidence-dir", default=str(EVIDENCE))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    payload = build(evidence_dir=Path(args.evidence_dir), subsets=args.subsets)
    print(format_table(payload))
    if not args.no_write:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        print(f"\n wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
