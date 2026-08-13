"""``H_raw`` is logged and never decided on.  [T5, hard rule 6]

Three independent checks, because one of them alone is easy to route around:

1. the policy-facing accessor does not contain ``H_raw`` at all;
2. no ``Decision.reasons`` produced by a real shadow pass contains it, at any
   nesting depth;
3. an AST scan of any policy module that exists finds no reference to it. Stage 0
   ships no policy modules — that is itself asserted, since writing them before
   the T8 gate would be the actual violation.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from hnav import config as _config
from hnav.adapters import mab_adapter as mab
from hnav.core.retrieval_signals import POLICY_FORBIDDEN, RetrievalSignals
from hnav.core.types import RetrievalView

REPO = Path(__file__).resolve().parents[2]
SHADOW = _config.HNavConfig(mode=_config.MODE_SHADOW)

CHUNK = """Here is a list of facts:
0. Thomas Kyd was born in the city of London.
1. The chairperson of Fatah is Mahmoud Abbas.
2. Thomas Kyd was born in the city of Madrid.
"""


def test_policy_view_excludes_raw_entropy():
    sig = RetrievalSignals(top_m=4).compute(
        RetrievalView(query="q", query_vector=None, ids=list("abcd"),
                      scores=np.array([90.0, 80.0, 70.0, 60.0]), top_k=3))
    assert "H_raw" in sig.to_dict(), "H_raw must still be LOGGED"
    for name in POLICY_FORBIDDEN:
        assert name not in sig.for_policy(), f"{name} leaked into the policy view"


def _walk_strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _walk_strings(v)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def test_no_decision_reasons_mention_raw_entropy(embedder):
    adapter = mab.MABAdapter(cfg=SHADOW, embedder=embedder,
                             signals=RetrievalSignals(top_m=50, k=3))
    adapter.before_memorize(CHUNK, context_id=0)
    decision = adapter.on_retrieve("Where was Thomas Kyd born?", [CHUNK], [88.0], top_k=1)

    reasons = list(_walk_strings(decision.reasons))
    for name in POLICY_FORBIDDEN:
        assert not any(name in r for r in reasons), f"{name} reached Decision.reasons"


def test_stage0_ships_no_policy_modules():
    """Write/read policies are live-intervention code, gated behind T8."""
    present = [p.name for p in (REPO / "hnav/core").glob("*policy*.py")]
    assert present == [], (
        f"policy modules exist before the T8 gate: {present}. "
        "Stage 0 must end at the report, not at an intervention."
    )


def test_any_future_policy_module_is_scanned():
    """Guard for the day a policy is written: it must not read H_raw.

    Kept live rather than added later, so the constraint outlives whoever
    remembers it.
    """
    for path in sorted((REPO / "hnav/core").glob("*policy*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                name = node.value
            if name and any(f in str(name) for f in POLICY_FORBIDDEN):
                raise AssertionError(f"{path.name}:{node.lineno} references {name!r}")
