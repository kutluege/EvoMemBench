"""Strict-conflict reference sheet — selection, blindness and scoring against hand-computed values.

Everything is synthetic and written into ``tmp_path``.
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

from hnav.labeling import audit_human_review as hr  # noqa: E402
from hnav.labeling import audit_strict_review as sr  # noqa: E402

REL = {1: "| rel one ", 2: "| rel two ", 3: "The rel three of | is "}
NAME = {1: "rel one", 2: "rel two", 3: "The rel three of | is"}
# new texts per relation the model calls an update conflict, and the model's strict label there
N_UPDATE = {1: 10, 2: 3, 3: 1}
MODEL_STRICT = {1: False, 2: False, 3: True}


def _pair(pid: str, text: str, rel: int) -> dict:
    return {"pair_id": pid, "subset": pid.split(":")[0], "fact_a": f"{text} has value <alpha>.",
            "fact_b": f"{text} has value beta.",
            "parser": {"fact_a_parsed": {"relation": REL[rel]}, "fact_b_parsed": {"relation": REL[rel]}}}


@pytest.fixture()
def world(tmp_path):
    """Gold, model labels, a pilot sheet and a review sheet; returns the build's out dir factory."""
    gold, model = [], []
    for rel, n in N_UPDATE.items():
        for i in range(n):
            gold.append(_pair(f"sh_6k:{rel}{i:03d}", f"New {rel}-{i}", rel))
            model.append((gold[-1]["pair_id"], "yes", "yes" if MODEL_STRICT[rel] else "no"))
    for i in range(5):                                       # no update conflict: never shown
        gold.append(_pair(f"sh_6k:9{i:03d}", f"Other {i}", 1))
        model.append((gold[-1]["pair_id"], "no", "no"))
    # pilot: P000 update yes / strict no (rel one), P001 update no, P002 update yes / strict no
    # (rel two). None of the three has a model label.
    gold += [_pair("sh_32k:h1", "Human one", 1), _pair("sh_32k:h2", "Human two", 1),
             _pair("sh_32k:h4", "Human four", 2)]
    # the review labelled the text of P002 again under another pair id, strict yes this time
    gold.append(_pair("sh_64k:h4", "Human four", 2))
    model.append(("sh_64k:h4", "yes", "no"))

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "gold.jsonl").write_text("\n".join(json.dumps(g) for g in gold) + "\n", encoding="utf-8")
    with open(tmp_path / "model.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "pair_id", "group", "update_conflict", "strict_conflict"])
        for i, (pid, u, s) in enumerate(model):
            w.writerow([f"a{i:05d}", pid, "stage1", u, s])

    def filled(name, rows):                                   # rows: (review_id, pair_id, update, strict)
        by_id = {g["pair_id"]: g for g in gold}
        out = []
        for rid, pid, upd, strict in rows:
            r = {"review_id": rid, "subset": "x", "fact_a": by_id[pid]["fact_a"],
                 "fact_b": by_id[pid]["fact_b"], "notes": "SECRET-NOTE"}
            r.update({c: "yes" for c in hr.LABEL_COLS[:3]})
            r["values_incompatible"] = r["update_conflict"] = "yes" if upd else "no"
            r["strict_conflict"] = "yes" if strict else "no"
            out.append(r)
        hr.write_sheet(tmp_path / name, out)

    filled("pilot.csv", [("P000", "sh_32k:h1", True, False), ("P001", "sh_32k:h2", False, False),
                         ("P002", "sh_32k:h4", True, False)])
    (tmp_path / "pilot_key.json").write_text(json.dumps({"rows": {
        "P000": {"pair_id": "sh_32k:h1"}, "P001": {"pair_id": "sh_32k:h2"},
        "P002": {"pair_id": "sh_32k:h4"}}}), encoding="utf-8")
    filled("review.csv", [("D000", "sh_64k:h4", True, True)])
    (tmp_path / "review_key.json").write_text(json.dumps({"rows": {
        "D000": {"shown_pair_id": "sh_64k:h4"}}}), encoding="utf-8")

    def build(sub="out", **kw):
        out = tmp_path / sub
        argv = ["build", "--gold", str(tmp_path / "gold.jsonl"),
                "--model-labels", str(tmp_path / "model.csv"),
                "--pilot-key", str(tmp_path / "pilot_key.json"),
                "--pilot-sheet", str(tmp_path / "pilot.csv"),
                "--review-key", str(tmp_path / "review_key.json"),
                "--review-sheet", str(tmp_path / "review.csv"), "--out-dir", str(out),
                "--n-new", "6"]
        for k, v in kw.items():
            argv += [f"--{k.replace('_', '-')}", str(v)]
        assert sr.main(argv) == 0
        return out
    return build


def _key(out) -> dict:
    return json.loads((out / "strict_key.json").read_text(encoding="utf-8"))


# ── selection ────────────────────────────────────────────────────────────────

def test_every_earlier_update_conflict_and_a_sample_with_each_relation(world):
    key = _key(world())
    rows = key["rows"]
    assert key["n_rows"] == 8 and key["by_stratum"] == {"labelled_before": 2, "new": 6}
    assert sorted(rows) == [f"S{i:03d}" for i in range(8)]
    # one seat per relation, the other three by size: 10, 3, 1 of 14 -> 2.14, 0.64, 0.21 -> 2, 1, 0
    new = [v for v in rows.values() if v["stratum"] == "new"]
    assert {n: sum(v["relation"] == NAME[n] for v in new) for n in NAME} == {1: 3, 2: 2, 3: 1}
    assert all(v["prior"] == [] and v["model_strict"] == MODEL_STRICT[
        {v: k for k, v in NAME.items()}[v["relation"]]] for v in new)

    before = {v["shown_pair_id"]: v for v in rows.values() if v["stratum"] == "labelled_before"}
    assert set(before) == {"sh_32k:h1", "sh_64k:h4"}          # P001 said no update conflict
    assert before["sh_32k:h1"]["prior"] == [{"review_id": "P000", "strict": False}]
    assert before["sh_32k:h1"]["model_strict"] is None
    four = before["sh_64k:h4"]                                # the copy with a model label is shown
    assert four["prior"] == [{"review_id": "P002", "strict": False},
                             {"review_id": "D000", "strict": True}]
    assert four["pair_ids"] == ["sh_32k:h4", "sh_64k:h4"] and four["model_strict"] is False
    assert not any(v["shown_pair_id"].startswith("sh_6k:9") for v in rows.values())


def test_selection_is_deterministic_and_seed_dependent(world):
    assert _key(world("a")) == _key(world("b"))
    picks = {tuple(sorted(v["shown_pair_id"] for v in _key(world(f"s{s}", seed=s))["rows"].values()))
             for s in range(6)}
    assert len(picks) > 1


# ── blindness ────────────────────────────────────────────────────────────────

def test_page_asks_one_question_and_shows_no_earlier_answer(world):
    out = world(lang="tr")
    key = _key(out)
    with open(out / "strict_sheet.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["review_id", "subset", "fact_a", "fact_b", "strict_conflict", "notes"]
        sheet_rows = list(reader)
    assert {r["review_id"] for r in sheet_rows} == set(key["rows"])
    assert all(r["strict_conflict"] == "" for r in sheet_rows)

    page = (out / "strict_label.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                page, re.S).group(1))
    assert data["label_cols"] == ["strict_conflict"] and data["sheet_cols"] == sr.COLS
    assert data["build_id"] == key["build_id"] and data["lang"] == "tr"
    assert all(set(r) == {"review_id", "subset", "fact_a", "fact_b"} for r in data["rows"])
    assert set(data["i18n"]["en"]["short"]) == {"strict_conflict"}
    assert '"strict_sheet.partial.csv" : "strict_sheet.filled.csv"' in page
    blind = page.replace(json.dumps(data["i18n"], ensure_ascii=False).replace("<", "\\u003c"), "")
    sheet_text = (out / "strict_sheet.csv").read_text(encoding="utf-8")
    for leak in ("SECRET-NOTE", "labelled_before", "model_strict", "sh_32k:", "sh_64k:", "sh_6k:",
                 "P000", "D000", "rel one", "rel two"):
        assert leak not in blind and leak not in sheet_text


# ── scoring ──────────────────────────────────────────────────────────────────

def _fill(out, answer_of) -> pathlib.Path:
    key = _key(out)["rows"]
    with open(out / "strict_sheet.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["strict_conflict"] = "yes" if answer_of(key[r["review_id"]]) else "no"
    sr.write_sheet(out / "filled.csv", rows)
    return out / "filled.csv"


def test_score_matches_hand_computed_counts(world):
    out = world()
    key = _key(out)["rows"]
    # new: rel one no, rel two yes, rel three yes; both earlier-labelled texts yes
    sheet = _fill(out, lambda k: k["stratum"] == "labelled_before" or k["relation"] != NAME[1])
    assert sr.main(["score", "--key", str(out / "strict_key.json"), "--sheet", str(sheet),
                    "--out-json", str(out / "S.json"), "--out-md", str(out / "S.md")]) == 0
    rep = json.loads((out / "S.json").read_text(encoding="utf-8"))
    rid = {v["shown_pair_id"]: r for r, v in key.items()}
    assert (rep["n_rows"], rep["strict_yes"]) == (8, 5)
    assert rep["by_stratum"] == {"labelled_before": {"n": 2, "strict_yes": 2},
                                 "new": {"n": 6, "strict_yes": 3}}
    # P000 said no and is now yes; the other text's latest earlier answer (D000) was already yes
    assert rep["against_own_earlier_answer"] == {"n": 2, "same": 1,
                                                 "no_to_yes": [rid["sh_32k:h1"]], "yes_to_no": []}
    # seven rows have a model label: rel one 3 same (no/no), rel three 1 same (yes/yes),
    # rel two 2 and the twice-labelled text are human yes / model no
    m = rep["against_model_relation_only_rule"]
    assert (m["n"], m["same"], len(m["human_yes_model_no"]), m["human_no_model_yes"]) == (7, 4, 3, [])
    assert rid["sh_64k:h4"] in m["human_yes_model_no"]
    assert rep["by_relation"] == {NAME[1]: {"n": 4, "strict_yes": 1},
                                  NAME[2]: {"n": 3, "strict_yes": 3},
                                  NAME[3]: {"n": 1, "strict_yes": 1}}
    assert rep["relations_with_both_answers"] == [NAME[1]]
    assert f"| {NAME[1]} | 4 | 1 |" in (out / "S.md").read_text(encoding="utf-8")


def test_blank_cells_and_foreign_sheets_are_rejected(world):
    out = world()
    key = _key(out)["rows"]
    with pytest.raises(SystemExit, match="expected yes/no"):
        sr.read_strict_sheet(out / "strict_sheet.csv")         # the blank sheet itself
    sheet = sr.read_strict_sheet(_fill(out, lambda k: True))
    sheet["X999"] = sheet.pop("S000")
    with pytest.raises(SystemExit, match="review_ids differ"):
        sr.score_sheet(sheet, key)
