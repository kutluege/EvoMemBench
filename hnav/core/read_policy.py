"""Read-path rerank policy — Stage 1, Faz B.  [T11]

The ONLY intervention H-Nav ships. Protocol trail: ``KAPI_KARARI.md`` §3/§6
(instruments GO, write_policy NO_GO forever, read_policy CONDITIONAL) →
user decision 2026-08-15 (``STAGE1_PLAN.md`` §0: read-path RERANK ONLY, no
filter/inject/merge) → this module. ``test_no_raw_entropy_in_policy.py``
permits exactly this file under ``hnav/core/*policy*.py`` and AST-scans it
for the forbidden raw-score entropy.

What it does, and all it does: consume a :class:`~hnav.core.read_gate.ReadGate`
decision and produce a **token-neutral permutation** of the retrieved page —
each verified conflict group's LATEST carrier is promoted immediately above
that group's highest-ranked stale rival. Same ids, same count, order only;
:func:`rerank_order` raises rather than return anything that is not a
permutation of its input.

Unit mapping. The gate works on whatever candidates the adapter gave it (facts,
on the primary arena); the page being reranked may be a coarser unit (chunks).
``id_map`` translates gate-member ids to page ids and is supplied by the
adapter — the policy stays benchmark-agnostic. Unmappable members, groups
without a LATEST (``latest_id=None``), and groups whose latest and stale
members share one page unit (an intra-unit conflict — nothing to reorder) are
all skipped, never guessed at.

Determinism. Groups are applied in ascending order of the ORIGINAL position of
their first stale rival (ties: original position of the latest carrier, then
its id), each as a single pop-and-insert on the working list. The output is a
pure function of ``(ordering, decision, id_map)``.

Ambiguity signals reach this policy only through the gate, which consumes them
via ``RetrievalSignalSet.for_policy()`` — the z-scored ``H_z`` family, never
the raw-score entropy (hard rule 6).
"""
from __future__ import annotations

from typing import Callable, Sequence

from .read_gate import GateDecision, GateThresholds, ReadGate
from .types import Decision

__all__ = ["rerank_order", "ReadRerankPolicy", "stage1_thresholds"]


def stage1_thresholds() -> GateThresholds:
    """The gate operating point the live read path runs at.

    Until the Faz B coverage-balanced calibration is frozen (sh_6k + sh_32k
    ONLY, never sh_64k/sh_262k), this returns the Faz A defaults — the frozen
    Stage-0 values whose provenance is documented in ``read_gate.py`` and
    pinned by ``test_threshold_provenance.py``. The calibration freeze commit
    replaces this body with the chosen operating point and extends the
    provenance test to ``stage0_results/stage1_operating_point.json``.
    """
    return GateThresholds()


def rerank_order(ordering: Sequence[str], decision: GateDecision,
                 id_map: Callable[[str], str | None] | None = None) -> list[str]:
    """Return the reranked page — a permutation of ``ordering``, or the
    identical list when the decision moves nothing.

    ``ordering``  page-unit ids, ranked (the benchmark's top-k page).
    ``decision``  a :class:`GateDecision`; only ``groups`` is consulted.
    ``id_map``    gate-member id -> page-unit id (or ``None`` when a member
                  has no page unit). Defaults to identity.
    """
    ids = list(ordering)
    if len(set(ids)) != len(ids):
        raise ValueError("ordering contains duplicate ids; refusing to rerank")
    if not decision.groups:
        return ids

    mapper = id_map if id_map is not None else (lambda x: x)
    pos0 = {u: i for i, u in enumerate(ids)}

    # Plan every promotion against the ORIGINAL positions, then apply in a
    # canonical order — the docstring's determinism contract.
    plans: list[tuple[int, int, str, str]] = []
    for g in decision.groups:
        if g.latest_id is None:
            continue                    # the gate refused to name a LATEST
        latest_u = mapper(g.latest_id)
        if latest_u is None or latest_u not in pos0:
            continue                    # not on the page; nothing to promote
        stale_us = sorted(
            {u for u in (mapper(s) for s in g.stale_ids)
             if u is not None and u in pos0 and u != latest_u},
            key=pos0.__getitem__)
        if not stale_us:
            continue                    # intra-unit conflict or off-page rivals
        first_stale = stale_us[0]
        if pos0[latest_u] <= pos0[first_stale]:
            continue                    # already above every rival
        plans.append((pos0[first_stale], pos0[latest_u], latest_u, first_stale))

    out = ids[:]
    for _, _, latest_u, first_stale in sorted(plans):
        cur, tgt = out.index(latest_u), out.index(first_stale)
        if cur > tgt:                   # may have been promoted past already
            out.pop(cur)
            out.insert(tgt, latest_u)

    if sorted(out) != sorted(ids):      # defence in depth: token neutrality
        raise AssertionError("rerank produced a non-permutation — refusing")
    return out


# Gate counters copied into Decision.reasons — one auditable place.
_GATE_COUNTERS = ("ambiguous", "n_candidates", "n_pairs_screened", "n_pairs_cos",
                  "n_pairs_filter_rejected", "n_groups_cos", "n_groups_geometric",
                  "n_pairs_nli", "n_pairs_verified")


class ReadRerankPolicy:
    """Gate → rerank, packaged as a :class:`~hnav.core.types.Decision`.

    ``decide`` mutates nothing: not the candidates, not the ordering, not the
    store. ``Decision.shadow`` is returned ``True``; the ADAPTER flips it to
    ``False`` only under ``HNAV_MODE=live`` — the same defence-in-depth seam
    Stage 0 used, so a stray policy object can never act by itself.
    """

    def __init__(self, gate: ReadGate) -> None:
        self.gate = gate

    def decide(self, candidates, ordering: Sequence[str],
               signal_view=None,
               latest_key: Callable | None = None,
               id_map: Callable[[str], str | None] | None = None) -> Decision:
        gd = self.gate.decide(candidates, signal_view, latest_key=latest_key)
        new_order = rerank_order(ordering, gd, id_map=id_map)
        changed = new_order != list(ordering)
        reasons = {
            "gate": {k: getattr(gd, k) for k in _GATE_COUNTERS},
            "groups": [g.to_dict() for g in gd.groups],
            "thresholds": gd.reasons.get("thresholds"),
            "ambiguity": {k: v for k, v in gd.reasons.items() if k != "thresholds"},
            "n_positions_changed": sum(1 for a, b in zip(new_order, ordering) if a != b),
        }
        return Decision(
            action="RERANK" if changed else "PASS",
            payload={"order": new_order} if changed else None,
            reasons=reasons,
            shadow=True,
        )
