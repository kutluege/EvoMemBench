"""CL-bench adapter — CrossEp-Know, the SECONDARY arena.  [T4]

``HNavMemoryWrapper`` wraps any ``cl_bench_memory`` backend behind the same
two-method ``Memory`` ABC (``retrieve`` / ``extract``). In shadow mode it
**delegates verbatim**: both methods return the inner backend's own return
value, the same objects, with no re-wrapping, so the caller cannot observe the
wrapper's presence.

Three things this arena needs that the primary one does not:

* there are no templates and no serial numbers, so ``Candidate.version`` is a
  monotone write counter and there is no key-based conflict index;
* the store is model-generated, so write-side effects can only ever be reported
  as *associational* — true counterfactual replay is unaffordable (plan §7.4);
* samples are clustered by ``context_id`` (ICC 0.346, design effect 3.20,
  effective N ≈ 276), which is recorded in every audit record so the analysis
  can cluster correctly.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav import config as _config  # noqa: E402
from hnav.core.audit import AuditLogger  # noqa: E402
from hnav.core.types import Candidate, Decision, MemoryRecord, StoreView  # noqa: E402

__all__ = ["CLBenchAdapter", "HNavMemoryWrapper", "wrap_memory", "result_annotation"]


class CLBenchAdapter:
    """Signal computation for CrossEp-Know. Holds no benchmark objects."""

    def __init__(self, cfg=None, embedder=None, replica=None,
                 audit: AuditLogger | None = None, signals=None, geometry=None,
                 diff=None) -> None:
        self.cfg = cfg or _config.get_config()
        self.cfg.require_not_live()
        self.mode = self.cfg.mode
        self.embedder = embedder
        self.replica = replica
        self.audit = audit
        self.signals = signals
        self.geometry = geometry
        self.diff = diff
        self.write_counter = 0
        self.n_write_decisions = 0
        self.n_read_decisions = 0

    # ── store views built from the backend's own persisted state ─────────────
    def store_view(self, memory: Any) -> StoreView:
        """Build a StoreView from a live backend.

        ``Qwen3EmbeddingMemory`` keeps ``memory_bank`` (chunk entries) and
        ``embeddings`` (L2-normalized, same order) in lockstep and persists both
        to ``<memory_dir>/embeddings.jsonl``, so the view is exact and free —
        no re-embedding.
        """
        bank = getattr(memory, "memory_bank", None) or []
        vecs = getattr(memory, "embeddings", None) or []
        records = []
        for i, entry in enumerate(bank):
            vec = np.asarray(vecs[i], dtype=np.float32) if i < len(vecs) else None
            records.append(MemoryRecord(
                id=f"{entry.get('task_id', i)}_chunk{entry.get('chunk_index', i)}",
                text=entry.get("chunk_text", ""),
                vector=vec,
                version=i,
                metadata={"task_id": entry.get("task_id"),
                          "chunk_index": entry.get("chunk_index"),
                          "context_category": entry.get("context_category"),
                          "sub_category": entry.get("sub_category")},
            ))
        return StoreView.from_records(records)

    def to_candidate(self, content: str, **kwargs) -> Candidate:
        self.write_counter += 1
        vec = None
        if self.embedder is not None:
            vec = self.embedder.encode([content])[0]
        return Candidate(
            id=f"{kwargs.get('task_id', 'task')}_w{self.write_counter}",
            text=content, vector=vec, op="ADD", version=self.write_counter,
            metadata={k: v for k, v in kwargs.items() if k != "content"},
        )

    # ── decisions (shadow: always PASS) ──────────────────────────────────────
    def on_extract(self, cand: Candidate, store: StoreView) -> Decision:
        self.n_write_decisions += 1
        decision = Decision(action="PASS", shadow=True,
                            reasons={"native_action": "ADD"})
        if self.audit is not None:
            self.audit.log_write(cand, geometry=None, diff=None,
                                 retrieval_effect=None, decision=decision,
                                 native_action="ADD", store_size=len(store),
                                 context_id=cand.metadata.get("context_category"))
        return decision

    def on_retrieve(self, query: str, store: StoreView,
                    native_text: str = "") -> Decision:
        self.n_read_decisions += 1
        decision = Decision(action="PASS", shadow=True)
        if self.replica is None or len(store) == 0:
            return decision
        view = self.replica.rank(store, query)
        sig = self.signals.compute(view) if self.signals is not None else None
        decision.reasons["n_ranked"] = len(view.ids)
        if self.audit is not None:
            self.audit.log_read(view, decision, signals=sig, store_size=len(store),
                                native_chars=len(native_text))
        return decision

    def annotation(self) -> dict:
        """The additive ``"hnav"`` field for the per-sample result record."""
        return {"mode": self.mode, "run_id": self.cfg.run_id,
                "n_read_decisions": self.n_read_decisions,
                "n_write_decisions": self.n_write_decisions,
                "action": "PASS"}


class HNavMemoryWrapper:
    """Wraps a ``cl_bench_memory`` backend. Shadow mode delegates verbatim.

    Not declared as a subclass of ``Memory``: importing the benchmark ABC from
    ``hnav/`` would invert the dependency the architecture depends on. Duck
    typing is sufficient — ``build_memory``'s callers only ever call
    ``retrieve`` and ``extract`` — and attribute access falls through to the
    inner backend, so ``memory.memory_bank`` and friends keep working.
    """

    def __init__(self, inner: Any, adapter: CLBenchAdapter | None = None,
                 mode: str = _config.MODE_SHADOW) -> None:
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "_adapter", adapter)
        object.__setattr__(self, "_mode", mode)

    # ── Memory interface ─────────────────────────────────────────────────────
    def retrieve(self, query: str) -> tuple:
        result = self._inner.retrieve(query)
        if self._mode == _config.MODE_SHADOW and self._adapter is not None:
            try:
                text = result[0] if isinstance(result, tuple) and result else ""
                self._adapter.on_retrieve(query, self._adapter.store_view(self._inner),
                                          native_text=text)
            except Exception:  # noqa: BLE001 — instrumentation must never break a run
                pass
        return result   # the inner backend's own object, unchanged

    def extract(self, content: str, **kwargs) -> dict:
        if self._mode == _config.MODE_SHADOW and self._adapter is not None:
            try:
                store = self._adapter.store_view(self._inner)
                cand = self._adapter.to_candidate(content, **kwargs)
                decision = self._adapter.on_extract(cand, store)
                assert decision.shadow, "shadow mode produced an actionable decision"
            except AssertionError:
                raise
            except Exception:  # noqa: BLE001
                pass
        return self._inner.extract(content, **kwargs)

    # ── transparency ─────────────────────────────────────────────────────────
    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_inner"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._inner, name, value)

    def __repr__(self) -> str:
        return f"HNavMemoryWrapper({self._inner!r}, mode={self._mode})"


_ADAPTER: CLBenchAdapter | None = None


def get_adapter(**kw) -> CLBenchAdapter | None:
    global _ADAPTER
    try:
        cfg = _config.get_config()
        if cfg.mode == _config.MODE_OFF:
            return None
        if _ADAPTER is None:
            _ADAPTER = CLBenchAdapter(cfg=cfg, **kw)
        return _ADAPTER
    except Exception:  # noqa: BLE001
        return None


def reset_adapter() -> None:
    global _ADAPTER
    _ADAPTER = None


def wrap_memory(memory: Any) -> Any:
    """``registry.build_memory`` hook. Returns ``memory`` itself when off."""
    adapter = get_adapter()
    if adapter is None:
        return memory
    return HNavMemoryWrapper(memory, adapter, mode=adapter.mode)


def result_annotation() -> dict | None:
    """``infer_context_memory`` hook. ``None`` when off, so the caller adds
    nothing at all to the record."""
    adapter = get_adapter()
    return None if adapter is None else adapter.annotation()
