"""Decision table for strict_conflict — rows, evidence and grouping against hand-computed values."""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from hnav.labeling import audit_human_review as hr  # noqa: E402
from hnav.labeling import audit_strict_review as sr  # noqa: E402
from hnav.labeling import strict_decision_table as dt  # noqa: E402

BORN, CAPITAL, CITIZEN = "| was born in the city of ", "The capital of | is ", "| is a citizen of "
HEAD, PM = "The name of the current head of the | government is ", None   # None: unparsed sentence


def _pair(pid, text, rel_a, rel_b=None):
    rel_b = rel_a if rel_b is None else rel_b
    return {"pair_id": pid, "subset": pid.split(":")[0], "fact_a": f"{text} is alpha.",
            "fact_b": f"{text} is beta.",
            "parser": {"fact_a_parsed": {"relation": rel_a} if rel_a else None,
                       "fact_b_parsed": {"relation": rel_b} if rel_b else None}}


@pytest.fixture()
def world(tmp_path):
    gold = [
        _pair("sh_6k:b1", "Born one", BORN), _pair("sh_32k:b1", "Born one", BORN),   # one text, two ids
        _pair("sh_6k:b2", "Born two", BORN),
        _pair("sh_6k:c1", "Capital one", CAPITAL),
        _pair("sh_6k:z1", "Citizen one", CITIZEN), _pair("sh_6k:z2", "Citizen two", CITIZEN),
        _pair("sh_6k:z3", "Citizen three", CITIZEN),      # model: no update conflict, never counted
        {**_pair("sh_6k:p1", "Office one", HEAD),          # second sentence does not parse
         "parser": {"fact_a_parsed": {"relation": HEAD}, "fact_b_parsed": PM}},
        _pair("sh_6k:h1", "Human only", CAPITAL),         # no model label; the annotator's row only
    ]
    # pair_id -> (update, strict) under the first guideline
    model = {"sh_6k:b1": ("yes", "yes"), "sh_32k:b1": ("yes", "yes"), "sh_6k:b2": ("yes", "yes"),
             "sh_6k:c1": ("yes", "yes"), "sh_6k:z1": ("yes", "no"), "sh_6k:z2": ("yes", "no"),
             "sh_6k:z3": ("no", "no"), "sh_6k:p1": ("yes", "yes")}
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "gold.jsonl").write_text("\n".join(json.dumps(g) for g in gold) + "\n", encoding="utf-8")
    with open(tmp_path / "model.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "pair_id", "update_conflict", "strict_conflict"])
        for i, (pid, (u, s)) in enumerate(model.items()):
            w.writerow([f"a{i}", pid, u, s])
    by_id = {g["pair_id"]: g for g in gold}

    def six(name, rows):                                   # (review_id, pair_id, update, strict)
        out = []
        for rid, pid, upd, strict in rows:
            r = {"review_id": rid, "subset": "x", "fact_a": by_id[pid]["fact_a"],
                 "fact_b": by_id[pid]["fact_b"], "notes": ""}
            r.update({c: "yes" for c in hr.LABEL_COLS[:3]})
            r["values_incompatible"] = r["update_conflict"] = "yes" if upd else "no"
            r["strict_conflict"] = "yes" if strict else "no"
            out.append(r)
        hr.write_sheet(tmp_path / name, out)

    # seed: capital text (no model label) yes; citizen one no; citizen two: not an update conflict
    six("pilot.csv", [("P000", "sh_6k:h1", True, True), ("P001", "sh_6k:z1", True, False),
                      ("P002", "sh_6k:z2", False, False)])
    (tmp_path / "pilot_key.json").write_text(json.dumps({"rows": {
        "P000": {"pair_id": "sh_6k:h1"}, "P001": {"pair_id": "sh_6k:z1"},
        "P002": {"pair_id": "sh_6k:z2"}}}), encoding="utf-8")
    # review: citizen one again, yes this time
    six("review.csv", [("D000", "sh_6k:z1", True, True)])
    (tmp_path / "review_key.json").write_text(json.dumps({"rows": {
        "D000": {"shown_pair_id": "sh_6k:z1"}}}), encoding="utf-8")
    # strict sheet: S000 is the annotator's own (born: yes); S012 is not and must be ignored
    sr.write_sheet(tmp_path / "strict.csv", [
        {"review_id": "S000", "subset": "x", "fact_a": "a", "fact_b": "b", "strict_conflict": "yes"},
        {"review_id": "S012", "subset": "x", "fact_a": "a", "fact_b": "b", "strict_conflict": "yes"}])
    (tmp_path / "strict_key.json").write_text(json.dumps({"rows": {
        "S000": {"shown_pair_id": "sh_6k:b2"}, "S012": {"shown_pair_id": "sh_6k:c1"}}}),
        encoding="utf-8")

    def build(sub="out"):
        out = tmp_path / sub
        assert dt.main(["build", "--gold", str(tmp_path / "gold.jsonl"),
                        "--model-labels", str(tmp_path / "model.csv"),
                        "--pilot-key", str(tmp_path / "pilot_key.json"),
                        "--pilot-sheet", str(tmp_path / "pilot.csv"),
                        "--review-key", str(tmp_path / "review_key.json"),
                        "--review-sheet", str(tmp_path / "review.csv"),
                        "--strict-key", str(tmp_path / "strict_key.json"),
                        "--strict-sheet", str(tmp_path / "strict.csv"),
                        "--out-dir", str(out)]) == 0
        with open(out / "decision_table.csv", newline="", encoding="utf-8") as f:
            return out, {r["relation"]: r for r in csv.DictReader(f)}
    return build


def test_rows_counts_and_evidence(world):
    out, rows = world()
    decisions = [k for k, r in rows.items() if r["group"] == "D"]
    assert [k[:2] for k in decisions] == ["D1", "D2", "D3", "D4", "D5", "D6"]   # they head the file
    assert all(rows[k]["pair_ids"] == "" for k in decisions)
    assert {k for k, r in rows.items() if r["group"] != "D"} == {
        "was born in the city of", "The capital of | is", "is a citizen of",
        "The name of the current head of the | government is / unparsed"}
    born = rows["was born in the city of"]
    assert (born["group"], born["pair_ids"], born["sentence_pairs"]) == ("A", "3", "2")
    assert born["model_first_guideline"] == "yes"
    assert (born["own_answers_yes"], born["own_answers_no"], born["own_answer_ids"]) == ("1", "0", "S000+")

    cap = rows["The capital of | is"]                  # S012 ignored; the seed row has no model label
    assert (cap["group"], cap["pair_ids"], cap["sentence_pairs"]) == ("B", "1", "1")
    assert (cap["own_answers_yes"], cap["own_answers_no"], cap["own_answer_ids"]) == ("1", "0", "P000+")

    cit = rows["is a citizen of"]                      # z3 is not an update conflict; P002 said no update
    assert (cit["group"], cit["pair_ids"], cit["sentence_pairs"]) == ("C", "2", "2")
    assert cit["model_first_guideline"] == "no"
    assert (cit["own_answers_yes"], cit["own_answers_no"]) == ("1", "1")
    assert cit["own_answer_ids"] == "D000+ P001-"

    para = rows["The name of the current head of the | government is / unparsed"]
    assert (para["group"], para["pair_ids"]) == ("P", "1")
    assert all(r["decision"] == "" and r["reason"] == "" for r in rows.values())


def test_view_groups_rows_and_lists_the_decisions(world):
    out, rows = world()
    md = (out / "DECISION_TABLE.md").read_text(encoding="utf-8")
    assert md.index("## Group A") < md.index("## Group B") < md.index("## Group C") < md.index("## Group P")
    for d in ("| D1 |", "| D2 |", "| D3 |", "| D4 |", "| D5 |", "| D6 |"):
        assert d in md
    assert "| was born in the city of | 3 | 2 | yes | 1 yes, 0 no: S000+ | |" in md
    assert "| **total** | 3 | 2 |" in md
    assert "S012" not in md


def test_every_real_relation_has_a_group_and_an_unknown_one_stops_the_build(world, tmp_path):
    assert set(dt.RELATION_GROUP.values()) == {"A", "B", "C"}
    assert len(dt.RELATION_GROUP) == 38                 # the 37 templates and "unparsed"
    assert dt.group_of("x / y") == "P" and dt.group_of("never seen") == "?"
    gold = [_pair("sh_6k:n1", "New rel", "| is something new ")]
    (tmp_path / "g.jsonl").write_text(json.dumps(gold[0]) + "\n", encoding="utf-8")
    (tmp_path / "m.csv").write_text("review_id,pair_id,update_conflict,strict_conflict\n"
                                    "a0,sh_6k:n1,yes,no\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="without a group"):
        dt.main(["build", "--gold", str(tmp_path / "g.jsonl"), "--model-labels", str(tmp_path / "m.csv"),
                 "--pilot-key", "none", "--pilot-sheet", "none", "--review-key", "none",
                 "--review-sheet", "none", "--strict-key", "none", "--strict-sheet", "none",
                 "--out-dir", str(tmp_path / "o")])
