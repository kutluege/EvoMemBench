#!/usr/bin/env python3
"""Detector-to-oracle gap: how much of the probe's ceiling survives detection?  [T13]

The oracle probe (``hnav/stage1/stale_suppression_probe.py``, ``sh_6k``, 473
real calls against the frozen :8003 substrate) measured what a PERFECT conflict
detector would buy on the conflicted stratum:

    arm                       overall   unique   conflicted     McNemar vs native
    native                    0.290     25/26    4/74  (5.4%)   --
    native_repeat             0.290     25/26    4/74           0/0  (A/A floor)
    oracle_suppress           0.910     25/26    66/74 (89.2%)  net +62, p=4.3e-19
    oracle_recency            0.460     26/26    20/74 (27.0%)  net +17, p=7.6e-05
    anti (latest to FRONT)    0.260     25/26    1/74  (1.4%)   net -3, n.s.

Those arms read the ANSWER to decide which fact to cut or move. A shipped
policy may not. This module runs the identical 5-arm design with the arms
driven by :class:`~hnav.core.read_gate.ReadGate` plus the T13 fact-level
mechanisms in ``hnav/core/read_policy.py`` — embedding geometry and
bidirectional NLI only, no gold, no answers, no future facts — and reports, per
mechanism, the number the thesis actually needs:

    detector-achieved  /  oracle-achieved

together with the detector's precision and recall at the operating point used,
so a reader can attribute whatever is missing to *detection* rather than to the
mechanism (or the other way round).

Arms
----
``native``                 the untouched context.
``native_repeat``          the same prompt, an independent second call: the
                           in-harness A/A floor. The oracle probe measured it at
                           literally 0/0 discordant over 100 questions, so every
                           effect below is read against a measured zero.
``detector_suppress``      ``ReadFactPolicy("suppress")`` — every stale member of
                           every VERIFIED conflict group in the retrieved pool is
                           deleted. This is deliberately NOT the oracle edit
                           restricted to the queried key: the detector does not
                           know which key is queried, so it cleans the whole
                           page, and that collateral is part of what is measured.
``detector_demote_late``   ``ReadFactPolicy("demote_late")`` — every verified
                           group's LATEST carrier moves to the END of the
                           context in ascending serial order; nothing is deleted.
``detector_anti``          the mirror: the same LATEST carriers move to the
                           FRONT. **Measurement only** — no such mechanism exists
                           in ``hnav/core/``. It is the direction control: if
                           placement is the mechanism at all, ``demote_late`` and
                           ``anti`` must move the number in OPPOSITE directions.

Where the detector's inputs come from
-------------------------------------
``hnav/_out/stage1_prepass_<subset>.json`` (T11): the campaign-faithful chunk
ranking per question, the retrieval signals, the candidate pool built by the
adapter's own :func:`~hnav.adapters.mab_adapter.select_pool`, the pair geometry,
and the real DeBERTa-v3 bidirectional NLI scores. Those scores are replayed into
the REAL ``ReadGate`` through ``calibrate_read_policy.ReplayNLI`` — imported, so
no second gate exists to drift from the first.

Fact VECTORS come from the shared embedding cache and are then PROVEN to be the
prepass's own: every pair cosine recomputed from the loaded vectors must
reproduce the prepass's stored ``cos`` to 1e-6, over every pair of every
question, or the run refuses. The namespace is auto-detected across the
historical cache keys because ``cache_key`` gained its ``max_length`` component
after this prepass was written (T12) — and a stale cache hit is worse than a
miss, because it looks like a result.

Two declared limitations of that input, neither configurable away
----------------------------------------------------------------
1. The prepass's CHUNK vectors were embedded under the 512-token truncation
   defect while a chunk is ~4096 tokens, so ``nmargin``/``H_z`` — and only those
   — are contaminated. They feed exactly one thing: the gate's ambiguity
   precondition, which the frozen operating point therefore disables
   (``ambiguity_mode="none"``; the full argument is in :func:`select`). FACT
   vectors are unaffected — one short sentence is far under 512 tokens — and the
   cosine proof above shows the vectors used are the ones the prepass used.
2. The prepass predates NLI-config stamping. ``--allow-unstamped-prepass``
   accepts it; the artifact records that it did, alongside the measured
   character-length headroom that makes it harmless in this arena (a fact pair
   is tens of tokens against a 256-token budget).

Harness
-------
Identical to the probe's and imported from it: the whole context as a single
``Memory 1:`` block in context order, the benchmark's system message and query
template, ``substring_exact_match``, ``generation_max_length=10``, the frozen
:8003 chat server. Identical on purpose — the headline is a RATIO against the
oracle arms, and a ratio taken across two harnesses means nothing.

Arms are built with the probe's own ``suppress`` / ``move_to_end`` /
``move_to_front`` helpers and then re-derived through the SHIPPED page-contract
path (:func:`~hnav.adapters.mab_adapter.page_edit`) and asserted byte-identical.
So the measurement exercises the code that would ship, and the artifact reports
``n_page_edit_mismatch`` — which must be 0 — instead of leaving it to trust.

Split discipline
----------------
``sh_6k`` + ``sh_32k`` only; ``sh_64k``/``sh_262k`` are refused outright
(exit 2). The operating point is chosen by ``--select`` from DETECTION quality
alone — no LLM, no accuracy, no gold answer — and frozen to
``stage0_results/stage1_operating_point.json`` BEFORE any arm is graded.
``config.require_not_live()``: a measurement taken under intervention is not a
measurement.

Running it
----------
    python hnav/stage1/detector_gap.py --select                 # freeze, no LLM
    python hnav/stage1/detector_gap.py --subsets sh_6k --dry-run
    python hnav/stage1/detector_gap.py --subsets sh_6k --smoke-llm
    HNAV_LLM_BASE_URL=http://localhost:8003/v1 \
        python hnav/stage1/detector_gap.py --subsets sh_6k
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav import config as _config  # noqa: E402
from hnav.adapters.mab_adapter import (MABAdapter, _fact_separator,  # noqa: E402
                                       explode_facts, fact_spans, page_edit)
from hnav.core import read_gate as _rg  # noqa: E402
from hnav.core.read_gate import GateThresholds, ReadGate  # noqa: E402
from hnav.core.read_policy import demote_ids, suppress_ids  # noqa: E402
from hnav.core.types import MemoryRecord  # noqa: E402
from hnav.labeling.counterfactual import substring_exact_match  # noqa: E402
from hnav.stage0.m2_retrieval_calibration import build_chunks  # noqa: E402
from hnav.labeling.question_strata import (STRATA, classify_questions,  # noqa: E402
                                           key_members)
# Imported, never re-transcribed: the gate replay, the grid axes, and the whole
# prompting / statistics harness the oracle numbers were produced with.
from hnav.stage1.calibrate_read_policy import (AMB_GRID, CALIBRATION,  # noqa: E402
                                               COS_GRID, FILTER_GRID,
                                               GENERATION_MAX_TOKENS, NLI_GRID,
                                               QUERY_TEMPLATE,
                                               R_MIN_GRID_LABELS, ReplayNLI,
                                               SYSTEM_MESSAGE, _CachedQR,
                                               build_user_prompt, r_min_of)
from hnav.stage1.stale_suppression_probe import (_acc, _sha,  # noqa: E402
                                                 build_prompt, move_to_end,
                                                 move_to_front, paired_cells,
                                                 primacy_stub, render_context,
                                                 split_context, suppress)

DATA = REPO / "In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/data/Conflict_Resolution.json"
ORACLE_DIR = REPO / "stage0_results/stage1"
OPERATING_POINT = REPO / "stage0_results/stage1_operating_point.json"
CONFIRMATORY = ("sh_64k", "sh_262k")
ARMS = ("native", "native_repeat", "detector_suppress", "detector_demote_late",
        "detector_anti")
EDIT_ARMS = ("detector_suppress", "detector_demote_late", "detector_anti")
# Which oracle arm each detector arm is the achievable counterpart of.
ORACLE_COUNTERPART = {"detector_suppress": "oracle_suppress",
                      "detector_demote_late": "oracle_recency",
                      "detector_anti": "anti"}
COS_TOLERANCE = 1e-6
HARNESSES = ("whole_context", "retrieval")
CHUNK_SIZE = 4096                       # the benchmark's own chunk_text_into_sentences
# r_min_label ordering, tightest first — used only as a deterministic tie-break.
R_RANK = {"frozen": 0, "loose": 1, "off": 2}
AMB_RANK = {"all": 0, "any": 1, "none": 2}


# ── ground truth, from fact TEXT alone (no answers involved) ─────────────────
def fact_table(item: dict) -> dict:
    """Everything the detector's ground truth needs, decided by the validated
    parser without reading a single answer.

    ``by_id``       fact id -> ``(serial, text, key, object)``
    ``superseded``  fact ids for which a LATER fact of the same key carries a
                    DIFFERENT object — genuinely stale under the benchmark's own
                    stated rule.
    ``latest``      key -> highest serial carrying that key.
    ``latest_obj``  key -> that fact's object.
    """
    members = key_members(item)
    by_id, superseded, latest, latest_obj = {}, set(), {}, {}
    for key, rows in members.items():
        top = max(rows)
        latest[key], latest_obj[key] = top[0], top[2]
        for s, text, obj in rows:
            by_id[f"fact:{s}"] = (s, text, key, obj)
            if any(s2 > s and o2 != obj for s2, _, o2 in rows):
                superseded.add(f"fact:{s}")
    return {"by_id": by_id, "superseded": superseded, "latest": latest,
            "latest_obj": latest_obj, "members": members}


def gt_pairs(ids, by_id) -> set[tuple[str, str]]:
    """Unordered pairs of ``ids`` that are TRUE supersession pairs: same
    ``(relation, subject)`` key, different object. Same definition
    ``calibrate_read_policy`` scores its false-verified rate against."""
    known = [i for i in ids if i in by_id]
    out = set()
    for a in range(len(known)):
        ia = known[a]
        ka, oa = by_id[ia][2], by_id[ia][3]
        if ka is None:
            continue
        for b in range(a + 1, len(known)):
            ib = known[b]
            if ka == by_id[ib][2] and oa != by_id[ib][3]:
                out.add((min(ia, ib), max(ia, ib)))
    return out


def count_gt_pairs(ids, by_id) -> int:
    """``len(gt_pairs(...))`` in linear time — a full page can hold thousands of
    facts and the quadratic form is only affordable on the 50-fact pool."""
    per_key: dict[tuple, list[str]] = {}
    for i in ids:
        row = by_id.get(i)
        if row and row[2] is not None:
            per_key.setdefault(row[2], []).append(row[3])
    total = 0
    for objs in per_key.values():
        n = len(objs)
        same = 0
        counts: dict[str, int] = {}
        for o in objs:
            counts[o] = counts.get(o, 0) + 1
        for c in counts.values():
            same += c * (c - 1) // 2
        total += n * (n - 1) // 2 - same
    return total


# ── vectors: the prepass's own, proven rather than assumed ───────────────────
class _FailOnMiss:
    dim = 0

    def encode(self, texts):
        raise RuntimeError(f"{len(texts)} text(s) missing from the cache, "
                           f"first={texts[0][:60]!r}")


def cosine_error(vecs: np.ndarray, order: list[str], prepasses) -> float:
    """Largest absolute deviation between a pair cosine recomputed from
    ``vecs`` and the cosine the prepass recorded for that pair. Zero pairs is
    reported as ``inf`` — an unverifiable namespace is not a verified one."""
    idx = {fid: i for i, fid in enumerate(order)}
    worst, n = 0.0, 0
    m = np.asarray(vecs, dtype=np.float64)
    for pp in prepasses:
        for q in pp["questions"]:
            for p in q["pairs"]:
                if p["a"] not in idx or p["b"] not in idx:
                    continue
                got = float(m[idx[p["a"]]] @ m[idx[p["b"]]])
                worst = max(worst, abs(got - float(p["cos"])))
                n += 1
    return worst if n else float("inf")


def load_fact_vectors(cfg, order, texts, prepasses) -> tuple[np.ndarray, str, float]:
    """Fact vectors from the shared cache, under whichever namespace the prepass
    was written with — auto-detected, then proven by :func:`cosine_error`."""
    from hnav.core.embedding import DiskCachedEmbedder, cache_key
    keys = [f"{cfg.embed_model}|{cfg.embed_dtype}".replace("/", "_"),
            cache_key(cfg.embed_model, cfg.embed_dtype, 512),
            cache_key(cfg.embed_model, cfg.embed_dtype, cfg.embed_max_length)]
    errors = []
    for key in dict.fromkeys(keys):
        try:
            emb = DiskCachedEmbedder(_FailOnMiss(), cfg.emb_cache_dir, key,
                                     persist=False)
            vecs = emb.encode(list(texts))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{key}: {str(e)[:120]}")
            continue
        err = cosine_error(vecs, order, prepasses)
        if err <= COS_TOLERANCE:
            return vecs, key, err
        errors.append(f"{key}: max cosine error {err:.3g} > {COS_TOLERANCE}")
    raise SystemExit(
        " REFUSED: no embedding-cache namespace reproduces the prepass "
        "geometry.\n   " + "\n   ".join(errors) +
        "\n The gate would then be running on vectors that are not the ones the "
        "prepass\n measured, which is exactly the failure T12 exists to remove. "
        "Re-run the\n prepass with the current embedder, or point HNAV_CACHE_DIR "
        "at its cache.")


# ── prepass -> gate input ────────────────────────────────────────────────────
def build_records(order, texts, table, vecs) -> dict[str, MemoryRecord]:
    """``fact id -> MemoryRecord`` with the vector, the serial as ``version``
    and the parsed key/object in metadata — the exact shape the live adapter
    hands the gate (``MABAdapter.candidate_for``)."""
    out = {}
    for i, fid in enumerate(order):
        serial, text, key, obj = table["by_id"][fid]
        out[fid] = MemoryRecord(id=fid, text=text, vector=vecs[i], version=serial,
                                metadata={"key": key, "object": obj})
    return out


def make_gate(cell, replay) -> ReadGate:
    return ReadGate(replay, GateThresholds(
        cos_pair=cell["cos_pair"], r_min=cell["r_min"],
        ambiguity_mode=cell["ambiguity_mode"],
        nli_contradiction=cell["nli_contradiction"]),
        pair_filter=MABAdapter.same_key_pair if cell["pair_filter"] else None)


def decide_all(prepass, recs, cells, replay):
    """``{question index: {cell index: GateDecision}}`` for one subset.

    Questions outer, cells inner, with ``_CachedQR`` installed exactly as
    ``calibrate_read_policy.evaluate`` installs it (and restored), so an
    identical leave-one-out QR is computed once per question rather than once
    per (question, cell).
    """
    gates = [make_gate(c, replay) for c in cells]
    qr_cache = _CachedQR()
    real_qr = _rg.qr_residual
    _rg.qr_residual = qr_cache
    out: dict[int, list] = {}
    try:
        for q in prepass["questions"]:
            pool = [recs[f] for f in q["pool"] if f in recs]
            if len(pool) >= 2:
                qr_cache.load(np.stack([np.asarray(r.vector, dtype=np.float64)
                                        for r in pool]))
            sig = {"nmargin": q["nmargin"], "H_z": q["H_z"]}
            out[q["index"]] = [g.decide(pool, sig,
                                        latest_key=MABAdapter.latest_key)
                               for g in gates]
    finally:
        _rg.qr_residual = real_qr
    return out


# ── detection metrics ────────────────────────────────────────────────────────
def blank_metrics() -> dict:
    return {"n_questions": 0, "tp": 0, "fp": 0, "gt_pool": 0, "gt_page": 0,
            "n_suppressed": 0, "n_suppressed_superseded": 0,
            "n_suppressed_same_value": 0, "n_suppressed_harmful": 0,
            "n_demoted": 0, "n_demoted_is_latest": 0,
            "n_conflicted": 0, "n_conflicted_hit": 0, "n_conflicted_gold_cut": 0,
            "n_unique": 0, "n_unique_touched": 0, "n_touched": 0,
            "n_ambiguous_pass": 0}


def classify_drops(m: dict, drop, table) -> None:
    """Split a suppression set into superseded / same-value / HARMFUL.

    The criterion is what the edit does to the PAGE, not what one fact looks
    like in isolation: for every key the drop set touches, take the members that
    survive and ask whether the key's newest surviving value is still the key's
    newest value. If it is not — or if the key loses every member — then every
    fact dropped from that key counts as harmful, because the page now says
    something different about that key than the corpus does.

    Getting this per-fact instead of per-key is exactly the mistake that would
    let a single-member key be waved through as a "duplicate restatement": its
    only fact IS its latest value, so ``object == latest_object`` is true right
    up to the moment deleting it erases the key.
    """
    by_id, members = table["by_id"], table["members"]
    dropped_serials = {by_id[f][0] for f in drop if f in by_id}
    per_key: dict[tuple, list[str]] = {}
    unknown = 0
    for fid in drop:
        row = by_id.get(fid)
        if row is None or row[2] is None:
            unknown += 1                    # unparsed: no defensible reasoning
            continue
        per_key.setdefault(row[2], []).append(fid)
    m["n_suppressed_harmful"] += unknown

    for key, fids in per_key.items():
        rows = sorted(members[key])
        survivors = [r for r in rows if r[0] not in dropped_serials]
        if not survivors or survivors[-1][2] != rows[-1][2]:
            m["n_suppressed_harmful"] += len(fids)
            continue
        for fid in fids:
            if fid in table["superseded"]:
                m["n_suppressed_superseded"] += 1
            else:
                m["n_suppressed_same_value"] += 1


def score_decision(m: dict, dec, table, strat, pool_ids, page_gt: int) -> None:
    """Accumulate one question's detection outcome into ``m``.

    Everything except the two ``n_conflicted_*`` counters is parse-derived: it
    uses fact text and serial order only. The conflicted-stratum counters use
    the question->key assignment from ``question_strata``, which is gold-derived
    — they are reported for ATTRIBUTION and are never used to choose an
    operating point (see :func:`select`).
    """
    by_id = table["by_id"]
    m["n_questions"] += 1
    if dec.ambiguous:
        m["n_ambiguous_pass"] += 1
    m["gt_pool"] += len(gt_pairs(pool_ids, by_id))
    m["gt_page"] += page_gt

    for pc in dec.pair_checks:
        if not pc.verified:
            continue
        ra, rb = by_id.get(pc.id_a), by_id.get(pc.id_b)
        true_pair = bool(ra and rb and ra[2] is not None and ra[2] == rb[2]
                         and ra[3] != rb[3])
        m["tp" if true_pair else "fp"] += 1

    drop = suppress_ids(dec)
    move = demote_ids(dec)
    m["n_suppressed"] += len(drop)
    m["n_demoted"] += len(move)
    if drop or move:
        m["n_touched"] += 1
    classify_drops(m, drop, table)
    for fid in move:
        row = by_id.get(fid)
        if row and row[2] is not None and table["latest"][row[2]] == row[0]:
            m["n_demoted_is_latest"] += 1

    if strat["stratum"] == "unique":
        m["n_unique"] += 1
        if drop or move:
            m["n_unique_touched"] += 1
    elif strat["stratum"] == "conflicted":
        m["n_conflicted"] += 1
        key = tuple(strat["key"])
        top = table["latest"][key]
        others = [s for s in strat["member_serials"] if s != top]
        cut = {int(f.split(":")[1]) for f in drop}
        if any(s in cut for s in others) and top not in cut:
            m["n_conflicted_hit"] += 1
        if strat["target_serial"] in cut:
            m["n_conflicted_gold_cut"] += 1


def finish_metrics(m: dict) -> dict:
    ver = m["tp"] + m["fp"]
    out = dict(m)
    out["pair_precision"] = (m["tp"] / ver) if ver else None
    out["pair_recall_pool"] = (m["tp"] / m["gt_pool"]) if m["gt_pool"] else None
    out["pair_recall_page"] = (m["tp"] / m["gt_page"]) if m["gt_page"] else None
    out["fact_precision"] = ((m["n_suppressed_superseded"] / m["n_suppressed"])
                             if m["n_suppressed"] else None)
    out["question_recall_conflicted"] = ((m["n_conflicted_hit"] / m["n_conflicted"])
                                         if m["n_conflicted"] else None)
    out["coverage"] = (m["n_touched"] / m["n_questions"]) if m["n_questions"] else None
    return out


# ── the grid and the pre-registered choice ───────────────────────────────────
def grid_cells() -> list[dict]:
    """The SAME axes ``calibrate_read_policy`` declared for the rerank
    calibration — reused rather than redeclared so the two searches cannot
    silently diverge."""
    cells = []
    for cos in COS_GRID:
        for rlab in R_MIN_GRID_LABELS:
            for amb in AMB_GRID:
                for tau in NLI_GRID:
                    for filt in FILTER_GRID:
                        cells.append({"cos_pair": cos, "r_min_label": rlab,
                                      "r_min": r_min_of(rlab),
                                      "ambiguity_mode": amb,
                                      "nli_contradiction": tau,
                                      "pair_filter": filt})
    return cells


SELECTION_RULE = {
    "require": [
        "pair_filter is True",
        "n_suppressed_harmful == 0",
    ],
    "maximise": "pair_recall_pool",
    "tie_break": ["higher cos_pair", "higher nli_contradiction",
                  "tighter r_min (frozen<loose<off)",
                  "stricter ambiguity_mode (all<any<none)"],
    "fit_on": "detection quality only - no LLM, no accuracy, no gold answer",
    "split": "sh_6k + sh_32k (calibration) ONLY",
}


def select(cells: list[dict]) -> dict | None:
    """Apply :data:`SELECTION_RULE`, which was frozen before any cell was scored.

    ``pair_filter is True`` is a REQUIREMENT, not a preference. The Faz A audit
    measured the NLI cross-encoder rubber-stamping same-template /
    different-subject pairs as bidirectional contradiction, and the T11
    calibration showed what that does downstream: with the identity screen OFF,
    ~86% of verifications were spurious and the resulting "gains" were noise
    (``STAGE1_NULL_ANALIZI.md`` §3). A gain built on a detector that cannot tell
    subjects apart is not a gain.

    ``n_suppressed_harmful == 0`` is the deletion criterion: not one suppressed
    fact may carry its key's CURRENT value. A fact that is genuinely superseded
    is safe to drop, and so is a same-valued duplicate; anything else is
    information loss, which no recall figure buys back.

    The objective is ``pair_recall_pool`` — TRUE supersession pairs verified,
    over the true supersession pairs present in the candidate pool. It is
    entirely parse-derived. The question-level and accuracy figures are reported
    but deliberately excluded from the objective: fitting the gate on either
    would make the calibration split a training set for the outcome.

    Note what a "none" ambiguity mode means if it wins: the frozen Stage-0
    ``nmargin``/``H_z`` precondition is disabled. That is defensible here and
    only here, for three stated reasons — those two signals are computed from
    CHUNK embeddings truncated at 512 of ~4096 tokens (the T12 defect, not yet
    re-fit because re-embedding is blocked while both servers hold the GPUs), so
    they are the one contaminated input the gate has; they are the dominant
    recall bottleneck; and the volume-limiting job they were doing is now done
    by the identity screen and the bidirectional NLI at measured precision 1.00.
    A campaign that re-fits the embeddings must revisit this.
    """
    feasible = [c for c in cells
                if c["pair_filter"] and c["metrics"]["n_suppressed_harmful"] == 0
                and c["metrics"]["pair_recall_pool"] is not None]
    if not feasible:
        return None
    feasible.sort(key=lambda c: (-c["metrics"]["pair_recall_pool"],
                                 -c["cos_pair"], -c["nli_contradiction"],
                                 R_RANK[c["r_min_label"]],
                                 AMB_RANK[c["ambiguity_mode"]]))
    return feasible[0]


# ── arms ─────────────────────────────────────────────────────────────────────
def arm_facts(arm: str, facts, plan) -> list[tuple[int, str]]:
    """The fact list one arm shows the model. Built with the PROBE's own
    helpers, so the only difference between an oracle arm and its detector
    counterpart is which serials were chosen."""
    if arm in ("native", "native_repeat"):
        return list(facts)
    if arm == "detector_suppress":
        return suppress(facts, plan["suppress_serials"])
    out = list(facts)
    if arm == "detector_demote_late":
        for s in plan["demote_serials"]:            # ascending: newest ends LAST
            out = move_to_end(out, s)
        return out
    if arm == "detector_anti":
        for s in plan["demote_serials"]:            # ascending: newest ends FIRST
            out = move_to_front(out, s)
        return out
    raise ValueError(f"unknown arm {arm!r}")


def shipped_page(arm: str, context: str, plan) -> str | None:
    """The same edit through the SHIPPED page contract, or ``None`` for an arm
    that has no shipped mechanism (``detector_anti``)."""
    ids_s = [f"fact:{s}" for s in plan["suppress_serials"]]
    ids_d = [f"fact:{s}" for s in plan["demote_serials"]]
    if arm == "detector_suppress":
        return page_edit([context], drop_ids=ids_s)[0][0]
    if arm == "detector_demote_late":
        return page_edit([context], move_last_ids=ids_d)[0][0]
    return None


# ── the retrieval-path harness (prereg v2 section 10) ────────────────────────
# The deployed system never reads a whole-context block: it reads the top_k
# retrieved CHUNKS, numbered "Memory i:", in similarity-rank order. All T13
# calibration evidence is whole-context, which is a documented deviation that
# was justified by retrieval being COMPLETE on the calibration split (2 and 9
# chunks against top_k=10). It stops being justified at sh_64k, which is 17
# chunks. This harness closes that gap: on the calibration split it changes ONLY
# the block structure and order, so it isolates that variable from retrieval
# incompleteness, which appears only on the confirmatory subset.
#
# Here the arms ARE the shipped page contract - `page_edit` applied to the real
# retrieved page - rather than a probe-style rebuild that is then checked
# against it.


def chunk_texts_for(item, prepass) -> list[str]:
    """The benchmark's own chunks, rebuilt and CHECKED against the prepass.

    The prepass stores chunk ids and a fact->chunk map but not chunk text, so
    the text is regenerated with the benchmark's chunker and then verified:
    identical fact->chunk assignment, fact for fact. A silent chunker drift
    would otherwise put different bytes on the page than the geometry that
    drives the gate was measured on.
    """
    chunks, fallback = build_chunks(item["context"], CHUNK_SIZE)
    if fallback:
        raise SystemExit(
            " REFUSED: nltk/punkt is missing, so build_chunks fell back and "
            "these are not the benchmark's chunks.")
    got = {}
    for i, c in enumerate(chunks):
        for serial, _ in explode_facts(c):
            got[f"fact:{serial}"] = f"chunk:{i}"
    want = prepass["fact_chunk"]
    if got != want:
        diff = sorted(k for k in set(got) | set(want) if got.get(k) != want.get(k))
        raise SystemExit(
            f" REFUSED: the rebuilt chunks disagree with the prepass on "
            f"{len(diff)} fact(s), first={diff[:3]}. The page would not be the "
            "one the gate's geometry was measured on.")
    return chunks


def page_move_front(page_texts, ids):
    """MEASUREMENT ONLY — the direction control's mirror of ``DEMOTE_LATE``.

    Deliberately NOT in ``hnav/adapters/``: no ``Decision`` action can produce a
    front-move, and putting one on the shipped surface would create a third
    mechanism nobody authorised. It reuses ``fact_spans`` and the adapter's own
    separator rule (imported, not re-transcribed) so that the bytes it moves are
    the same bytes ``page_edit`` would move, and it is exercised by
    ``detector_anti`` and nothing else.

    Facts are inserted in DESCENDING serial order before the first fact of the
    first chunk, so the newest ends up first — the exact mirror of
    ``page_edit``'s ascending append.
    """
    texts = list(page_texts)
    spans = [fact_spans(t) for t in texts]
    where: dict = {}
    for ci, sp in enumerate(spans):
        for fs in sp:
            where.setdefault(f"fact:{fs.serial}", (ci, fs))
    missing = [i for i in ids if i not in where]
    if missing:
        raise LookupError(f"{len(missing)} id(s) not on this page, "
                          f"first={missing[0]!r}")
    if not ids:
        return texts

    sep = _fact_separator(spans, texts)
    moved = sorted(((where[i][1].serial, i) for i in ids), reverse=True)
    moved_bytes = [texts[where[i][0]][where[i][1].start: where[i][1].own_end]
                   for _, i in moved]

    cuts: dict = {}
    for i in ids:
        ci, fs = where[i]
        cuts.setdefault(ci, []).append(fs)
    out = list(texts)
    for ci, ss in cuts.items():
        t = out[ci]
        for fs in sorted(ss, key=lambda x: x.del_start, reverse=True):
            t = t[: fs.del_start] + t[fs.del_end:]
        out[ci] = t

    head = fact_spans(out[0])
    pos = head[0].start if head else len(out[0].rstrip())
    out[0] = out[0][:pos] + "".join(m + sep for m in moved_bytes) + out[0][pos:]
    return out


def retrieval_arm_page(arm: str, page, plan):
    """The page one arm shows the model, through the SHIPPED edit path."""
    if arm in ("native", "native_repeat"):
        return list(page)
    drop = [f"fact:{s}" for s in plan["suppress_serials"]]
    move = [f"fact:{s}" for s in plan["demote_serials"]]
    if arm == "detector_suppress":
        return page_edit(page, drop_ids=drop)[0]
    if arm == "detector_demote_late":
        return page_edit(page, move_last_ids=move)[0]
    if arm == "detector_anti":
        return page_move_front(page, move)
    raise ValueError(f"unknown arm {arm!r}")


def page_facts(page) -> list:
    return sorted(f for t in page for f in explode_facts(t))


def retrieval_integrity(arm: str, page, edited, plan) -> bool:
    """Did the edit do exactly what the arm claims, and nothing else?

    Same chunk count always; the fact multiset is preserved by both placement
    arms and reduced by exactly the named facts by ``SUPPRESS``. Returns True on
    a violation, so the caller can count violations the way the whole-context
    harness counts ``page_edit`` mismatches — and refuse the run before sending
    anything.
    """
    if len(edited) != len(page):
        return True
    before, after = page_facts(page), page_facts(edited)
    if arm in ("native", "native_repeat"):
        return after != before
    if arm == "detector_suppress":
        drop = set(plan["suppress_serials"])
        return after != sorted(f for f in before if f[0] not in drop)
    return after != before


def plan_subset(item, name, prepass, decisions, cell_i, table,
                max_questions=None, harness: str = "whole_context") -> dict:
    """Build every arm for one subset, under either harness.

    ``whole_context`` reproduces the oracle probe exactly (one ``Memory 1:``
    block in context order) and CHECKS each edit against the shipped
    ``page_edit``. ``retrieval`` puts the benchmark's own top-k chunks on the
    page in rank order and performs the edit THROUGH ``page_edit``, checking
    instead that the result did exactly what the arm claims. Either way the
    counter is ``n_page_edit_mismatch`` and either way a non-zero value refuses
    the run before a call is sent.
    """
    if harness not in HARNESSES:
        raise ValueError(f"harness={harness!r} not in {HARNESSES}")
    preamble, facts = split_context(item["context"])
    strata = {r["index"]: r for r in classify_questions(item)}
    chunks = chunk_texts_for(item, prepass) if harness == "retrieval" else None

    questions, mismatches, pages = [], 0, []
    for q in prepass["questions"]:
        if max_questions and len(questions) >= max_questions:
            break
        dec = decisions[q["index"]][cell_i]
        plan = {
            "suppress_serials": sorted(int(f.split(":")[1])
                                       for f in suppress_ids(dec)),
            "demote_serials": sorted(int(f.split(":")[1])
                                     for f in demote_ids(dec)),
            "n_groups": len(dec.groups),
            "n_pairs_verified": dec.n_pairs_verified,
        }
        rec = strata[q["index"]]
        arms = {}
        if harness == "whole_context":
            for arm in ARMS:
                fl = arm_facts(arm, facts, plan)
                text = render_context(preamble, fl)
                if arm in ("detector_suppress", "detector_demote_late"):
                    if shipped_page(arm, item["context"], plan) != text:
                        mismatches += 1
                arms[arm] = {"prompt": build_prompt(text, rec["question"]),
                             "n_facts": len(fl)}
        else:
            page = [chunks[int(c.split(":")[1])] for c in q["top_ids"]]
            pages.append(len(page))
            message = QUERY_TEMPLATE.format(question=rec["question"])
            for arm in ARMS:
                edited = retrieval_arm_page(arm, page, plan)
                if retrieval_integrity(arm, page, edited, plan):
                    mismatches += 1
                arms[arm] = {"prompt": build_user_prompt(edited, message),
                             "n_facts": len(page_facts(edited))}
        native_prompt = arms["native"]["prompt"]
        questions.append({
            "index": q["index"], "question": rec["question"],
            "truths": rec["truths"], "stratum": rec["stratum"],
            "key": list(rec["key"]) if rec["key"] else None,
            "plan": plan, "arms": arms,
            "identical_to_native": {a: arms[a]["prompt"] == native_prompt
                                    for a in ARMS},
        })
    return {"subset": name, "n_facts": len(facts), "questions": questions,
            "n_page_edit_mismatch": mismatches, "harness": harness,
            "n_chunks_total": len(chunks) if chunks is not None else None,
            "n_chunks_on_page": max(pages) if pages else None,
            "retrieval_complete": (len(chunks) <= max(pages)
                                   if chunks is not None and pages else None),
            "strata_counts": {s: sum(1 for q in questions if q["stratum"] == s)
                              for s in STRATA}}


def budget(plans) -> dict:
    rows, calls, chars = [], 0, 0
    for p in plans:
        prompts, c = set(), 0
        for q in p["questions"]:
            for arm in ARMS:
                if arm == "native_repeat":
                    continue
                t = q["arms"][arm]["prompt"]
                if t not in prompts:
                    prompts.add(t)
                    c += len(t)
        c += sum(len(q["arms"]["native"]["prompt"]) for q in p["questions"])
        n = len(prompts) + len(p["questions"])
        rows.append({"subset": p["subset"], "n_questions": len(p["questions"]),
                     "n_distinct_prompts": len(prompts),
                     "n_aa_repeats": len(p["questions"]), "n_calls": n,
                     "approx_prompt_tokens": c // 4,
                     "n_identical_to_native": {
                         a: sum(1 for q in p["questions"]
                                if q["identical_to_native"][a])
                         for a in EDIT_ARMS}})
        calls += n
        chars += c
    return {"per_subset": rows, "total_calls": calls,
            "approx_total_prompt_tokens": chars // 4}


# ── execution ────────────────────────────────────────────────────────────────
def make_answer_fn(args, cfg):
    if args.smoke_llm:
        return primacy_stub()
    from openai import OpenAI  # noqa: PLC0415 — lazy: no network at import

    client = OpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)

    def answer(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=cfg.llm_model,
            messages=[{"role": "system", "content": SYSTEM_MESSAGE},
                      {"role": "user", "content": prompt}],
            temperature=cfg.llm_temperature, max_tokens=GENERATION_MAX_TOKENS)
        return resp.choices[0].message.content or ""
    return answer


def run_subset(plan, answer_fn) -> dict:
    cache, per_question, n_calls = {}, [], 0
    for q in plan["questions"]:
        row = {"index": q["index"], "stratum": q["stratum"], "key": q["key"],
               "truths": q["truths"], "plan": q["plan"], "arms": {}}
        for arm in ARMS:
            prompt = q["arms"][arm]["prompt"]
            if arm == "native_repeat":
                out = answer_fn(prompt)              # deliberately uncached: A/A
                n_calls += 1
            else:
                if prompt not in cache:
                    cache[prompt] = answer_fn(prompt)
                    n_calls += 1
                out = cache[prompt]
            row["arms"][arm] = {
                "output": out,
                "correct": bool(substring_exact_match(out, q["truths"])),
                "n_facts": q["arms"][arm]["n_facts"],
                "prompt_chars": len(prompt), "prompt_sha": _sha(prompt),
                "identical_to_native": q["identical_to_native"][arm]}
        per_question.append(row)

    flags = {a: [r["arms"][a]["correct"] for r in per_question] for a in ARMS}
    by_stratum = {}
    for s in STRATA:
        idx = [i for i, r in enumerate(per_question) if r["stratum"] == s]
        if not idx:
            continue
        by_stratum[s] = {
            "arms": {a: _acc([flags[a][i] for i in idx]) for a in ARMS},
            "paired_vs_native": {
                a: paired_cells([flags["native"][i] for i in idx],
                                [flags[a][i] for i in idx])
                for a in ARMS if a != "native"}}

    nat_chars = sum(r["arms"]["native"]["prompt_chars"] for r in per_question)
    tokens = {a: {"prompt_chars": sum(r["arms"][a]["prompt_chars"]
                                      for r in per_question)}
              for a in ARMS}
    for a, t in tokens.items():
        t["delta_chars_vs_native"] = t["prompt_chars"] - nat_chars
        t["delta_pct"] = (100.0 * t["delta_chars_vs_native"] / nat_chars
                          if nat_chars else None)
        t["approx_prompt_tokens"] = t["prompt_chars"] // 4

    return {"subset": plan["subset"], "n_facts": plan["n_facts"],
            "strata_counts": plan["strata_counts"],
            "n_page_edit_mismatch": plan["n_page_edit_mismatch"],
            "harness": plan["harness"],
            "n_chunks_total": plan["n_chunks_total"],
            "n_chunks_on_page": plan["n_chunks_on_page"],
            "retrieval_complete": plan["retrieval_complete"],
            "n_llm_calls": n_calls,
            "arms": {a: _acc(flags[a]) for a in ARMS},
            "paired_vs_native": {a: paired_cells(flags["native"], flags[a])
                                 for a in ARMS if a != "native"},
            "aa_floor": paired_cells(flags["native"], flags["native_repeat"]),
            "by_stratum": by_stratum, "tokens": tokens,
            "per_question": per_question}


# ── the headline: detector vs oracle ─────────────────────────────────────────
def load_oracle(subset: str) -> dict | None:
    """The committed oracle-probe result for this subset, whatever it is named."""
    for path in sorted(ORACLE_DIR.glob("stale_suppression_probe*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("smoke_llm"):
            continue
        for res in payload.get("results", []):
            if res["subset"] == subset:
                return {"file": str(path.relative_to(REPO)).replace("\\", "/"),
                        "harness": payload.get("harness", {}), "result": res}
    return None


def _ratio(num, den):
    if den in (None, 0) or num is None:
        return None
    return num / den


def compare_to_oracle(res: dict, oracle: dict | None) -> dict | None:
    """``detector-achieved / oracle-achieved`` per mechanism, on the paired
    McNemar net and on the conflicted-stratum gain over native.

    Both harnesses are identical and the ``native`` arm is a byte-identical
    prompt in both, so the two runs' native arms are compared directly as a
    cross-run A/A check. A drift there would invalidate every ratio below,
    which is why it is reported rather than assumed.
    """
    if oracle is None:
        return None
    o = oracle["result"]
    o_conf = o["by_stratum"].get("conflicted", {}).get("arms", {})
    d_conf = res["by_stratum"].get("conflicted", {}).get("arms", {})
    o_nat = o["arms"]["native"]
    d_nat = res["arms"]["native"]

    rows = {}
    for arm, oarm in ORACLE_COUNTERPART.items():
        d_net = res["paired_vs_native"][arm]["net"]
        o_net = o["paired_vs_native"][oarm]["net"]
        d_gain = (d_conf.get(arm, {}).get("correct", 0)
                  - d_conf.get("native", {}).get("correct", 0))
        o_gain = (o_conf.get(oarm, {}).get("correct", 0)
                  - o_conf.get("native", {}).get("correct", 0))
        rows[arm] = {
            "oracle_arm": oarm,
            "detector_net": d_net, "oracle_net": o_net,
            "net_ratio": _ratio(d_net, o_net),
            "detector_conflicted_correct": d_conf.get(arm, {}).get("correct"),
            "oracle_conflicted_correct": o_conf.get(oarm, {}).get("correct"),
            "detector_conflicted_gain": d_gain, "oracle_conflicted_gain": o_gain,
            "conflicted_gain_ratio": _ratio(d_gain, o_gain),
            "detector_accuracy": res["arms"][arm]["accuracy"],
            "oracle_accuracy": o["arms"][oarm]["accuracy"]}
    o_harness = "whole_context"          # every oracle probe arm is whole-context
    return {
        "source": oracle["file"],
        "oracle_harness": o_harness,
        "harness_match": res.get("harness", "whole_context") == o_harness,
        "harness_caveat": None if res.get("harness", "whole_context") == o_harness else (
            "This run uses the RETRIEVAL-PATH harness; the oracle probe is "
            "whole-context. The ratios below therefore compare across harnesses "
            "and are NOT the detector/oracle ratio of the confirmatory design - "
            "read them as 'how much of the whole-context oracle ceiling survives "
            "being applied to a rank-ordered multi-block page'."),
        "same_harness": {
            "llm_model": oracle["harness"].get("llm_model"),
            "llm_base_url": oracle["harness"].get("llm_base_url"),
            "prompt_shape": oracle["harness"].get("prompt_shape")},
        "native_cross_run": {
            "detector_native": d_nat, "oracle_native": o_nat,
            "identical": d_nat["correct"] == o_nat["correct"]},
        "by_mechanism": rows}


# ── reporting ────────────────────────────────────────────────────────────────
def _fmt(x, nd: int = 3) -> str:
    return "-" if x is None else f"{x:.{nd}f}"


def format_detection(cells, chosen) -> str:
    lines = ["", "=" * 100,
             " DETECTOR OPERATING-POINT SELECTION (detection quality only - "
             "no LLM, no gold)", "=" * 100,
             f"{'cos':>5}{'r_min':>8}{'amb':>6}{'nli':>6}{'filt':>6}"
             f"{'prec':>8}{'rec_pool':>10}{'rec_page':>10}{'sup':>7}"
             f"{'harm':>6}{'q_rec':>8}{'cover':>7}"]
    top = sorted([c for c in cells if c["pair_filter"]],
                 key=lambda c: -(c["metrics"]["pair_recall_pool"] or 0))[:12]
    for c in top:
        m = c["metrics"]
        lines.append(
            f"{c['cos_pair']:>5}{c['r_min_label']:>8}{c['ambiguity_mode']:>6}"
            f"{c['nli_contradiction']:>6}{str(c['pair_filter']):>6}"
            f"{_fmt(m['pair_precision']):>8}{_fmt(m['pair_recall_pool']):>10}"
            f"{_fmt(m['pair_recall_page']):>10}"
            f"{m['n_suppressed']:>7}{m['n_suppressed_harmful']:>6}"
            f"{_fmt(m['question_recall_conflicted']):>8}"
            f"{_fmt(m['coverage']):>7}")
    if chosen:
        m = chosen["metrics"]
        lines += ["",
                  f" CHOSEN: cos_pair={chosen['cos_pair']} "
                  f"r_min={chosen['r_min_label']} "
                  f"ambiguity={chosen['ambiguity_mode']} "
                  f"nli={chosen['nli_contradiction']} "
                  f"pair_filter={chosen['pair_filter']}",
                  f"   pair precision {m['pair_precision']:.4f}  "
                  f"recall(pool) {m['pair_recall_pool']:.4f}  "
                  f"recall(page) {m['pair_recall_page']:.4f}",
                  f"   suppressed {m['n_suppressed']} facts "
                  f"({m['n_suppressed_superseded']} superseded, "
                  f"{m['n_suppressed_same_value']} same-value duplicates, "
                  f"{m['n_suppressed_harmful']} harmful)",
                  f"   conflicted-question recall "
                  f"{m['n_conflicted_hit']}/{m['n_conflicted']} "
                  f"(gold-valued fact cut in {m['n_conflicted_gold_cut']})",
                  f"   unique-stratum questions touched "
                  f"{m['n_unique_touched']}/{m['n_unique']}"]
    else:
        lines.append("\n NO cell satisfies the pre-registered requirements. "
                     "REPORT AND STOP.")
    return "\n".join(lines)


def format_run(results, comparisons) -> str:
    lines = []
    for res in results:
        cmp_ = comparisons.get(res["subset"])
        cov = ""
        if res.get("n_chunks_total") is not None:
            cov = (f", {res['n_chunks_on_page']}/{res['n_chunks_total']} chunks "
                   f"on page{'' if res['retrieval_complete'] else ' - INCOMPLETE'}")
        lines += ["", "=" * 100,
                  f" {res['subset']}  [{res.get('harness', 'whole_context')}]  "
                  f"({res['n_facts']} facts, {res['strata_counts']}{cov})", "=" * 100,
                  f"{'arm':<24}{'overall':>18}{'unique':>18}{'conflicted':>18}"
                  f"{'b/c':>10}{'tok d%':>9}"]
        for arm in ARMS:
            cells = ""
            if arm != "native":
                pc = res["paired_vs_native"][arm]
                cells = f"{pc['b_native_only']}/{pc['c_arm_only']}"
            row = f"{arm:<24}"
            for scope in ("overall", "unique", "conflicted"):
                a = (res["arms"][arm] if scope == "overall"
                     else (res["by_stratum"].get(scope) or {}).get("arms", {}).get(arm))
                row += ("{:>18}".format("-") if not a or a["accuracy"] is None
                        else "{:>18}".format("{}/{} {:.3f}".format(
                            a["correct"], a["n"], a["accuracy"])))
            dp = res["tokens"][arm]["delta_pct"]
            lines.append(row + f"{cells:>10}" +
                         ("{:>9}".format("-") if dp is None else f"{dp:>+9.2f}"))
        aa = res["aa_floor"]
        lines.append(f"  A/A floor: {aa['b_native_only']}/{aa['c_arm_only']} "
                     f"discordant of {aa['n']} (p={aa['p_exact']:.3f})")
        lines.append(f"  page-edit mismatches vs the shipped contract: "
                     f"{res['n_page_edit_mismatch']} (must be 0)")
        for arm in ARMS:
            if arm in ("native", "native_repeat"):
                continue
            pc = res["paired_vs_native"][arm]
            lines.append(f"  {arm:<22} net {pc['net']:+d}  "
                         f"(b={pc['b_native_only']} c={pc['c_arm_only']}, "
                         f"exact p={pc['p_exact']:.4g})")
        if cmp_:
            lines += ["", "  DETECTOR / ORACLE", "  " + "-" * 92,
                      f"  {'mechanism':<24}{'oracle arm':<18}"
                      f"{'det net':>9}{'orc net':>9}{'ratio':>8}"
                      f"{'det conf':>10}{'orc conf':>10}{'gain ratio':>12}"]
            for arm, r in cmp_["by_mechanism"].items():
                nr = _fmt(r["net_ratio"])
                gr = _fmt(r["conflicted_gain_ratio"])
                lines.append(
                    f"  {arm:<24}{r['oracle_arm']:<18}"
                    f"{r['detector_net']:>+9d}{r['oracle_net']:>+9d}{nr:>8}"
                    f"{str(r['detector_conflicted_correct']):>10}"
                    f"{str(r['oracle_conflicted_correct']):>10}{gr:>12}")
            nx = cmp_["native_cross_run"]
            lines.append(f"  cross-run native check: this run "
                         f"{nx['detector_native']['correct']}/"
                         f"{nx['detector_native']['n']}, oracle run "
                         f"{nx['oracle_native']['correct']}/"
                         f"{nx['oracle_native']['n']} "
                         f"({'identical' if nx['identical'] else 'DRIFTED'})")
    return "\n".join(lines)


# ── loading ──────────────────────────────────────────────────────────────────
def subset_of(item: dict) -> str:
    return item["metadata"]["qa_pair_ids"][0].rsplit("_no", 1)[0] \
        .replace("factconsolidation_", "")


def load_context(cfg, subsets, args) -> dict:
    """Dataset items, prepasses, ground-truth tables and gate-ready records.

    The prepass NLI-config stamp is checked here rather than trusted: a table
    scored by a different engine, replayed into this gate, would produce numbers
    that look valid and are not (the T12 lesson). An unstamped prepass predates
    the stamp and is accepted only behind ``--allow-unstamped-prepass``, with
    the fact recorded in every artifact this run writes.
    """
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = {subset_of(i): i for i in data if subset_of(i) in subsets}
    missing = [s for s in subsets if s not in items]
    if missing:
        raise SystemExit(f" REFUSED: no dataset item for {missing}")

    prepasses, unstamped = {}, []
    for s in subsets:
        p = cfg.out_dir / f"stage1_prepass_{s}.json"
        if not p.exists():
            raise SystemExit(
                f" REFUSED: {p} missing. Run\n"
                f"   python hnav/stage1/calibrate_read_policy.py --prepass "
                f"--subsets {s}\n first (it needs the embedder and the NLI).")
        pp = json.loads(p.read_text(encoding="utf-8"))
        stamp = pp.get("nli_config")
        if stamp is None:
            unstamped.append(s)
            if not args.allow_unstamped_prepass:
                raise SystemExit(
                    f" REFUSED: {p.name} predates NLI-config stamping (T12), so "
                    "the engine that\n produced its scores cannot be verified. "
                    "Re-run --prepass, or pass\n --allow-unstamped-prepass to "
                    "accept it (the artifact records that you did).")
        elif stamp.get("stub"):
            raise SystemExit(f" REFUSED: {p.name} was scored with a STUB NLI.")
        prepasses[s] = pp

    tables = {s: fact_table(items[s]) for s in subsets}

    records, namespaces, cos_err = {}, set(), 0.0
    for s in subsets:
        table = tables[s]
        order = sorted(table["by_id"], key=lambda f: table["by_id"][f][0])
        texts = [table["by_id"][f][1] for f in order]
        vecs, key, err = load_fact_vectors(cfg, order, texts, [prepasses[s]])
        records[s] = build_records(order, texts, table, vecs)
        namespaces.add(key)
        cos_err = max(cos_err, err)

    return {"items": items, "prepasses": prepasses, "tables": tables,
            "records": records, "unstamped": unstamped,
            "embed_namespaces": sorted(namespaces), "max_cosine_error": cos_err}


def page_fact_ids(prepass, table) -> list[str]:
    """Every fact the retrieved page carries, from the prepass's own
    ``fact_chunk`` map. This is the denominator for ``pair_recall_page`` — what
    a detector with no pool cap could in principle have seen."""
    tops = {c for q in prepass["questions"] for c in q["top_ids"]}
    return [f for f, c in prepass["fact_chunk"].items()
            if c in tops and f in table["by_id"]]


# ── selection driver ─────────────────────────────────────────────────────────
def measure_grid(ctx, subsets, cells) -> None:
    """Fill ``cell["metrics"]`` (pooled over the split) and ``cell["by_subset"]``."""
    for c in cells:
        c["metrics"] = blank_metrics()
        c["by_subset"] = {s: blank_metrics() for s in subsets}
    for s in subsets:
        pp, table, recs = ctx["prepasses"][s], ctx["tables"][s], ctx["records"][s]
        strata = {r["index"]: r for r in classify_questions(ctx["items"][s])}
        page_gt = count_gt_pairs(page_fact_ids(pp, table), table["by_id"])
        decisions = decide_all(pp, recs, cells, ReplayNLI(pp["nli_table"]))
        for q in pp["questions"]:
            decs = decisions[q["index"]]
            pool = [f for f in q["pool"] if f in table["by_id"]]
            for ci, c in enumerate(cells):
                score_decision(c["metrics"], decs[ci], table,
                               strata[q["index"]], pool, page_gt)
                score_decision(c["by_subset"][s], decs[ci], table,
                               strata[q["index"]], pool, page_gt)
    for c in cells:
        c["metrics"] = finish_metrics(c["metrics"])
        c["by_subset"] = {s: finish_metrics(m) for s, m in c["by_subset"].items()}


AMBIGUITY_NOTE = (
    "ambiguity_mode='none' disables the frozen Stage-0 nmargin/H_z "
    "precondition. Declared, not incidental: those two signals are the only "
    "gate input computed from CHUNK embeddings, which were truncated at 512 of "
    "~4096 tokens (T12) and are not yet re-fit; they are also the dominant "
    "recall bottleneck (question-level recall collapses from 0.97 to 0.16 with "
    "the screen on); and the volume-limiting role they played is now carried by "
    "the identity screen plus bidirectional NLI at the measured precision "
    "recorded here. A campaign run after the embeddings are re-fit must "
    "revisit this.")


def freeze(chosen, ctx, subsets) -> Path:
    art = {
        "task": "T13",
        "thresholds": {
            "cos_pair": chosen["cos_pair"], "r_min": chosen["r_min"],
            "nmargin": _rg.NMARGIN_CAL, "H_z": _rg.H_Z_CAL,
            "ambiguity_mode": chosen["ambiguity_mode"],
            "nli_contradiction": chosen["nli_contradiction"]},
        "r_min_label": chosen["r_min_label"],
        "pair_filter": chosen["pair_filter"],
        "mechanisms": ["suppress", "demote_late"],
        "selection_rule": SELECTION_RULE,
        "metrics": chosen["metrics"],
        "by_subset": chosen["by_subset"],
        "ambiguity_note": AMBIGUITY_NOTE if chosen["ambiguity_mode"] == "none"
                          else None,
        "provenance": {
            "generated_at_utc":
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_head": _git_head(),
            "fit_subsets": sorted(subsets),
            "confirmatory_refused": list(CONFIRMATORY),
            "prepass": {s: f"hnav/_out/stage1_prepass_{s}.json" for s in subsets},
            "prepass_unstamped_nli_config": ctx["unstamped"],
            "embed_cache_namespace": ctx["embed_namespaces"],
            "max_pair_cosine_error_vs_prepass": ctx["max_cosine_error"],
            "grid": {"cos_pair": list(COS_GRID),
                     "r_min": list(R_MIN_GRID_LABELS),
                     "ambiguity_mode": list(AMB_GRID),
                     "nli_contradiction": list(NLI_GRID),
                     "pair_filter": list(FILTER_GRID)},
        },
    }
    OPERATING_POINT.parent.mkdir(parents=True, exist_ok=True)
    OPERATING_POINT.write_text(json.dumps(art, indent=1, default=str),
                               encoding="utf-8")
    return OPERATING_POINT


def frozen_cell() -> dict:
    """The committed operating point, as a grid cell. Refuses to invent one."""
    if not OPERATING_POINT.exists():
        raise SystemExit(
            f" REFUSED: {_rel(OPERATING_POINT)} does not exist. Run\n"
            "   python hnav/stage1/detector_gap.py --select\n"
            " first: the operating point is frozen from DETECTION quality, "
            "before anything is graded.")
    art = json.loads(OPERATING_POINT.read_text(encoding="utf-8"))
    thr = art["thresholds"]
    return {"cos_pair": thr["cos_pair"], "r_min": thr["r_min"],
            "r_min_label": art.get("r_min_label", "custom"),
            "ambiguity_mode": thr["ambiguity_mode"],
            "nli_contradiction": thr["nli_contradiction"],
            "pair_filter": art["pair_filter"], "artifact": art}


def _rel(path: Path) -> str:
    """Repo-relative when possible; the absolute path otherwise, so a message
    about a missing file cannot itself raise."""
    try:
        return str(Path(path).relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path)


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--subsets", nargs="*", default=list(CALIBRATION))
    ap.add_argument("--select", action="store_true",
                    help="score the grid on DETECTION quality only and freeze "
                         "the operating point. No LLM, no grading.")
    ap.add_argument("--dry-run", action="store_true",
                    help="build every arm, print the exact call budget, send nothing")
    ap.add_argument("--smoke-llm", action="store_true",
                    help="SMOKE ONLY: the probe's deterministic primacy stub "
                         "instead of the answer model. Writes *_SMOKE.json; the "
                         "numbers are MEANINGLESS as evidence about any model.")
    ap.add_argument("--harness", choices=list(HARNESSES),
                    default="whole_context",
                    help="whole_context reproduces the oracle probe exactly; "
                         "retrieval puts the benchmark's own top-k chunks on the "
                         "page in rank order and edits them through the shipped "
                         "page contract (pre-registration v2 section 10)")
    ap.add_argument("--max-questions", type=int, default=None)
    ap.add_argument("--allow-unstamped-prepass", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = _config.get_config()
    cfg.require_not_live()

    bad = [s for s in args.subsets if s not in CALIBRATION]
    if bad:
        print(f" REFUSED: {bad} is outside the calibration split {CALIBRATION}.\n"
              f" {CONFIRMATORY} is the confirmatory arena; measuring or tuning "
              "there would\n void the campaign (STAGE1_PLAN.md). Nothing was "
              "computed.")
        return 2
    subsets = list(dict.fromkeys(args.subsets))

    ctx = load_context(cfg, subsets, args)
    print(f" embedding cache namespace(s): {ctx['embed_namespaces']}  "
          f"(max pair-cosine error vs prepass {ctx['max_cosine_error']:.2e})")
    if ctx["unstamped"]:
        print(f" NOTE: prepass for {ctx['unstamped']} predates NLI-config "
              "stamping; accepted under --allow-unstamped-prepass.")

    if args.select:
        if sorted(subsets) != sorted(CALIBRATION):
            print(f" NOTE: fitting on {subsets}, not the full calibration split "
                  f"{list(CALIBRATION)}. Recorded in the artifact.")
        cells = grid_cells()
        measure_grid(ctx, subsets, cells)
        chosen = select(cells)
        print(format_detection(cells, chosen))
        (cfg.out_dir / "detector_gap_selection.json").write_text(
            json.dumps({"cells": cells, "chosen": chosen,
                        "selection_rule": SELECTION_RULE,
                        "fit_subsets": subsets}, indent=1, default=str),
            encoding="utf-8")
        if chosen is None:
            return 3
        print(f"\n froze operating point -> "
              f"{_rel(freeze(chosen, ctx, subsets))}")
        return 0

    cell = frozen_cell()
    print(f" harness: {args.harness}")
    print(f" operating point: cos_pair={cell['cos_pair']} "
          f"r_min={cell['r_min_label']} ambiguity={cell['ambiguity_mode']} "
          f"nli={cell['nli_contradiction']} pair_filter={cell['pair_filter']}")

    plans = []
    for s in subsets:
        pp, table, recs = ctx["prepasses"][s], ctx["tables"][s], ctx["records"][s]
        decisions = decide_all(pp, recs, [cell], ReplayNLI(pp["nli_table"]))
        plans.append(plan_subset(ctx["items"][s], s, pp, decisions, 0, table,
                                 args.max_questions, harness=args.harness))

    bud = budget(plans)
    print("=" * 100)
    print(" DETECTOR-GAP RUN - call budget (exact, pre-flight)")
    print("=" * 100)
    for row in bud["per_subset"]:
        print(f"  {row['subset']:<9} questions={row['n_questions']:<5}"
              f" distinct prompts={row['n_distinct_prompts']:<5}"
              f" A/A repeats={row['n_aa_repeats']:<5}"
              f" calls={row['n_calls']:<6} "
              f"~{row['approx_prompt_tokens']:,} prompt tokens")
        print(f"             arms byte-identical to native: "
              f"{row['n_identical_to_native']}")
    print(f"  TOTAL {bud['total_calls']} calls, "
          f"~{bud['approx_total_prompt_tokens']:,} prompt tokens "
          f"(max_tokens={GENERATION_MAX_TOKENS} out)")
    print(f"  server: {'STUB (no endpoint)' if args.smoke_llm else cfg.llm_base_url}"
          f"   model: {'stub' if args.smoke_llm else cfg.llm_model}"
          f"   mode: {cfg.mode}")

    bad_edit = [p["subset"] for p in plans if p["n_page_edit_mismatch"]]
    if bad_edit:
        print(f"\n REFUSED: the probe-style arm and the shipped page_edit path "
              f"disagree on {bad_edit}.\n The measurement would not be measuring "
              "the mechanism that ships. Nothing was sent.")
        return 4

    if args.dry_run:
        print("\n --dry-run: nothing sent.")
        return 0

    answer_fn = make_answer_fn(args, cfg)
    if args.smoke_llm:
        print("\n *** SMOKE RUN - primacy-anchored stub, not a model. ***")
    results = [run_subset(p, answer_fn) for p in plans]
    comparisons = {}
    for res in results:
        c = compare_to_oracle(res, load_oracle(res["subset"]))
        if c:
            comparisons[res["subset"]] = c
    print(format_run(results, comparisons))

    payload = {
        "generated_at_utc":
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git_head(), "mode": cfg.mode,
        "smoke_llm": bool(args.smoke_llm),
        "harness": args.harness,
        "preregistration": "stage0_results/stage1_preregistration_v2.md",
        "operating_point": cell["artifact"],
        "harness": {
            "llm_model": None if args.smoke_llm else cfg.llm_model,
            "llm_base_url": None if args.smoke_llm else cfg.llm_base_url,
            "temperature": cfg.llm_temperature,
            "max_tokens": GENERATION_MAX_TOKENS,
            "system_message": SYSTEM_MESSAGE,
            "prompt_shape":
                "RAGSystem: 'Memory 1:\\n<whole context>\\n' + templated query",
            "prompt_source":
                "hnav.stage1.stale_suppression_probe (imported verbatim)",
            "grader": "hnav.labeling.counterfactual.substring_exact_match",
            "identical_to_oracle_probe": (
                "same prompt shape, same system message, same grader, same "
                "frozen :8003 substrate - the headline is a RATIO against the "
                "oracle arms and a ratio taken across harnesses is meaningless"),
        },
        "arms": {
            "native": "untouched context",
            "native_repeat":
                "same prompt, independent second call (A/A floor)",
            "detector_suppress":
                "ReadFactPolicy('suppress'): drop every stale member of every "
                "verified group; serials NOT renumbered",
            "detector_demote_late":
                "ReadFactPolicy('demote_late'): every verified group's LATEST "
                "carrier moves to the END, ascending serial order",
            "detector_anti":
                "measurement-only mirror: the same LATEST carriers move to the "
                "FRONT",
        },
        "detector_inputs": {
            "prepass": {s: f"hnav/_out/stage1_prepass_{s}.json" for s in subsets},
            "prepass_unstamped_nli_config": ctx["unstamped"],
            "embed_cache_namespace": ctx["embed_namespaces"],
            "max_pair_cosine_error_vs_prepass": ctx["max_cosine_error"],
            "gate": "hnav.core.read_gate.ReadGate (real); NLI replayed from the "
                    "prepass via calibrate_read_policy.ReplayNLI",
            "policy": "hnav.core.read_policy.ReadFactPolicy",
            "page_contract_check":
                "each suppress/demote arm re-derived through "
                "mab_adapter.page_edit and asserted byte-identical",
        },
        "split": {"calibration": list(CALIBRATION),
                  "refused": list(CONFIRMATORY)},
        "budget": bud,
        "results": results,
        "detector_vs_oracle": comparisons,
    }
    tag = "" if args.harness == "whole_context" else f"_{args.harness}"
    out = Path(args.out) if args.out else (
        cfg.out_dir / (f"detector_gap{tag}_SMOKE.json" if args.smoke_llm
                       else f"detector_gap{tag}.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"\n wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
