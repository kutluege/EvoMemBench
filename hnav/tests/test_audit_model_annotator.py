"""Model annotator pass: split, blind batches, label validation, scoring.

Counts and agreement figures are worked out by hand in each test, not read
back from the module's own output.
"""
from __future__ import annotations

import csv
import gzip
import json

import pytest

from hnav.labeling import audit_model_annotator as ma
from hnav.labeling.audit_human_review import LABEL_COLS, SHEET_COLS

YES6 = dict.fromkeys(LABEL_COLS, "yes")
NO6 = dict.fromkeys(LABEL_COLS, "no")


def _gold_row(i: int, tier: str, in_eval: bool, judge_update: bool, same_key: bool) -> dict:
    return {"pair_id": f"s:{i}-{i + 1}", "subset": "sh_6k", "tier": tier, "in_eval_set": in_eval,
            "gold_update": tier in ("core", "update_only_fork"), "gold_strict": tier == "core",
            "fact_a": f"Item {i} has value left.", "fact_b": f"Item {i} has value right.",
            "judge": dict({c: judge_update for c in LABEL_COLS}),
            "parser": {"same_key": same_key, "both_parse": True, "same_subject": same_key,
                       "same_relation": True, "same_object": False}}


def _gold() -> list[dict]:
    rows, i = [], 0
    for tier, n, in_eval, ju, sk in [("core", 12, True, True, True),
                                     ("update_only_fork", 8, True, False, True),
                                     ("rejected", 2, False, False, True),
                                     ("discovered_unverified", 4, False, True, False),
                                     ("negative", 20, True, False, False),
                                     ("negative", 30, False, False, False)]:
        for _ in range(n):
            rows.append(_gold_row(i, tier, in_eval, ju, sk))
            i += 10
    return rows


def _setup(tmp_path, pilot_n_per_tier=None):
    """Write a gold file, a pilot key and a filled pilot sheet. Returns paths and rows."""
    gold = _gold()
    gp = tmp_path / "gold.jsonl.gz"
    with gzip.open(gp, "wt", encoding="utf-8") as f:
        for g in gold:
            f.write(json.dumps(g) + "\n")
    take = pilot_n_per_tier or {"core": 2, "update_only_fork": 4, "rejected": 1,
                                "discovered_unverified": 2, "negative": 1}
    pilot, seen = [], dict.fromkeys(take, 0)
    for g in gold:
        if seen[g["tier"]] < take[g["tier"]] and g["in_eval_set"] == (g["tier"] in ("core", "update_only_fork", "negative")):
            seen[g["tier"]] += 1
            pilot.append(g)
    key = {"rows": {f"P{i:03d}": {"pair_id": g["pair_id"], "tier": g["tier"], "stratum": "x"}
                    for i, g in enumerate(pilot)}}
    kp = tmp_path / "pilot_key.json"
    kp.write_text(json.dumps(key), encoding="utf-8")
    sp = tmp_path / "pilot_filled.csv"
    with open(sp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS)
        w.writeheader()
        for i, g in enumerate(pilot):
            lab = YES6 if g["tier"] == "core" else NO6
            w.writerow(dict(lab, review_id=f"P{i:03d}", subset="sh_6k", fact_a=g["fact_a"],
                            fact_b=g["fact_b"], notes="n" if i == 0 else ""))
    return gold, gp, kp, sp, key


def _labels(path, rows: dict[str, dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ma.OUT_COLS)
        w.writeheader()
        for rid, lab in rows.items():
            w.writerow(dict(lab, review_id=rid, notes=""))


def test_stage_partition_covers_every_pair_once_and_excludes_the_pilot(tmp_path):
    gold, *_ , key = _setup(tmp_path)
    pilot = {r["pair_id"] for r in key["rows"].values()}
    s1 = [r for b in ma.make_batches(gold, pilot, 1, batch_size=7) for r in b]
    s2 = [r for b in ma.make_batches(gold, pilot, 2, batch_size=7) for r in b]
    # stage 1 = 12 core + 8 fork + 2 rejected + 4 discovered + 20 eval negatives = 46, minus 10 pilot
    assert len(s1) == 36 and len(s2) == 30
    ids1, ids2 = {r["pair_id"] for r in s1}, {r["pair_id"] for r in s2}
    assert not ids1 & ids2 and not (ids1 | ids2) & pilot
    assert ids1 | ids2 | pilot == {g["pair_id"] for g in gold}
    assert len({r["review_id"] for r in s1 + s2}) == 66
    assert all(len(b) == 7 for b in ma.make_batches(gold, pilot, 1, batch_size=7)[:-1])


def test_batches_are_deterministic_and_seed_dependent(tmp_path):
    gold, *_ = _setup(tmp_path)
    a = ma.make_batches(gold, set(), 1, seed=1)
    assert a == ma.make_batches(list(reversed(gold)), set(), 1, seed=1)
    assert a != ma.make_batches(gold, set(), 1, seed=2)


def test_batch_files_are_blind(tmp_path):
    gold, gp, kp, sp, _ = _setup(tmp_path)
    out = tmp_path / "out"
    assert ma.main(["batches", "--gold", str(gp), "--key", str(kp), "--out-dir", str(out),
                    "--stage", "all", "--batch-size", "10", "--n-sentinel", "0"]) == 0
    files = sorted((out / "batches").rglob("*.csv"))
    assert len(files) == 4 + 3                      # 36 -> 4 batches, 30 -> 3 batches
    for p in files:
        text = p.read_text(encoding="utf-8")
        assert text.splitlines()[0] == "review_id,fact_a,fact_b"
        for word in ("s:", "core", "fork", "rejected", "discovered", "negative", "judge", "sh_6k"):
            assert word not in text
    key = json.loads((out / "batch_key.json").read_text(encoding="utf-8"))
    assert sum(len(b) for b in key["stages"]["1"].values()) == 36


def test_split_apportions_heldout_by_tier_and_hides_the_heldout_labels(tmp_path):
    gold, gp, kp, sp, key = _setup(tmp_path)
    held = ma.split_pilot(key["rows"], seed=5, n_heldout=5)
    # tier sizes 2/4/1/2/1 of 10, five seats: quotas 1, 2, .5, 1, .5 -> 1, 2, 1, 1, 0 or 1, 2, 0, 1, 1
    tiers = [key["rows"][r]["tier"] for r in held]
    assert len(held) == 5 and tiers.count("core") == 1 and tiers.count("update_only_fork") == 2
    assert tiers.count("discovered_unverified") == 1
    assert held == ma.split_pilot(key["rows"], seed=5, n_heldout=5)

    out = tmp_path / "out"
    assert ma.main(["split", "--sheet", str(sp), "--key", str(kp), "--out-dir", str(out),
                    "--seed", "5", "--n-heldout", "5"]) == 0
    cal = list(csv.DictReader(open(out / "calibration_human.csv", encoding="utf-8")))
    assert {r["review_id"] for r in cal} == set(key["rows"]) - set(held)
    blind = (out / "batches" / "heldout" / "batch_001.csv").read_text(encoding="utf-8")
    assert "yes" not in blind and "P0" not in blind and blind.count("\n") == 6
    hk = json.loads((out / "heldout_key.json").read_text(encoding="utf-8"))
    assert sorted(v["pilot_id"] for v in hk["rows"].values()) == held
    ex = (out / "calibration_examples.md").read_text(encoding="utf-8")
    assert all(r not in ex for r in held) and all(r in ex for r in set(key["rows"]) - set(held))


def test_read_labels_rejects_blanks_foreign_ids_and_duplicates(tmp_path):
    p = tmp_path / "l.csv"
    _labels(p, {"a00001": YES6, "a00002": NO6})
    assert ma.read_labels(p, {"a00001", "a00002"})["a00001"]["update_conflict"] is True
    with pytest.raises(ValueError, match="review ids differ"):
        ma.read_labels(p, {"a00001", "a00003"})
    _labels(p, {"a00001": dict(YES6, strict_conflict="")})
    with pytest.raises(ValueError, match="expected yes/no"):
        ma.read_labels(p, {"a00001"})
    p.write_text("review_id," + ",".join(LABEL_COLS) + ",notes\n" + "a1,yes,yes,yes,yes,yes,yes,\n" * 2,
                 encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        ma.read_labels(p, {"a1"})


def test_rubric_violations():
    assert ma.rubric_violations({c: True for c in LABEL_COLS}) == []
    assert ma.rubric_violations({c: False for c in LABEL_COLS}) == []
    lab = {c: True for c in LABEL_COLS}
    lab["update_conflict"] = False
    assert len(ma.rubric_violations(lab)) == 2      # update != conjunction, and strict without update


def test_ingest_scores_against_hand_computed_counts(tmp_path, capsys):
    gold, gp, kp, sp, key = _setup(tmp_path)
    out = tmp_path / "out"
    common = ["--key", str(kp), "--out-dir", str(out), "--seed", "5"]
    ma.main(["split", "--sheet", str(sp), "--n-heldout", "5"] + common)
    ma.main(["batches", "--gold", str(gp), "--stage", "1", "--batch-size", "36"] + common)

    hk = json.loads((out / "heldout_key.json").read_text(encoding="utf-8"))["rows"]
    human = {h: (YES6 if key["rows"][v["pilot_id"]]["tier"] == "core" else NO6) for h, v in hk.items()}
    flipped = sorted(hk)[0]                         # the model disagrees with the human on one pair
    model_h = dict(human)
    model_h[flipped] = NO6 if human[flipped] is YES6 else YES6
    _labels(out / "labels" / "heldout" / "batch_001.csv", model_h)

    bk = json.loads((out / "batch_key.json").read_text(encoding="utf-8"))["stages"]["1"]["batch_001"]
    tier = {g["pair_id"]: g["tier"] for g in gold}
    # the model says yes on every core and every fork pair, no elsewhere
    _labels(out / "labels" / "stage1" / "batch_001.csv",
            {rid: (YES6 if tier[pid] in ("core", "update_only_fork") else NO6) for rid, pid in bk.items()})

    assert ma.main(["ingest", "--gold", str(gp), "--sheet", str(sp)] + common) == 0
    rep = json.loads((out / "MODEL_ANNOTATION_SUMMARY.json").read_text(encoding="utf-8"))
    assert rep["n_labelled"] == 41
    hv = rep["heldout_vs_human"]["update_conflict"]["agree"]
    assert (hv["k"], hv["n"]) == (4, 5)
    assert rep["heldout_vs_human"]["all_six_fields_identical"]["k"] == 4
    # 4 of 5 = 0.80: below the 0.85 bar on update_conflict, at the 0.80 bar on the other fields
    gate = rep["heldout_gate"]
    assert gate["failed_fields"] == ["update_conflict"] and gate["passed"] is False

    held_tiers = [key["rows"][v["pilot_id"]]["tier"] for v in hk.values()]
    flipped_tier = key["rows"][hk[flipped]["pilot_id"]]["tier"]
    # stage-1 fork pairs: 8 in tier, 4 in the pilot -> 4 labelled in stage 1, all "yes";
    # the judge says no on every fork pair and the parser says yes.
    fork = rep["by_tier"]["update_only_fork"]
    n_fork_held = held_tiers.count("update_only_fork")
    fork_held_yes = 1 if flipped_tier == "update_only_fork" else 0
    assert fork["n"] == 4 + n_fork_held and fork["n_in_tier"] == 8
    assert fork["model_update_yes"] == 4 + fork_held_yes
    assert fork["update_agrees_with_parser"]["k"] == 4 + fork_held_yes
    assert fork["update_agrees_with_judge"]["k"] == n_fork_held - fork_held_yes
    assert rep["rubric_departures"] == {}

    merged = list(csv.DictReader(open(out / "MODEL_LABELS.csv", encoding="utf-8")))
    assert len(merged) == 41 and {r["group"] for r in merged} == {"heldout", "stage1"}


def test_ingest_reports_an_invalid_batch_and_keeps_the_valid_ones(tmp_path, capsys):
    gold, gp, kp, sp, _ = _setup(tmp_path)
    out = tmp_path / "out"
    common = ["--key", str(kp), "--out-dir", str(out)]
    ma.main(["batches", "--gold", str(gp), "--stage", "1", "--batch-size", "18"] + common)
    bk = json.loads((out / "batch_key.json").read_text(encoding="utf-8"))["stages"]["1"]
    _labels(out / "labels" / "stage1" / "batch_001.csv", {rid: NO6 for rid in bk["batch_001"]})
    _labels(out / "labels" / "stage1" / "batch_002.csv", {rid: NO6 for rid in list(bk["batch_002"])[:-1]})
    assert ma.main(["ingest", "--gold", str(gp), "--sheet", str(tmp_path / "absent.csv")] + common) == 1
    rep = json.loads((out / "MODEL_ANNOTATION_SUMMARY.json").read_text(encoding="utf-8"))
    assert rep["n_labelled"] == 18 and "heldout_vs_human" not in rep
    assert [b["state"] for b in rep["batches"]] == ["done", "invalid"]
    assert ma.main(["status"] + common) == 0
    assert "1/2 batches done, 1 invalid" in capsys.readouterr().out


def _hv(k_update: int, k_other: int, n: int) -> dict:
    return {c: {"agree": {"k": k, "n": n, "rate": k / n}}
            for c in LABEL_COLS for k in [k_update if c == "update_conflict" else k_other]}


def test_heldout_gate_thresholds_and_completeness():
    assert ma.heldout_gate(_hv(17, 16, 20), 20, 20)["passed"] is True      # 0.85 and 0.80 exactly
    g = ma.heldout_gate(_hv(16, 20, 20), 20, 20)                           # 0.80 on update_conflict
    assert g["passed"] is False and g["failed_fields"] == ["update_conflict"]
    g = ma.heldout_gate(_hv(20, 15, 20), 20, 20)                           # 0.75 on the other fields
    assert g["passed"] is False and len(g["failed_fields"]) == 5
    assert ma.heldout_gate(_hv(19, 19, 19), 19, 20)["passed"] is False     # one held-out pair unlabelled


def test_assign_gives_disjoint_contiguous_lists_of_unfinished_batches():
    st = [{"group": "stage1", "batch": f"batch_{i:03d}", "state": "done" if i in (2, 5) else "missing"}
          for i in range(1, 12)]
    st.append({"group": "stage2", "batch": "batch_001", "state": "missing"})
    parts = ma.assign_batches(st, "stage1", 4)
    flat = [b for p in parts for b in p]
    assert flat == [f"batch_{i:03d}" for i in (1, 3, 4, 6, 7, 8, 9, 10, 11)]   # 9 left of 11
    assert sorted(len(p) for p in parts) == [2, 2, 2, 3]
    assert ma.assign_batches(st, "stage1", 20) == [[b] for b in flat]          # more workers than batches
    assert ma.assign_batches([], "stage1", 3) == []


def test_stage2_batches_carry_sentinels_and_ingest_checks_them(tmp_path):
    gold, gp, kp, sp, key = _setup(tmp_path)
    out = tmp_path / "out"
    common = ["--key", str(kp), "--out-dir", str(out)]
    # stage 2 refuses to build before stage 1 has labels to draw sentinels from
    ma.main(["batches", "--gold", str(gp), "--stage", "1", "--batch-size", "18"] + common)
    with pytest.raises(SystemExit, match="sentinel"):
        ma.main(["batches", "--gold", str(gp), "--stage", "2", "--batch-size", "18"] + common)

    tier = {g["pair_id"]: g["tier"] for g in gold}
    k1 = json.loads((out / "batch_key.json").read_text(encoding="utf-8"))["stages"]["1"]
    truth = {pid: (YES6 if tier[pid] in ("core", "update_only_fork") else NO6)
             for b in k1.values() for pid in b.values()}
    for name, b in k1.items():                             # 36 stage-1 pairs in two batches
        _labels(out / "labels" / "stage1" / f"{name}.csv", {rid: truth[pid] for rid, pid in b.items()})

    ma.main(["batches", "--gold", str(gp), "--stage", "2", "--batch-size", "18",
             "--n-sentinel", "3"] + common)
    k2 = json.loads((out / "batch_key.json").read_text(encoding="utf-8"))["stages"]["2"]
    assert len(k2) == 2                                    # 30 new pairs: 18 + 12, plus 3 sentinels each
    b1 = k2["batch_001"]
    assert len(b1) == 18 + 3 and len(k2["batch_002"]) == 12 + 3
    sent1 = {rid: pid for rid, pid in b1.items() if pid in truth}
    assert len(sent1) == 3 and all(tier[pid] != "negative" for pid in sent1.values())
    new = [pid for b in k2.values() for pid in b.values() if pid not in truth]
    assert len(new) == 30 == len(set(new)) and all(tier[p] == "negative" for p in new)
    blind = (out / "batches" / "stage2" / "batch_001.csv").read_text(encoding="utf-8")
    assert blind.splitlines()[0] == "review_id,fact_a,fact_b" and blind.count("\n") == 22

    # the worker answers every sentinel as in stage 1, except one in batch_001
    wrong = sorted(sent1)[0]
    lab = {rid: (truth[pid] if pid in truth else NO6) for rid, pid in b1.items()}
    lab[wrong] = NO6 if truth[b1[wrong]] is YES6 else YES6
    _labels(out / "labels" / "stage2" / "batch_001.csv", lab)
    _labels(out / "labels" / "stage2" / "batch_002.csv",
            {rid: (truth[pid] if pid in truth else NO6) for rid, pid in k2["batch_002"].items()})

    assert ma.main(["ingest", "--gold", str(gp), "--sheet", str(tmp_path / "absent.csv")] + common) == 0
    rep = json.loads((out / "MODEL_ANNOTATION_SUMMARY.json").read_text(encoding="utf-8"))
    assert rep["n_labelled"] == 36 + 30                    # sentinel rows are not labels
    sc = rep["sentinels"]
    assert sc["n"] == 6 and sc["all_six_identical"]["k"] == 5
    assert sc["batches_with_a_mismatch"] == {"stage2/batch_001": 1}
    merged = list(csv.DictReader(open(out / "MODEL_LABELS.csv", encoding="utf-8")))
    assert len(merged) == 66 and len({r["pair_id"] for r in merged}) == 66


def test_repeated_text_and_parser_slot_counts():
    gold = {"p1": {"fact_a": "A", "fact_b": "B", "parser": {"both_parse": True, "same_subject": True,
                                                           "same_relation": True, "same_object": False}},
            "p2": {"fact_a": "B", "fact_b": "A", "parser": {"both_parse": True, "same_subject": True,
                                                           "same_relation": True, "same_object": False}},
            "p3": {"fact_a": "A", "fact_b": "B", "parser": {"both_parse": False}},
            "p4": {"fact_a": "C", "fact_b": "C", "parser": {"both_parse": True, "same_subject": False,
                                                           "same_relation": True, "same_object": True}},
            "p5": {"fact_a": "C", "fact_b": "C", "parser": {"both_parse": True, "same_subject": False,
                                                           "same_relation": True, "same_object": True}}}
    yes = {c: True for c in LABEL_COLS}
    no = {c: False for c in LABEL_COLS}
    merged = {"r1": dict(yes, pair_id="p1", batch="s/1"), "r2": dict(yes, pair_id="p2", batch="s/2"),
              "r3": dict(no, pair_id="p3", batch="s/2"),          # same text as p1/p2, other labels
              "r4": dict(no, pair_id="p4", batch="s/3"), "r5": dict(no, pair_id="p5", batch="s/3")}
    rt = ma.repeated_text(merged, gold)
    assert rt["n_rows"] == 5 and rt["n_distinct_texts"] == 2
    assert (rt["repeated_texts"]["k"], rt["repeated_texts"]["n"]) == (1, 2)       # {C,C} agrees, {A,B} does not
    assert (rt["repeated_in_different_batches"]["k"], rt["repeated_in_different_batches"]["n"]) == (0, 1)
    ps = ma.parser_slots(merged, gold)
    assert ps["n_both_parse"] == 4 and ps["same_referent_equals_same_subject"] == 4
    assert ps["same_template_and_same_value"] == 2 and ps["of_which_values_incompatible"] == 0
    assert ps["same_template_different_value"] == 2 and ps["of_which_values_compatible"] == 0
