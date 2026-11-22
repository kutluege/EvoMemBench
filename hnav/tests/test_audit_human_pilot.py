"""Pilot human review — selection, blindness and scoring against hand-computed values.

The gold universe is synthetic and written into ``tmp_path``; nothing here reads
the committed dataset, torch or the network.
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from hnav.labeling import audit_human_pilot as pilot  # noqa: E402
from hnav.labeling import audit_human_review as hr  # noqa: E402
from hnav.labeling.agreement_stats import wilson  # noqa: E402

# parser tag, judge verdict and evaluation-set membership per tier, as in the gold dataset
TIER_SPEC = {
    "core":                  {"same_key": True,  "update": True,  "strict": True,  "eval": True},
    "negative":              {"same_key": False, "update": False, "strict": False, "eval": True},
    "update_only_fork":      {"same_key": True,  "update": False, "strict": False, "eval": True},
    "rejected":              {"same_key": True,  "update": False, "strict": False, "eval": False},
    "discovered_unverified": {"same_key": False, "update": True,  "strict": True,  "eval": False},
}
SIZES = {"core": 40, "negative": 60, "update_only_fork": 282, "rejected": 12,
         "discovered_unverified": 105}


def _record(tier: str, i: int) -> dict:
    s = TIER_SPEC[tier]
    n = 1000 * list(SIZES).index(tier) + i          # the fact text must not name the tier
    return {"pair_id": f"sh_6k:{tier}-{i:04d}", "subset": "sh_6k", "tier": tier,
            "in_eval_set": s["eval"],
            "fact_a": f"Entity {n} has value <alpha>.",
            "fact_b": f"Entity {n} has value \"beta\", or so.",
            "parser": {"same_key": s["same_key"]},
            "judge": {"same_referent": True, "same_relation": True, "context_overlap": True,
                      "values_incompatible": s["update"], "update_conflict": s["update"],
                      "strict_conflict": s["strict"],
                      "explanation": "SECRET-JUDGE-EXPLANATION"}}


@pytest.fixture()
def gold() -> list[dict]:
    return [_record(t, i) for t, n in SIZES.items() for i in range(n)]


def _write_gold(tmp_path: pathlib.Path, gold: list[dict]) -> pathlib.Path:
    p = tmp_path / "gold.jsonl"
    p.write_text("\n".join(json.dumps(g) for g in gold) + "\n", encoding="utf-8")
    return p


def _build(tmp_path, gold, **kw):
    out = tmp_path / "pilot"
    argv = ["build", "--gold", str(_write_gold(tmp_path, gold)), "--out-dir", str(out)]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    assert pilot.main(argv) == 0
    return out


# ── selection ────────────────────────────────────────────────────────────────

def test_disputed_seats_follow_the_largest_remainder_apportionment(gold):
    # quotas for 50 seats over 282 / 12 / 105 of 399: 35.34, 1.50, 13.16
    # floors 35 + 1 + 13 = 49; the last seat goes to the largest remainder (0.50)
    rows = pilot.select_pilot(gold)
    by_tier = {t: sum(r["tier"] == t for r in rows) for t in SIZES}
    assert by_tier == {"update_only_fork": 35, "rejected": 2, "discovered_unverified": 13,
                       "core": 5, "negative": 5}
    assert sum(r["stratum"] == "disputed" for r in rows) == 50
    assert sum(r["stratum"] == "control" for r in rows) == 10


def test_selection_is_deterministic_and_seed_dependent(gold):
    a = pilot.select_pilot(gold, seed=1)
    b = pilot.select_pilot(list(reversed(gold)), seed=1)      # input order must not matter
    c = pilot.select_pilot(gold, seed=2)
    assert [(r["review_id"], r["pair_id"]) for r in a] == [(r["review_id"], r["pair_id"]) for r in b]
    assert {r["pair_id"] for r in a} != {r["pair_id"] for r in c}
    assert len({r["pair_id"] for r in a}) == len(a) == 60
    assert [r["review_id"] for r in a] == [f"P{i:03d}" for i in range(60)]


def test_small_pools_are_taken_whole_and_controls_come_from_the_eval_set(gold):
    few = [g for g in gold if g["tier"] != "update_only_fork"]            # 12 + 105 disputed
    rows = pilot.select_pilot(few, n_disputed=500, n_control=4)
    assert sum(r["stratum"] == "disputed" for r in rows) == 117
    outside = [dict(g, in_eval_set=False) for g in gold]
    assert all(r["stratum"] == "disputed" for r in pilot.select_pilot(outside))


def test_a_pair_that_is_not_disputed_stops_the_build(gold):
    drifted = [dict(g, judge=dict(g["judge"], update_conflict=True))
               if g["tier"] == "update_only_fork" else g for g in gold]
    with pytest.raises(SystemExit, match="not disputed"):
        pilot.select_pilot(drifted)


# ── blindness ────────────────────────────────────────────────────────────────

def test_sheet_and_page_carry_nothing_but_the_blind_columns(tmp_path, gold):
    out = _build(tmp_path, gold)
    key = json.loads((out / "pilot_key.json").read_text(encoding="utf-8"))
    with open(out / "pilot_sheet.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == hr.SHEET_COLS
        assert not set(reader.fieldnames) & hr.FORBIDDEN_COLS
        sheet_rows = list(reader)
    assert {r["review_id"] for r in sheet_rows} == set(key["rows"])
    assert all(r[c] == "" for r in sheet_rows for c in hr.LABEL_COLS)

    page = (out / "pilot_label.html").read_text(encoding="utf-8")
    blob = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1)
    assert "<" not in blob                                     # facts cannot close the script tag
    data = json.loads(blob)
    assert data["build_id"] == key["build_id"]
    assert all(set(r) == {"review_id", "subset", "fact_a", "fact_b"} for r in data["rows"])
    assert [r["review_id"] for r in data["rows"]] == [r["review_id"] for r in sheet_rows]
    by_id = {r["review_id"]: r for r in data["rows"]}
    for rid, k in key["rows"].items():                         # facts survive the escaping intact
        g = next(x for x in gold if x["pair_id"] == k["pair_id"])
        assert (by_id[rid]["fact_a"], by_id[rid]["fact_b"]) == (g["fact_a"], g["fact_b"])
    for leak in ("SECRET-JUDGE-EXPLANATION", "sh_6k:", "update_only_fork", "discovered_unverified",
                 "in_eval_set", "same_key"):
        assert leak not in page
        assert leak not in (out / "pilot_sheet.csv").read_text(encoding="utf-8")
    assert data["sheet_cols"] == hr.SHEET_COLS and data["label_cols"] == hr.LABEL_COLS
    assert set(pilot.SHORT) == set(hr.LABEL_COLS)


# ── scoring ──────────────────────────────────────────────────────────────────

def _fill(out: pathlib.Path, gold: list[dict], name: str, answer) -> pathlib.Path:
    """Write a filled sheet; ``answer(tier, index_within_tier)`` gives update_conflict."""
    key = json.loads((out / "pilot_key.json").read_text(encoding="utf-8"))["rows"]
    seen: dict[str, int] = {}
    rows = []
    with open(out / "pilot_sheet.csv", newline="", encoding="utf-8") as f:
        for r in sorted(csv.DictReader(f), key=lambda r: r["review_id"]):
            tier = key[r["review_id"]]["tier"]
            i = seen.get(tier, 0)
            seen[tier] = i + 1
            upd = answer(tier, i)
            r.update({"same_referent": "yes", "same_relation": "yes", "context_overlap": "yes",
                      "values_incompatible": "yes" if upd else "no",
                      "update_conflict": "yes" if upd else "no", "strict_conflict": "no"})
            rows.append(r)
    path = out / name
    hr.write_sheet(path, rows)
    return path


def test_score_matches_hand_computed_counts(tmp_path, gold):
    out = _build(tmp_path, gold)
    gold_path = tmp_path / "gold.jsonl"

    # annotator A: sides with the parser on the first 10 of 35 forks and with the judge on the
    # other 25; with the judge on both rejected pairs; with the judge on 4 of 13 discovered;
    # reads every control as the judge does.
    def a(tier, i):
        if tier == "update_only_fork":
            return i < 10                    # parser says update, judge says no
        if tier == "rejected":
            return False
        if tier == "discovered_unverified":
            return i < 4                     # judge says update, parser says no
        return tier == "core"

    sheet_a = _fill(out, gold, "a.csv", a)
    argv = ["score", "--gold", str(gold_path), "--key", str(out / "pilot_key.json"),
            "--sheet", str(sheet_a), "--out-json", str(out / "s.json"), "--out-md", str(out / "s.md")]
    assert pilot.main(argv) == 0
    rep = json.loads((out / "s.json").read_text(encoding="utf-8"))
    g = rep["update_conflict_by_group"]

    assert rep["n_reviewed"] == 60 and rep["annotators"] == 1
    assert g["update_only_fork"]["human_update_yes"] == 10
    assert g["update_only_fork"]["agrees_with_judge"]["k"] == 25
    assert g["update_only_fork"]["agrees_with_parser"]["k"] == 10
    assert g["rejected"]["agrees_with_judge"]["k"] == 2
    assert g["discovered_unverified"]["agrees_with_judge"]["k"] == 4
    assert g["discovered_unverified"]["agrees_with_parser"]["k"] == 9
    assert g["disputed"]["n"] == 50
    assert g["disputed"]["agrees_with_judge"]["k"] == 25 + 2 + 4
    assert g["disputed"]["agrees_with_parser"]["k"] == 10 + 0 + 9
    for tier in pilot.DISPUTED_TIERS + ["disputed"]:           # parser and judge always differ
        assert g[tier]["agrees_with_judge"]["k"] + g[tier]["agrees_with_parser"]["k"] == g[tier]["n"]
    assert g["control"]["agrees_with_judge"]["k"] == g["control"]["agrees_with_parser"]["k"] == 10
    lo, hi = wilson(31, 50)
    assert math.isclose(g["disputed"]["agrees_with_judge"]["wilson95"][0], lo, abs_tol=1e-12)
    assert math.isclose(g["disputed"]["agrees_with_judge"]["wilson95"][1], hi, abs_tol=1e-12)

    # field level: update_conflict agrees on 31 disputed + 10 controls; strict_conflict is "no"
    # everywhere, so it agrees wherever the judge's strict flag is false: 35 + 2 forks and
    # rejected, 5 negatives = 42
    f = rep["field_agreement_with_judge"]
    assert f["update_conflict"]["k"] == 41 and f["same_referent"]["k"] == 60
    assert f["strict_conflict"]["k"] == 42
    assert "human_human" not in rep
    assert "sum to n" in (out / "s.md").read_text(encoding="utf-8")


def test_two_annotators_give_a_hand_computed_kappa(tmp_path, gold):
    out = _build(tmp_path, gold)

    def a(tier, i):
        return tier in ("core", "update_only_fork") and (tier == "core" or i < 10)

    def b(tier, i):
        return tier in ("core", "update_only_fork") and (tier == "core" or 5 <= i < 20)

    sheet_a, sheet_b = _fill(out, gold, "a.csv", a), _fill(out, gold, "b.csv", b)
    argv = ["score", "--gold", str(tmp_path / "gold.jsonl"), "--key", str(out / "pilot_key.json"),
            "--sheet", str(sheet_a), "--sheet-b", str(sheet_b),
            "--out-json", str(out / "s.json"), "--out-md", str(out / "s.md")]
    assert pilot.main(argv) == 0
    hh = json.loads((out / "s.json").read_text(encoding="utf-8"))["human_human"]["update_conflict"]
    # A yes: 5 core + forks 0-9 = 15; B yes: 5 core + forks 5-19 = 20; both yes: 5 + 5 = 10
    # TT=10, TF=5, FT=10, FF=35 over 60: po = 45/60 = 0.75
    # pe = (15/60)(20/60) + (45/60)(40/60) = 1/12 + 1/2 = 7/12; kappa = (3/4 - 7/12)/(5/12) = 0.4
    assert hh["table_A_B"] == {"TT": 10, "TF": 5, "FT": 10, "FF": 35}
    assert math.isclose(hh["agreement"], 0.75, abs_tol=1e-12)
    assert math.isclose(hh["kappa"], 0.4, abs_tol=1e-12)


def test_score_rejects_blank_cells_and_foreign_sheets(tmp_path, gold):
    out = _build(tmp_path, gold)
    base = ["score", "--gold", str(tmp_path / "gold.jsonl"), "--key", str(out / "pilot_key.json"),
            "--out-json", str(out / "s.json"), "--out-md", str(out / "s.md")]
    with pytest.raises(SystemExit, match="expected yes/no"):
        pilot.main(base + ["--sheet", str(out / "pilot_sheet.csv")])       # the unfilled sheet

    filled = _fill(out, gold, "a.csv", lambda tier, i: False)
    with open(filled, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    hr.write_sheet(out / "short.csv", rows[:-1])
    with pytest.raises(SystemExit, match="review_ids differ"):
        pilot.main(base + ["--sheet", str(out / "short.csv")])
    assert not (out / "s.json").exists()                                   # nothing was written
