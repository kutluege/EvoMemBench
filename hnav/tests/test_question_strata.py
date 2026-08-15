"""Question strata and the error taxonomy.  [T12]

Three levels of check, matching the standard the rest of the suite is held to:

1. **Synthetic, known by construction.** Hand-built contexts where the answer
   is determined by the fixture, not by the classifier: a key with two distinct
   values is conflicted, a key with one is unique, a question whose subject
   matches nothing is unmatched. Includes the case that separates the right
   rule from the plausible-but-wrong one — the same value written twice is a
   *duplicate*, not a conflict.
2. **Independent oracle on the real artifacts.** ``_oracle_counts`` below goes
   from the raw dataset JSON and the raw run JSON to per-run, per-stratum
   accuracy and error counts using ``gold_rule.py``'s conflicted-first matching
   form — a different code path from ``map_questions_to_keys`` — and the two
   must agree exactly on all 400 single-hop questions and all 8 committed runs.
3. **Negative controls.** A deliberately mislabeled fixture must be *rejected*
   by the same assertion helper the positive tests use, and an output carrying a
   different key's value must not be scored as a stale value of this one. A
   classifier that cannot fail proves nothing.

Plus regression pins on the numbers this task exists to establish: sh_6k is
26 unique / 74 conflicted, the unique stratum is 26/26 in every one of the eight
committed runs, and 572 of the 575 conflicted-stratum errors are the stale value
of the correct key.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

import pytest

from hnav.labeling.conflict_analysis import parse as parse_fact
from hnav.labeling.counterfactual import normalize_answer, substring_exact_match
from hnav.labeling.question_strata import (DATA, ERROR_CLASSES, EVIDENCE, STRATA,
                                           build, classify_questions, error_class,
                                           implied_conflicted_accuracy, key_members,
                                           load_runs, score_run, stratum_of,
                                           subset_of_run)

# ── synthetic fixtures: the classification is fixed by construction ──────────
SYNTHETIC = {
    "context": (
        "Here is a list of facts:\n"
        "0. The capital of Atlantis is Poseidonis.\n"
        "1. The capital of Numenor is Armenelos.\n"
        "2. The capital of Atlantis is Kallipolis.\n"
        "3. The chairperson of Fatah is Ada Lovelace.\n"
    ),
    # index 0: key has TWO distinct values          -> conflicted
    # index 1: key has ONE value                    -> unique
    # index 2: key has ONE value, different template-> unique
    # index 3: no subject in the context matches    -> unmatched
    "questions": ["What is the capital of Atlantis?",
                  "What is the capital of Numenor?",
                  "Who is the chairperson of Fatah?",
                  "Who won the 1998 world cup?"],
    "answers": [["Kallipolis"], ["Armenelos"], ["Ada Lovelace"], ["France"]],
}
SYNTHETIC_EXPECTED = ["conflicted", "unique", "unique", "unmatched"]

DUPLICATE = {
    # the SAME value twice: two facts, one distinct value. A classifier that
    # counts facts calls this conflicted; the rule counts distinct values.
    "context": ("Here is a list of facts:\n"
                "0. The capital of Utopia is Amaurot.\n"
                "1. The capital of Utopia is Amaurot.\n"),
    "questions": ["What is the capital of Utopia?"],
    "answers": [["Amaurot"]],
}


def assert_strata(item: dict, expected: list[str]) -> None:
    """The single assertion helper both the positive tests and the negative
    control go through — so the negative control proves *this* check can fail."""
    got = [r["stratum"] for r in classify_questions(item)]
    assert got == expected, f"strata {got} != expected {expected}"


def test_synthetic_classification_is_known_by_construction():
    assert_strata(SYNTHETIC, SYNTHETIC_EXPECTED)


def test_conflicted_record_carries_the_full_value_inventory():
    rec = classify_questions(SYNTHETIC)[0]
    assert rec["key"][1] == "Atlantis"
    assert rec["n_members"] == 2
    assert rec["other_values"] == ["Poseidonis"]        # gold excluded
    assert rec["target_serial"] == 2 and rec["latest_serial"] == 2
    assert rec["gold_is_latest"] is True


def test_unique_record_has_no_other_values():
    rec = classify_questions(SYNTHETIC)[1]
    assert rec["stratum"] == "unique" and rec["other_values"] == []


def test_unmatched_record_has_no_key_at_all():
    rec = classify_questions(SYNTHETIC)[3]
    assert rec["key"] is None and rec["target_serial"] is None
    assert rec["other_values"] == [] and rec["latest_serial"] is None
    assert stratum_of(rec) == "unmatched"


def test_duplicate_values_are_not_a_conflict():
    """The discrimination the whole analysis rests on: >=2 *facts* is not the
    rule, >=2 *distinct values* is."""
    rec = classify_questions(DUPLICATE)[0]
    assert rec["n_members"] == 2, "the fixture really does contain two facts"
    assert rec["stratum"] == "unique"


def test_key_members_indexes_every_parsable_fact_in_context_order():
    groups = key_members(SYNTHETIC)
    atlantis = [k for k in groups if k[1] == "Atlantis"][0]
    assert [s for s, _, _ in groups[atlantis]] == [0, 2]
    assert len(groups) == 3


# ── NEGATIVE CONTROLS ────────────────────────────────────────────────────────
def test_negative_control_a_mislabeled_fixture_is_rejected():
    """Swap two labels and the same helper the positive test uses must fail.

    Without this, ``assert_strata`` passing would be evidence of nothing.
    """
    mislabeled = ["unique", "conflicted", "unique", "unmatched"]
    assert mislabeled != SYNTHETIC_EXPECTED
    with pytest.raises(AssertionError):
        assert_strata(SYNTHETIC, mislabeled)


def test_negative_control_a_different_keys_value_is_not_a_stale_value():
    """``Armenelos`` is a real value in the context — of a *different* key. The
    taxonomy must call that ``off_list``; calling it ``stale_value`` would
    inflate the headline finding."""
    rec = classify_questions(SYNTHETIC)[0]
    assert error_class("Armenelos", rec) == "off_list"


def test_negative_control_a_corrupted_context_changes_the_verdict():
    """Rewrite the conflicting fact to carry the gold value and the question
    stops being conflicted — the classifier tracks the data, not the fixture."""
    flattened = dict(SYNTHETIC)
    flattened["context"] = SYNTHETIC["context"].replace(
        "0. The capital of Atlantis is Poseidonis.",
        "0. The capital of Atlantis is Kallipolis.")
    assert classify_questions(flattened)[0]["stratum"] == "unique"


# ── error taxonomy, oracle written out by hand ───────────────────────────────
def test_error_class_cases():
    conflicted = classify_questions(SYNTHETIC)[0]
    unique = classify_questions(SYNTHETIC)[1]

    assert error_class("Poseidonis", conflicted) == "stale_value"
    # normalized substring containment, exactly as the evaluator compares golds
    assert error_class("It is Poseidonis, I think.", conflicted) == "stale_value"
    assert error_class("the Poseidonis", conflicted) == "stale_value"
    assert error_class("Byzantium", conflicted) == "off_list"
    assert error_class("", conflicted) == "empty"
    assert error_class("  ...  ", conflicted) == "empty", \
        "punctuation-only survives nothing after normalization"
    # a unique key has no non-gold value, so every miss is off_list
    assert error_class("Byzantium", unique) == "off_list"


def _fake_run(outputs: list[str], sub_dataset: str = "factconsolidation_syn") -> dict:
    """A run artifact in the benchmark's own shape, with chosen outputs."""
    truths = [a for a in SYNTHETIC["answers"]]
    return {
        "dataset_config": {"sub_dataset": sub_dataset},
        "averaged_metrics": {"substring_exact_match": None},
        "data": [{"query_id": i, "qa_pair_id": f"{sub_dataset}_no{i}",
                  "parsed_output": o, "answer": truths[i],
                  "substring_exact_match": substring_exact_match(o, truths[i])}
                 for i, o in enumerate(outputs)],
    }


def test_score_run_against_a_hand_written_expectation():
    records = classify_questions(SYNTHETIC)
    scored = score_run(_fake_run([
        "Poseidonis",     # q0 conflicted -> wrong, stale value of the same key
        "Armenelos",      # q1 unique     -> correct
        "Grace Hopper",   # q2 unique     -> wrong, off_list
        "",               # q3 unmatched  -> wrong, empty
    ]), records)

    # written out by hand from the four lines above, not computed
    assert scored["strata"]["conflicted"] == {
        "n": 1, "correct": 0, "accuracy": 0.0,
        "errors": {"stale_value": 1, "off_list": 0, "empty": 0}}
    assert scored["strata"]["unique"] == {
        "n": 2, "correct": 1, "accuracy": 0.5,
        "errors": {"stale_value": 0, "off_list": 1, "empty": 0}}
    assert scored["strata"]["unmatched"] == {
        "n": 1, "correct": 0, "accuracy": 0.0,
        "errors": {"stale_value": 0, "off_list": 0, "empty": 1}}
    assert scored["accuracy_overall"] == 0.25
    assert scored["grade_check"]["n_disagreements"] == 0
    assert [s["output"] for s in scored["off_list_outputs"]] == ["Grace Hopper"]


def test_score_run_reports_disagreement_with_a_wrong_recorded_grade():
    """The cross-check against the benchmark's own field must be able to fire."""
    payload = _fake_run(["Poseidonis", "Armenelos", "Grace Hopper", ""])
    payload["data"][0]["substring_exact_match"] = True      # a lie
    scored = score_run(payload, classify_questions(SYNTHETIC))
    assert scored["grade_check"]["n_disagreements"] == 1


# ── closed form ──────────────────────────────────────────────────────────────
def test_implied_conflicted_accuracy_is_the_stated_algebra():
    # (acc * n - n_unique) / n_conflicted, i.e. all unique questions correct
    assert implied_conflicted_accuracy(0.33, 26, 74, 100) == pytest.approx(7 / 74)
    assert implied_conflicted_accuracy(0.47, 35, 65, 100) == pytest.approx(12 / 65)
    assert implied_conflicted_accuracy(0.20, 21, 77, 100) == pytest.approx(-1 / 77)
    assert implied_conflicted_accuracy(None, 26, 74, 100) is None
    assert implied_conflicted_accuracy(0.33, 26, 0, 26) is None


# ── the real thing ───────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def payload():
    if not DATA.exists():
        pytest.skip(f"missing {DATA}")
    return build()


def test_real_subset_strata_counts_are_pinned(payload):
    """Regression pin. These four rows are the finding."""
    got = {r["subset"]: r["counts"] for r in payload["subsets"]}
    assert got == {
        "sh_6k":   {"unique": 26, "conflicted": 74, "unmatched": 0},
        "sh_32k":  {"unique": 35, "conflicted": 65, "unmatched": 0},
        "sh_64k":  {"unique": 34, "conflicted": 66, "unmatched": 0},
        "sh_262k": {"unique": 21, "conflicted": 77, "unmatched": 2},
    }


def test_every_run_answers_the_unique_stratum_perfectly(payload):
    assert len(payload["runs"]) == 8, "eight committed sh_6k runs"
    for run in payload["runs"]:
        u = run["strata"]["unique"]
        assert (u["correct"], u["n"]) == (26, 26), f"{run['run']}: {u}"


def test_the_conflicted_stratum_is_near_zero_in_every_run(payload):
    for run in payload["runs"]:
        c = run["strata"]["conflicted"]
        assert c["n"] == 74
        assert 0 <= c["correct"] <= 5, f"{run['run']}: {c}"


def test_the_error_taxonomy_totals_are_pinned(payload):
    assert payload["aggregate"]["errors_total"] == {
        "stale_value": 572, "off_list": 3, "empty": 0}


def test_recomputed_grades_agree_with_the_benchmarks_own_field(payload):
    assert payload["aggregate"]["n_grade_disagreements"] == 0
    total = sum(r["grade_check"]["n_compared"] for r in payload["runs"])
    assert total == 800, "8 runs x 100 questions"
    assert all(r["grade_check"]["n_id_mismatches"] == 0 for r in payload["runs"])


def test_overall_accuracy_matches_the_runs_own_averaged_metric(payload):
    for run in payload["runs"]:
        recorded = run["recorded_averaged_substring_exact_match"]
        assert recorded == pytest.approx(100 * run["accuracy_overall"], abs=1e-6)


# ── independent oracle: raw files -> counts, via gold_rule's matching form ───
def _oracle_records(item: dict) -> list[dict]:
    """``gold_rule.py``'s rule, re-implemented here: search CONFLICTED keys
    first, fall back to all keys. Different traversal from
    ``map_questions_to_keys``; must produce the same labels."""
    groups: dict = defaultdict(list)
    for num, txt in re.findall(r"^\s*(\d+)\.\s+(.*)$", item["context"], re.M):
        p = parse_fact(txt)
        if p:
            groups[(p[0], p[1])].append((int(num), p[2]))
    conflicts = {k: v for k, v in groups.items() if len({o for _, o in v}) > 1}

    out = []
    for q, ans in zip(item["questions"], item["answers"]):
        gold = {str(a).lower() for a in
                (ans if isinstance(ans, (list, tuple)) else [ans])}
        hit = None
        for source, label in ((conflicts, "conflicted"), (groups, "unique")):
            for (rel, subj), vals in source.items():
                if subj.lower() in q.lower() and any(o.lower() in gold for _, o in vals):
                    hit = (label, (rel, subj), vals)
                    break
            if hit:
                break
        if hit is None:
            out.append({"stratum": "unmatched", "gold": gold, "others": []})
            continue
        label, _, vals = hit
        out.append({"stratum": label, "gold": gold,
                    "others": [o for _, o in vals if o.lower() not in gold]})
    return out


def _oracle_counts(item: dict, run_payload: dict) -> dict:
    per = {s: {"n": 0, "correct": 0, "errors": Counter()} for s in STRATA}
    recs = _oracle_records(item)
    for row in run_payload["data"]:
        rec = recs[row["query_id"]]
        out = row["parsed_output"]
        bucket = per[rec["stratum"]]
        bucket["n"] += 1
        if any(normalize_answer(g) in normalize_answer(out) for g in rec["gold"]):
            bucket["correct"] += 1
            continue
        if not normalize_answer(out).strip():
            bucket["errors"]["empty"] += 1
        elif any(normalize_answer(o) and normalize_answer(o) in normalize_answer(out)
                 for o in rec["others"]):
            bucket["errors"]["stale_value"] += 1
        else:
            bucket["errors"]["off_list"] += 1
    return per


def test_module_agrees_with_the_independent_oracle_on_every_committed_run(payload):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = {it["metadata"]["qa_pair_ids"][0].rsplit("_no", 1)[0]
             .replace("factconsolidation_", ""): it for it in data}

    runs = {name: p for name, _, p in load_runs(EVIDENCE)}
    assert runs, "no committed run artifacts found"
    for run in payload["runs"]:
        item = items[run["subset"]]
        oracle = _oracle_counts(item, runs[run["run"]])
        for s in STRATA:
            assert run["strata"][s]["n"] == oracle[s]["n"], (run["run"], s)
            assert run["strata"][s]["correct"] == oracle[s]["correct"], (run["run"], s)
            for c in ERROR_CLASSES:
                assert run["strata"][s]["errors"][c] == oracle[s]["errors"].get(c, 0), \
                    (run["run"], s, c)


def test_module_agrees_with_the_independent_oracle_on_all_400_questions():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    n = 0
    for item in data:
        name = item["metadata"]["qa_pair_ids"][0].rsplit("_no", 1)[0]
        if not name.startswith("factconsolidation_sh_"):
            continue
        mine = [r["stratum"] for r in classify_questions(item)]
        theirs = [r["stratum"] for r in _oracle_records(item)]
        assert mine == theirs, name
        n += len(mine)
    assert n == 400


def test_subset_of_run_reads_the_runs_own_config():
    assert subset_of_run({"dataset_config": {"sub_dataset": "factconsolidation_sh_6k"}}) \
        == "sh_6k"
    assert subset_of_run({}) == "unknown"
