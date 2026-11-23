"""Two-annotator validation — sample, page and scoring against hand-computed values.

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

from hnav.labeling import audit_human_pilot as pilot  # noqa: E402
from hnav.labeling import audit_validation as av  # noqa: E402
from hnav.labeling.agreement_stats import wilson  # noqa: E402

GOLD_YES = {"core", "update_only_fork"}
JUDGE_YES = {"core", "discovered_unverified"}

# pair_id, tier, text, model update, in_eval_set, cosine
SPEC = [
    ("sh_6k:c0", "core", "Core 0", True, True, 0.97), ("sh_6k:c1", "core", "Core 1", True, True, 0.97),
    ("sh_6k:c2", "core", "Core 2", True, True, 0.97), ("sh_6k:c3", "core", "Core 3", True, True, 0.97),
    ("sh_6k:c4", "core", "Core 4", False, True, 0.97),             # model differs: a disputed row
    ("sh_6k:c5", "core", "Core 5", True, True, 0.97),              # same text under another tier:
    ("sh_32k:c5", "update_only_fork", "Core 5", True, True, 0.97),  # not eligible anywhere
    ("sh_6k:n0", "negative", "Neg 0", False, True, 0.95), ("sh_6k:n1", "negative", "Neg 1", False, True, 0.96),
    ("sh_6k:n2", "negative", "Neg 2", False, True, 0.90),          # below the cosine floor
    ("sh_6k:n3", "negative", "Neg 3", False, False, 0.97),         # outside the evaluation set
    ("sh_6k:n4", "negative", "Neg 4", False, True, 0.95),          # labelled in the pilot
    ("sh_6k:f0", "update_only_fork", "Fork 0", True, True, 0.96),
    ("sh_6k:f1", "update_only_fork", "Fork 1", True, True, 0.96),
    ("sh_6k:f2", "update_only_fork", "Fork 2", False, True, 0.96),  # disputed
    ("sh_6k:q0", "discovered_unverified", "Quar 0", False, False, 0.93),
    ("sh_6k:q1", "discovered_unverified", "Quar 1", True, False, 0.93),   # disputed
]
DISPUTED = {"D000": "sh_6k:c4", "D001": "sh_6k:f2", "D002": "sh_6k:q1"}
STAGE4 = {"D000": "no", "D001": "no", "D002": "yes"}               # with the model on all three
EXTRA = [{"id": "new:1", "fact_a": "Tessa Brand lives in Ardel.", "fact_b": "Tessa Brand lives in Morn.",
          "constructed_update": True, "constructed_strict": True},
         {"id": "new:2", "fact_a": "Tessa Brand lives in Ardel.", "fact_b": "Ole Venn lives in Ardel.",
          "constructed_update": False, "constructed_strict": False}]
RUBRIC = "Approved instructions.\n"


@pytest.fixture()
def world(tmp_path):
    gold = [{"pair_id": pid, "subset": pid.split(":")[0], "tier": tier, "in_eval_set": ev,
             "gold_update": tier in GOLD_YES, "gold_strict": tier == "core", "cosine_similarity": cos,
             "fact_a": f"{text} has value <alpha>.", "fact_b": f"{text} has value beta.",
             "judge": {"update_conflict": tier in JUDGE_YES, "strict_conflict": tier == "core"},
             "parser": {"same_key": tier in GOLD_YES}}
            for pid, tier, text, _, ev, cos in SPEC]
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "gold.jsonl").write_text("\n".join(json.dumps(g) for g in gold) + "\n", encoding="utf-8")
    with open(tmp_path / "model.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "pair_id", "update_conflict", "strict_conflict"])
        for i, (pid, tier, _, upd, _, _) in enumerate(SPEC):
            w.writerow([f"a{i}", pid, "yes" if upd else "no", "yes" if upd and tier == "core" else "no"])
    (tmp_path / "pilot_key.json").write_text(json.dumps({"rows": {"P000": {"pair_id": "sh_6k:n4"}}}),
                                             encoding="utf-8")
    (tmp_path / "review_key.json").write_text(json.dumps({"rows": {
        rid: {"shown_pair_id": pid, "pairs": [{"pair_id": pid}]} for rid, pid in DISPUTED.items()}}),
        encoding="utf-8")
    with open(tmp_path / "review.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "update_conflict"])
        w.writerows(STAGE4.items())
    (tmp_path / "extra.jsonl").write_text("\n".join(json.dumps(x) for x in EXTRA) + "\n", encoding="utf-8")
    (tmp_path / "rubric.md").write_text(RUBRIC, encoding="utf-8")

    def build(sub="out", extra=True, **kw):
        out = tmp_path / sub
        argv = ["build", "--gold", str(tmp_path / "gold.jsonl"), "--model-labels", str(tmp_path / "model.csv"),
                "--pilot-key", str(tmp_path / "pilot_key.json"),
                "--review-key", str(tmp_path / "review_key.json"),
                "--review-sheet", str(tmp_path / "review.csv"),
                "--rubric-en", str(tmp_path / "rubric.md"), "--rubric-tr", str(tmp_path / "rubric.md"),
                "--out-dir", str(out)]
        if extra:
            argv += ["--extra", str(tmp_path / "extra.jsonl")]
        for k, v in kw.items():
            argv += [f"--{k.replace('_', '-')}"] + ([] if v is True else [str(v)])
        assert av.main(argv) == 0
        return out
    return build


def _key(out) -> dict:
    return json.loads((out / "validation_key.json").read_text(encoding="utf-8"))


# ── selection ────────────────────────────────────────────────────────────────

def test_strata_take_only_clean_unseen_agreement_pairs(world):
    key = _key(world())
    assert key["strata"] == {
        "disputed": {"eligible": 3, "requested": 3, "drawn": 3},
        "core": {"eligible": 4, "requested": 40, "drawn": 4},          # c4 disputed, c5 mixed tier
        "lookalike": {"eligible": 2, "requested": 40, "drawn": 2},     # n2 cosine, n3 eval set, n4 seen
        "update_only": {"eligible": 2, "requested": 15, "drawn": 2},   # f2 disputed
        "quarantined": {"eligible": 1, "requested": 15, "drawn": 1},   # q1 disputed
        "test_set": {"eligible": 2, "requested": 2, "drawn": 2}}
    rows = key["rows"]
    assert key["n_rows"] == 14 and sorted(rows) == [f"V{i:03d}" for i in range(14)]
    shown = {v["shown_pair_id"]: v for v in rows.values()}
    assert {p for p, v in shown.items() if v["stratum"] == "core"} == {f"sh_6k:c{i}" for i in range(4)}
    assert {p for p, v in shown.items() if v["stratum"] == "lookalike"} == {"sh_6k:n0", "sh_6k:n1"}
    assert {p for p, v in shown.items() if v["stratum"] == "disputed"} == set(DISPUTED.values())
    assert shown["sh_6k:c4"]["stage4"] == {"review_id": "D000", "update_conflict": False}
    assert shown["sh_6k:q1"]["sources"] == {
        "gold_update": False, "gold_strict": False, "judge_update": True, "judge_strict": False,
        "parser_same_key": False, "model_update": True, "model_strict_first_guideline": False}
    assert shown["new:1"]["sources"] == {"constructed_update": True, "constructed_strict": True}
    assert "sh_6k:c5" not in shown and "sh_32k:c5" not in shown and "sh_6k:n4" not in shown


def test_quotas_seed_and_dry_run(world, tmp_path):
    assert _key(world("a")) == _key(world("b"))
    picks = {tuple(sorted(v["shown_pair_id"] for v in _key(world(f"s{s}", seed=s))["rows"].values()))
             for s in range(4)}
    assert len(picks) == 1                                  # every stratum is taken whole here
    orders = {tuple(_key(world(f"o{s}", seed=s))["rows"][f"V{i:03d}"]["shown_pair_id"] for i in range(14))
              for s in range(4)}
    assert len(orders) > 1
    out = world("dry", dry_run=True)
    assert not out.exists()
    gold = [json.loads(l) for l in (tmp_path / "gold.jsonl").read_text(encoding="utf-8").splitlines()]
    model = av.read_model(tmp_path / "model.csv")
    rows, drawn = av.select(gold, model, {}, set(), quotas={"core": 2, "lookalike": 1})
    # with no stage 4 key c4 is still out: the model differs from the released label on it
    assert drawn["core"] == {"eligible": 4, "requested": 2, "drawn": 2}
    assert drawn["lookalike"] == {"eligible": 3, "requested": 1, "drawn": 1}   # n4 is unseen now
    assert drawn["update_only"]["drawn"] == 0 and len(rows) == 3


# ── page ─────────────────────────────────────────────────────────────────────

def test_page_asks_two_questions_and_records_time(world):
    out = world(lang="tr")
    key = _key(out)
    with open(out / "validation_sheet.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["review_id", "subset", "fact_a", "fact_b", "update_conflict",
                                     "strict_conflict", "notes", "seconds", "answered_at"]
        assert {r["review_id"] for r in reader} == set(key["rows"])
    page = (out / "validation_label.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',
                                page, re.S).group(1))
    assert data["label_cols"] == ["update_conflict", "strict_conflict"] and data["sheet_cols"] == av.COLS
    assert data["build_id"] == key["build_id"] and data["lang"] == "tr"
    assert all(set(r) == {"review_id", "subset", "fact_a", "fact_b"} for r in data["rows"])
    assert set(data["i18n"]["en"]["short"]) == set(data["i18n"]["tr"]["short"]) == set(av.LABELS)
    assert data["i18n"]["en"]["rubric"] == RUBRIC
    for piece in ("function tick()", "stamp(r.review_id);", 'c === "seconds"', 'c === "answered_at"',
                  "function go(i) { tick();", '"validation_sheet.filled.csv"', "visibilitychange"):
        assert piece in page
    assert "tick()" not in pilot.PAGE_TEMPLATE and "__STEM__" not in page
    sheet_text = (out / "validation_sheet.csv").read_text(encoding="utf-8")
    blind = page.replace(json.dumps(data["i18n"], ensure_ascii=False).replace("<", "\\u003c"), "")
    for leak in ("sh_6k:", "sh_32k:", "update_only", "quarantined", "lookalike", "disputed",
                 "gold_update", "model_update", "judge", "D000", "constructed"):
        assert leak not in blind and leak not in sheet_text


def test_a_draft_rubric_or_a_drifted_template_stops_the_build(world, tmp_path, monkeypatch):
    (tmp_path / "rubric.md").write_text("DRAFT instructions.\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="still contains 'DRAFT'"):
        world("draft")
    (tmp_path / "rubric.md").write_text("Same attribute [R1] to confirm.\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"still contains '\[R'"):
        world("open")
    monkeypatch.setattr(av, "PAGE_TEMPLATE", pilot.PAGE_TEMPLATE.replace("function go(i)", "function goto(i)"))
    with pytest.raises(SystemExit, match="no longer contains exactly one"):
        av.page_template()


# ── scoring ──────────────────────────────────────────────────────────────────

def _fill(out, name, update_of, strict_of, seconds=lambda p: 10.0, done=lambda p: "2026-12-01T10:00:00Z"):
    key = _key(out)["rows"]
    with open(out / "validation_sheet.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        k = key[r["review_id"]]
        r["update_conflict"] = "yes" if update_of(k) else "no"
        r["strict_conflict"] = "yes" if strict_of(k) else "no"
        r["seconds"] = "" if seconds(k["shown_pair_id"]) is None else seconds(k["shown_pair_id"])
        r["answered_at"] = done(k["shown_pair_id"])
    av.write_sheet(out / name, rows)
    return out / name


def _truth(k):
    s = k["sources"]
    return s["constructed_update"] if "constructed_update" in s else s["gold_update"]


def _kappa(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    pe = (sum(x) / n) * (sum(y) / n) + (1 - sum(x) / n) * (1 - sum(y) / n)
    return (po - pe) / (1 - pe)


def test_score_matches_hand_computed_values(world):
    out = world()
    key = _key(out)["rows"]
    rid = {v["shown_pair_id"]: r for r, v in key.items()}
    # A: the agreed label everywhere except c0 and n0; with the model on all three disputed rows
    a_flip = {"sh_6k:c0", "sh_6k:n0"}
    a_upd = lambda k: (k["sources"]["model_update"] if k["stratum"] == "disputed"
                       else _truth(k) != (k["shown_pair_id"] in a_flip))
    # B: the agreed label except c0; with the model on c4 and f2, with the released label on q1
    b_upd = lambda k: ((k["sources"]["gold_update"] if k["shown_pair_id"] == "sh_6k:q1"
                        else k["sources"]["model_update"]) if k["stratum"] == "disputed"
                       else _truth(k) != (k["shown_pair_id"] == "sh_6k:c0"))
    a = _fill(out, "a.csv", a_upd, lambda k: a_upd(k) and k["stratum"] == "core",
              seconds=lambda p: 2.0 if p == "sh_6k:c1" else None if p == "sh_6k:c2" else 10.0,
              done=lambda p: "" if p == "sh_6k:c3" else "2026-12-01T10:00:00Z")
    b = _fill(out, "b.csv", b_upd, lambda k: k["shown_pair_id"] == "sh_6k:n0")   # strict without update
    assert av.main(["score", "--key", str(out / "validation_key.json"), "--sheet-a", str(a),
                    "--sheet-b", str(b), "--out-json", str(out / "S.json"),
                    "--out-md", str(out / "S.md")]) == 0
    rep = json.loads((out / "S.json").read_text(encoding="utf-8"))
    assert (rep["n_rows"], rep["annotators"]) == (14, 2)
    A, B = rep["annotator"]["A"], rep["annotator"]["B"]

    # agreement strata: 4 core + 2 lookalike + 2 update-only + 1 quarantined = 9 rows
    assert A["agreement_strata"]["contradicts_agreed_label"] == sorted([rid["sh_6k:c0"], rid["sh_6k:n0"]])
    assert A["agreement_strata"]["error_rate"]["wilson95"] == pytest.approx(list(wilson(2, 9)))
    assert B["agreement_strata"]["contradicts_agreed_label"] == [rid["sh_6k:c0"]]
    assert rep["both_annotators"]["agreement_strata_both_contradict"]["review_ids"] == [rid["sh_6k:c0"]]
    assert rep["both_annotators"]["agreement_strata_both_contradict"]["error_rate"]["n"] == 9

    assert A["disputed"] == {"n": 3, "sides_with_released_label": 0, "sides_with_model": 3}
    assert B["disputed"] == {"n": 3, "sides_with_released_label": 1, "sides_with_model": 2}
    assert rep["both_annotators"]["disputed"] == {"n": 3, "annotators_agree": 2,
                                                  "sides_with_released_label": 0, "sides_with_model": 2}

    # A against the released label: 9 agreement rows minus 2, plus 0 of 3 disputed = 7 of 12
    src = A["against_sources"]
    assert (src["update_conflict vs gold_update"]["n"], src["update_conflict vs gold_update"]["k"]) == (12, 7)
    assert (src["update_conflict vs model_update"]["n"], src["update_conflict vs model_update"]["k"]) == (12, 10)
    assert (src["update_conflict vs constructed_update"]["n"],
            src["update_conflict vs constructed_update"]["k"]) == (2, 2)
    assert B["strict_without_update"] == [rid["sh_6k:n0"]] and A["strict_without_update"] == []

    ids = sorted(key)
    sa, sb = av.read_sheet(a), av.read_sheet(b)
    x, y = [sa[r]["update_conflict"] for r in ids], [sb[r]["update_conflict"] for r in ids]
    assert sum(u != v for u, v in zip(x, y)) == 2          # n0 and q1
    hh = rep["human_human"]["all"]["update_conflict"]
    assert hh["agreement"] == pytest.approx(12 / 14) and hh["kappa"] == pytest.approx(_kappa(x, y))
    assert rep["human_human"]["disputed"]["update_conflict"]["agreement"] == pytest.approx(2 / 3)

    t = A["timing"]                                         # 13 timed rows: twelve at 10 s, one at 2 s
    assert (t["rows_with_time"], t["median_seconds"], t["rows_under_3_seconds"]) == (13, 10.0, 1)
    assert t["total_minutes"] == pytest.approx(round(122 / 60, 1))
    assert t["rows_without_completion_time"] == 1
    md = (out / "S.md").read_text(encoding="utf-8")
    assert "| all | update_conflict | 14 |" in md and "## Annotator B" in md


def test_one_sheet_scores_alone_and_bad_sheets_are_rejected(world):
    out = world(extra=False)
    key = _key(out)["rows"]
    a = _fill(out, "a.csv", _truth, lambda k: False)
    rep = av.score_sheets(key, av.read_sheet(a))
    assert rep["annotators"] == 1 and "human_human" not in rep and rep["n_rows"] == 12
    with pytest.raises(SystemExit, match="expected yes/no"):
        av.read_sheet(out / "validation_sheet.csv")
    bad = _fill(out, "bad.csv", _truth, lambda k: False, seconds=lambda p: "soon")
    with pytest.raises(SystemExit, match="not a number"):
        av.read_sheet(bad)
    sheet = av.read_sheet(a)
    sheet["X1"] = sheet.pop("V000")
    with pytest.raises(SystemExit, match="review_ids differ"):
        av.score_sheets(key, sheet)
