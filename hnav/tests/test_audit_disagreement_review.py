"""Review of gold-model disagreements — selection, blindness and scoring against hand-computed values.

The gold universe, the model labels and the pilot key are synthetic and written
into ``tmp_path``; nothing here reads the committed dataset, torch or the network.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from hnav.labeling import audit_disagreement_review as dr  # noqa: E402
from hnav.labeling import audit_human_pilot as pilot  # noqa: E402
from hnav.labeling import audit_human_review as hr  # noqa: E402
from hnav.labeling.agreement_stats import wilson  # noqa: E402

EVAL_TIERS = {"core", "update_only_fork", "negative"}
GOLD_YES = {"core", "update_only_fork"}

# (pair_id, tier, text number, model update_conflict or None, swap A/B)
#   text 1: two disputed copies, gold yes / model no
#   text 2: one disputed copy (rejected) and one agreeing copy with the opposite gold label (core)
#   text 3: one disputed copy and one pilot pair that has no model label
#   text 4: two disputed copies, the second with A and B swapped
#   texts 5-7: gold and model agree, or no model label - never in the sheet
SPEC = [
    ("sh_6k:0001", "update_only_fork", 1, False, False),
    ("sh_32k:0001", "core", 1, False, False),
    ("sh_32k:0002", "rejected", 2, True, False),
    ("sh_64k:0002", "core", 2, True, False),
    ("sh_64k:0003", "discovered_unverified", 3, True, False),
    ("sh_6k:0003", "discovered_unverified", 3, None, False),
    ("sh_64k:0004", "update_only_fork", 4, False, False),
    ("sh_32k:0004", "update_only_fork", 4, False, True),
    ("sh_6k:0005", "core", 5, True, False),
    ("sh_6k:0006", "negative", 6, False, False),
    ("sh_6k:0007", "negative", 7, None, False),
]
PILOT = {"sh_6k:0003": "P007"}
# the disputed pair id that sorts first under each text, and annotator A's / B's update_conflict
SHOWN = {1: "sh_32k:0001", 2: "sh_32k:0002", 3: "sh_64k:0003", 4: "sh_32k:0004"}
ANSWER_A = {1: True, 2: True, 3: False, 4: False}
ANSWER_B = {1: True, 2: False, 3: False, 4: True}


def _facts(n: int, swap: bool) -> tuple[str, str]:
    a, b = f"Entity {n} has value <alpha>.", f"Entity {n} has value \"beta\", or so."
    return (b, a) if swap else (a, b)


@pytest.fixture()
def gold() -> list[dict]:
    out = []
    for pid, tier, n, _, swap in SPEC:
        a, b = _facts(n, swap)
        out.append({"pair_id": pid, "subset": pid.split(":")[0], "tier": tier,
                    "in_eval_set": tier in EVAL_TIERS, "gold_update": tier in GOLD_YES,
                    "fact_a": a, "fact_b": b, "judge": {"explanation": "SECRET-JUDGE-EXPLANATION"}})
    return out


def _build(tmp_path: pathlib.Path, gold: list[dict], **kw) -> pathlib.Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    g = tmp_path / "gold.jsonl"
    g.write_text("\n".join(json.dumps(x) for x in gold) + "\n", encoding="utf-8")
    m = tmp_path / "MODEL_LABELS.csv"
    with open(m, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "pair_id", "group", "update_conflict", "notes"])
        for i, (pid, _, _, model, _) in enumerate(SPEC):
            if model is not None:
                w.writerow([f"a{i:05d}", pid, "stage1", "yes" if model else "no", "SECRET-NOTE"])
    k = tmp_path / "pilot_key.json"
    k.write_text(json.dumps({"rows": {rid: {"pair_id": pid} for pid, rid in PILOT.items()}}),
                 encoding="utf-8")
    out = tmp_path / "review"
    argv = ["build", "--gold", str(g), "--model-labels", str(m), "--pilot-key", str(k),
            "--out-dir", str(out)]
    for name, v in kw.items():
        argv += [f"--{name.replace('_', '-')}", str(v)]
    assert dr.main(argv) == 0
    return out


def _key(out: pathlib.Path) -> dict:
    return json.loads((out / "disagreement_key.json").read_text(encoding="utf-8"))


def _rid_of_text(key: dict) -> dict[int, str]:
    by_shown = {v["shown_pair_id"]: rid for rid, v in key["rows"].items()}
    return {n: by_shown[pid] for n, pid in SHOWN.items()}


def _fill(out: pathlib.Path, answers: dict[int, bool], name: str, **override) -> pathlib.Path:
    """Fill the blind sheet: update_conflict as given, the four checks consistent with it."""
    rid = _rid_of_text(_key(out))
    want = {rid[n]: v for n, v in answers.items()}
    with open(out / "disagreement_sheet.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        yes = want[r["review_id"]]
        for c in hr.LABEL_COLS[:3]:
            r[c] = "yes"
        r["values_incompatible"] = r["update_conflict"] = "yes" if yes else "no"
        r["strict_conflict"] = "no"
        r.update(override.get(r["review_id"], {}))
    p = out / name
    hr.write_sheet(p, rows)
    return p


# ── selection ────────────────────────────────────────────────────────────────

def test_one_row_per_sentence_pair_and_the_key_lists_every_copy(tmp_path, gold):
    key = _key(_build(tmp_path, gold))
    assert key["n_rows"] == 4 and key["n_disputed_pairs"] == 6
    assert key["disputed_by_tier"] == {"update_only_fork": 3, "core": 1, "rejected": 1,
                                       "discovered_unverified": 1}
    assert key["disputed_in_eval_set"] == 4
    assert (key["disputed_gold_yes_model_no"], key["disputed_gold_no_model_yes"]) == (4, 2)
    assert key["rows_seen_in_pilot"] == 1
    rid = _rid_of_text(key)
    assert sorted(key["rows"]) == ["D000", "D001", "D002", "D003"]

    two = {p["pair_id"]: p for p in key["rows"][rid[2]]["pairs"]}
    assert set(two) == {"sh_32k:0002", "sh_64k:0002"}        # the agreeing copy is recorded too
    assert two["sh_32k:0002"]["disputed"] and not two["sh_64k:0002"]["disputed"]
    assert (two["sh_32k:0002"]["gold_update"], two["sh_64k:0002"]["gold_update"]) == (False, True)

    three = {p["pair_id"]: p for p in key["rows"][rid[3]]["pairs"]}
    assert three["sh_6k:0003"]["model_update"] is None and not three["sh_6k:0003"]["disputed"]
    assert key["rows"][rid[3]]["seen_in_pilot"] == ["P007"]
    assert all(key["rows"][rid[n]]["seen_in_pilot"] == [] for n in (1, 2, 4))

    four = key["rows"][rid[4]]["pairs"]                       # A/B order does not split a text
    assert [p["pair_id"] for p in four] == ["sh_32k:0004", "sh_64k:0004"]
    assert all(p["disputed"] for p in four)


def test_selection_is_deterministic_and_seed_dependent(tmp_path, gold):
    a = _key(_build(tmp_path / "a", gold))
    b = _key(_build(tmp_path / "b", gold))
    assert a == b
    orders = {tuple(_key(_build(tmp_path / f"s{s}", gold, seed=s))["rows"][f"D{i:03d}"]["shown_pair_id"]
                    for i in range(4)) for s in range(8)}
    assert len(orders) > 1
    assert all(sorted(o) == sorted(SHOWN.values()) for o in orders)


def test_nothing_to_review_stops_the_build(tmp_path, gold):
    model = {pid: m for pid, _, _, m, _ in SPEC}
    agreeing = [dict(g, gold_update=g["gold_update"] if model[g["pair_id"]] is None
                     else model[g["pair_id"]]) for g in gold]
    with pytest.raises(SystemExit, match="nothing to review"):
        _build(tmp_path, agreeing)


def test_model_labels_must_be_yes_or_no(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("review_id,pair_id,group,update_conflict\na1,sh_6k:1,stage1,maybe\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="expected yes/no"):
        dr.read_model_update(p)
    p.write_text("review_id,pair_id,group,update_conflict\na1,sh_6k:1,stage1,yes\n"
                 "a2,sh_6k:1,stage1,no\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="duplicate pair_id"):
        dr.read_model_update(p)


# ── blindness ────────────────────────────────────────────────────────────────

def test_sheet_and_page_carry_nothing_but_the_blind_columns(tmp_path, gold):
    out = _build(tmp_path, gold)
    key = _key(out)
    sheet_text = (out / "disagreement_sheet.csv").read_text(encoding="utf-8")
    with open(out / "disagreement_sheet.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == hr.SHEET_COLS
        sheet_rows = list(reader)
    assert {r["review_id"] for r in sheet_rows} == set(key["rows"])
    assert all(r[c] == "" for r in sheet_rows for c in hr.LABEL_COLS)

    page = (out / "disagreement_label.html").read_text(encoding="utf-8")
    blob = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1)
    assert "<" not in blob
    data = json.loads(blob)
    assert data["build_id"] == key["build_id"]
    assert all(set(r) == {"review_id", "subset", "fact_a", "fact_b"} for r in data["rows"])
    by_id = {r["review_id"]: r for r in data["rows"]}
    for rid, k in key["rows"].items():                        # the shown pair's own text and order
        g = next(x for x in gold if x["pair_id"] == k["shown_pair_id"])
        assert (by_id[rid]["fact_a"], by_id[rid]["fact_b"]) == (g["fact_a"], g["fact_b"])
    for leak in ("SECRET-JUDGE-EXPLANATION", "SECRET-NOTE", "sh_6k:", "sh_32k:", "sh_64k:",
                 "update_only_fork", "discovered_unverified", "rejected", "gold_update",
                 "model_update", "disputed", "in_eval_set", "P007"):
        assert leak not in page
        assert leak not in sheet_text


def test_the_page_saves_under_its_own_name_and_the_pilot_page_is_unchanged(tmp_path, gold):
    out = _build(tmp_path, gold, lang="tr")
    page = (out / "disagreement_label.html").read_text(encoding="utf-8")
    assert '"disagreement_sheet.partial.csv" : "disagreement_sheet.filled.csv"' in page
    assert "pilot_sheet" not in page and "pilot_key.json" not in page
    assert "human_review_key.json" not in page and "__STEM__" not in page
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                page, re.S).group(1))
    assert data["lang"] == "tr" and data["langs"] == ["en", "tr"]
    assert data["i18n"]["tr"]["title"] == "Ayrışma incelemesi: kör etiketleme"
    assert "disagreement_key.json" in data["i18n"]["en"]["rubric"]
    assert "disagreement_key.json" in data["i18n"]["tr"]["rubric"]

    blind = [{"review_id": "P000", "subset": "sh_6k", "fact_a": "a", "fact_b": "b"}]
    default = pilot.render_page(blind)
    assert '"pilot_sheet.partial.csv" : "pilot_sheet.filled.csv"' in default
    assert "__STEM__" not in default
    assert pilot.I18N["en"]["title"] == "Pilot review: blind labelling"   # the copy was a deep one
    assert "human_review_key.json" in pilot.I18N["en"]["rubric"]


# ── scoring ──────────────────────────────────────────────────────────────────

def test_score_matches_hand_computed_counts(tmp_path, gold):
    out = _build(tmp_path, gold)
    sheet = _fill(out, ANSWER_A, "a.csv")
    assert dr.main(["score", "--key", str(out / "disagreement_key.json"), "--sheet", str(sheet),
                    "--out-json", str(out / "S.json"), "--out-md", str(out / "S.md")]) == 0
    rep = json.loads((out / "S.json").read_text(encoding="utf-8"))
    assert (rep["n_rows"], rep["n_disputed_pairs"], rep["annotators"]) == (4, 6, 1)
    assert (rep["human_update_yes_rows"], rep["human_strict_yes_rows"]) == (2, 0)
    assert rep["rows_departing_from_rubric"] == [] and rep["rows_seen_in_pilot"] == 1

    # text 1 (yes): 2 pairs with gold; text 2 (yes): 1 with model; text 3 (no): 1 with gold;
    # text 4 (no): 2 with model
    want = {"all disputed pairs": (6, 3), "in evaluation set": (4, 2),
            "outside evaluation set": (2, 1), "gold yes, model no": (4, 2),
            "gold no, model yes": (2, 1), "text new to the pilot": (5, 2),
            "text labelled in the pilot": (1, 1), "core": (1, 1), "update_only_fork": (3, 1),
            "rejected": (1, 0), "discovered_unverified": (1, 1)}
    got = rep["update_conflict_by_group"]
    assert set(got) == set(want)
    for name, (n, k_gold) in want.items():
        b = got[name]
        assert (b["n"], b["sides_with_gold"]["k"], b["sides_with_model"]["k"]) == (n, k_gold, n - k_gold)
        assert b["sides_with_gold"]["wilson95"] == pytest.approx(list(wilson(k_gold, n)))
        assert b["sides_with_model"]["wilson95"] == pytest.approx(list(wilson(n - k_gold, n)))

    rid = _rid_of_text(_key(out))
    assert rep["rows_with_opposite_gold_labels"] == {"n": 1, "human_update_yes": 1,
                                                     "review_ids": [rid[2]]}
    md = (out / "S.md").read_text(encoding="utf-8")
    assert "| all disputed pairs | 6 | 3 |" in md and "Human–human" not in md


def test_two_annotators_give_a_hand_computed_kappa(tmp_path, gold):
    out = _build(tmp_path, gold)
    a, b = _fill(out, ANSWER_A, "a.csv"), _fill(out, ANSWER_B, "b.csv")
    key = _key(out)["rows"]
    rep = dr.score_sheet(hr.read_sheet(a), key, hr.read_sheet(b))
    # A = yes, yes, no, no and B = yes, no, no, yes: agreement 2/4, chance 0.5, kappa 0
    hh = rep["human_human"]["update_conflict"]
    assert hh["n"] == 4 and hh["agreement"] == pytest.approx(0.5)
    assert hh["kappa"] == pytest.approx(0.0)
    assert rep["human_human"]["same_referent"]["agreement"] == pytest.approx(1.0)
    # they agree on text 1 (2 pairs, with gold) and text 3 (1 pair, with gold)
    both = rep["both_annotators"]
    assert (both["n_disputed_pairs"], both["annotators_agree"], both["annotators_split"]) == (6, 3, 3)
    assert both["where_they_agree"]["sides_with_gold"]["k"] == 3
    assert both["where_they_agree"]["sides_with_model"]["k"] == 0
    assert "Human–human" in dr.render_md(rep)


def test_rubric_departures_are_listed_and_bad_sheets_are_rejected(tmp_path, gold):
    out = _build(tmp_path, gold)
    key = _key(out)["rows"]
    rid = _rid_of_text(_key(out))
    odd = _fill(out, ANSWER_A, "odd.csv", **{rid[3]: {"strict_conflict": "yes"}})
    assert dr.score_sheet(hr.read_sheet(odd), key)["rows_departing_from_rubric"] == [rid[3]]

    blank = _fill(out, ANSWER_A, "blank.csv", **{rid[1]: {"update_conflict": ""}})
    with pytest.raises(SystemExit, match="expected yes/no"):
        hr.read_sheet(blank)

    foreign = hr.read_sheet(_fill(out, ANSWER_A, "ok.csv"))
    foreign["P000"] = foreign.pop(rid[1])
    with pytest.raises(SystemExit, match="review_ids differ"):
        dr.score_sheet(foreign, key)

    broken = json.loads(json.dumps(key))
    broken[rid[1]]["pairs"][0]["model_update"] = broken[rid[1]]["pairs"][0]["gold_update"]
    with pytest.raises(SystemExit, match="gold and model agree"):
        dr.score_sheet(hr.read_sheet(out / "ok.csv"), broken)
