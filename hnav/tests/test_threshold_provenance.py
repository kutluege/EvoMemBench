"""Frozen constants in code == the committed Stage-0 artifacts. Exactly.  [T11]

Supervisor audit Note 2 (Faz A): a constant whose provenance is a docstring can
drift silently; one whose provenance is an equality test cannot. Every frozen
number the read gate ships is compared here against the committed measurement
JSON it claims to come from — ``==``, not ``approx``, because the constants
were COPIED from these files and a copy is either exact or wrong.

When the Faz B calibration freeze lands, this file also pins the Stage-1
operating point (``stage0_results/stage1_operating_point.json``) to the values
``hnav.core.read_policy.stage1_thresholds()`` actually runs with.
"""
from __future__ import annotations

import json
from pathlib import Path

from hnav.core import read_gate, read_policy

REPO = Path(__file__).resolve().parents[2]
FINAL = REPO / "stage0_results/final"


def _load(name: str):
    return json.loads((FINAL / name).read_text(encoding="utf-8"))


def test_m3_thresholds_match_the_gate_constants_exactly():
    rows = _load("m3_headroom.json")
    assert rows, "m3_headroom.json is empty"
    for row in rows:
        thr = row["thresholds"]
        # Every subset row carries the SAME frozen threshold block …
        assert thr["fit_subsets"] == ["sh_6k", "sh_32k"]
        assert thr["unfit_for_analysis"] is False
        # … and the gate constants are byte-for-byte those values.
        assert read_gate.NMARGIN_CAL == thr["nmargin"]
        assert read_gate.H_Z_CAL == thr["H_z"]
        assert read_gate.R_MIN_CAL == thr["r_min"]


def test_cos_pair_is_the_rounded_mean_of_m1b_best_f1_taus_on_calibration():
    rows = {r["subset"]: r for r in _load("m1b_grouping_ablation.json")}
    taus = [rows["sh_6k"]["best_f1"]["tau"], rows["sh_32k"]["best_f1"]["tau"]]
    assert taus == [0.91, 0.93], "m1b calibration taus moved — re-derive COS_PAIR_CAL"
    assert read_gate.COS_PAIR_CAL == round(sum(taus) / 2, 2)


def test_gate_defaults_are_the_frozen_constants():
    thr = read_gate.GateThresholds()
    assert thr.nmargin == read_gate.NMARGIN_CAL
    assert thr.H_z == read_gate.H_Z_CAL
    assert thr.r_min == read_gate.R_MIN_CAL
    assert thr.cos_pair == read_gate.COS_PAIR_CAL


def test_stage1_operating_point_artifact_matches_the_live_thresholds():
    """Until the calibration freeze the artifact does not exist and the live
    thresholds must be the Faz A baseline. Once the artifact is committed the
    equality is mandatory — a frozen operating point the live path does not
    actually run at would invalidate the campaign."""
    art = REPO / "stage0_results/stage1_operating_point.json"
    thr = read_policy.stage1_thresholds()
    if not art.exists():
        assert thr == read_gate.GateThresholds(), (
            "stage1_thresholds() departed from the Faz A baseline without a "
            "committed stage0_results/stage1_operating_point.json")
        return
    op = json.loads(art.read_text(encoding="utf-8"))["thresholds"]
    assert thr.cos_pair == op["cos_pair"]
    assert thr.r_min == op["r_min"]
    assert thr.nmargin == op["nmargin"]
    assert thr.H_z == op["H_z"]
    assert thr.nli_contradiction == op["nli_contradiction"]
    assert thr.ambiguity_mode == op["ambiguity_mode"]


def test_stage1_operating_point_was_fit_on_the_calibration_split_only():
    """The one invariant a threshold artifact can violate silently.  [T13]"""
    art = REPO / "stage0_results/stage1_operating_point.json"
    if not art.exists():
        return
    prov = json.loads(art.read_text(encoding="utf-8"))["provenance"]
    assert sorted(prov["fit_subsets"]) == ["sh_32k", "sh_6k"]
    assert sorted(prov["confirmatory_refused"]) == ["sh_262k", "sh_64k"]


def test_disabling_the_ambiguity_screen_is_declared_in_the_artifact():
    """``ambiguity_mode="none"`` switches off the frozen Stage-0 nmargin/H_z
    precondition. That is a legitimate, argued choice (T13) — but it must never
    be a silent one, so the artifact has to carry the argument, and the frozen
    constants have to stay recorded even while the screen is off."""
    art = REPO / "stage0_results/stage1_operating_point.json"
    thr = read_policy.stage1_thresholds()
    assert thr.nmargin is not None and thr.H_z is not None, (
        "the frozen ambiguity constants must stay on the record even when the "
        "screen is off — otherwise the departure stops being auditable")
    if thr.ambiguity_mode != "none":
        return
    assert art.exists(), (
        "the live gate disables the ambiguity screen but no operating-point "
        "artifact explains why")
    payload = json.loads(art.read_text(encoding="utf-8"))
    assert payload.get("ambiguity_note"), "ambiguity_note missing"
    assert payload["pair_filter"] is True, (
        "with the ambiguity screen off, the identity screen is the only thing "
        "bounding intervention volume; the artifact must record it as required")
