"""MemoryAgentBench adapter — InEp-Know, the PRIMARY arena.  [T4]

Owns every benchmark-specific fact about this arena so that ``hnav/core/`` does
not have to know any of them:

* memorize messages are 4096-token *chunks* of numbered facts, so a chunk is
  exploded into per-fact candidates with ``FACT_RE``;
* the fact's serial number is the benchmark's own supersession key and becomes
  ``Candidate.version``;
* retrieval units are chunks, not facts, so read-side staleness is resolved by
  mapping retrieved chunks back to the facts they contain.

**Shadow mode returns the caller's own object, unchanged.** ``before_memorize``
returns the exact ``message`` it was handed (identity, not a copy);
``after_retrieval`` returns a ``Decision`` whose ``shadow`` flag the caller must
check before acting. Nothing here mutates a store, and nothing here makes an LLM
call (invariants I1/I2/I3).

Leakage: this module reads fact text and serial numbers only. It never opens the
dataset JSON, so it cannot see the ``questions`` list or the answer list that
sit in the same file. ``hnav/tests/test_leakage_audit.py`` enforces that by AST
scan.
"""
from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav import config as _config  # noqa: E402
from hnav.core.audit import AuditLogger  # noqa: E402
from hnav.core.types import (Candidate, Decision, MemoryRecord,  # noqa: E402
                             RetrievalView, StoreView)
from hnav.labeling.conflict_analysis import parse as parse_fact  # noqa: E402
from hnav.labeling.conflict_index import (Entry, ReadConflictIndex,  # noqa: E402
                                          WriteConflictIndex, to_probe)

__all__ = ["FACT_RE", "MABAdapter", "explode_facts", "fact_key", "native_page_from_scored"]

# The benchmark's own fact numbering. Identical to the regex already used by
# conflict_analysis.analyze and by T1 — deliberately not a second dialect.
FACT_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$", re.M)

# ...but a memorize chunk is NOT the raw context. `chunk_text_into_sentences`
# (utils/eval_other_utils.py:173) splits the context with nltk and rejoins with
# `" ".join(...)`, so wherever punkt found a sentence boundary the newline
# between two facts becomes a space and the line-anchored regex above stops
# matching. FACT_RE is still tried first — it is the prescribed regex and it is
# exact on the raw context — and this inline scanner takes over when the chunk
# has been through the joiner. Each fact runs to the next serial or to the end.
FACT_RE_INLINE = re.compile(r"(?:(?<=\s)|(?<=\A))(\d+)\.\s+(.+?)(?=\s+\d+\.\s|\Z)", re.S)


def _text_id(prefix: str, text: str) -> str:
    return f"{prefix}:{hashlib.sha1(text.encode()).hexdigest()[:12]}"


def fact_key(text: str) -> tuple[tuple[str, str] | None, str | None]:
    """``((relation, subject), object)`` for a fact, or ``(None, None)``.

    Delegates to the validated 99.5%-coverage parser. Do not reimplement.
    """
    p = parse_fact(text)
    if not p:
        return None, None
    rel, subj, obj = p
    return (rel, subj), obj


def explode_facts(message: str) -> list[tuple[int, str]]:
    """A memorize chunk -> ``[(serial, fact_text)]``.

    Tries the line-anchored ``FACT_RE`` first and falls back to
    ``FACT_RE_INLINE`` when the chunk has been through the benchmark's
    sentence-joining chunker and yields fewer facts. Serials are the
    benchmark's own and are preserved exactly; text is right-stripped only.
    """
    primary = [(int(n), t.strip()) for n, t in FACT_RE.findall(message)]
    inline = [(int(n), t.strip()) for n, t in FACT_RE_INLINE.findall(message)]
    return inline if len(inline) > len(primary) else primary


def native_page_from_scored(scored: Sequence[tuple[Any, float]], top_k: int) -> list[str]:
    """The exact list ``TextRetriever.retrieve`` returned before the hook.

    The native code was ``[doc.page_content for doc in
    similarity_search(query, k=top_k)][:top_k]``. The hooked code asks for the
    full ranking instead and truncates here. FAISS flat search is exact, so the
    first ``top_k`` entries of the full ranking are the same documents in the
    same order as a ``k=top_k`` search. This function is the single place that
    equivalence lives, so it can be tested (``test_shadow_neutrality.py``).
    """
    return [doc.page_content for doc, _ in scored[:top_k]]


def to_similarity(scores: Sequence[float], kind: str = "similarity") -> np.ndarray:
    """Normalize a score vector to the H-Nav convention (higher is better).

    ``"similarity"``  already cosine-like; passed through.
    ``"l2sq"``        FAISS squared-L2 distance -> ``cos × 100``, exact for unit
                      vectors and strictly decreasing, so ranks are preserved.
    """
    s = np.asarray(scores, dtype=np.float64)
    if kind == "l2sq":
        return (1.0 - s / 2.0) * 100.0
    if kind != "similarity":
        raise ValueError(f"unknown score_kind {kind!r}")
    return s


@dataclass
class ChunkRecord:
    """One memorize chunk, plus the facts it contains."""

    id: str
    text: str
    index: int
    fact_ids: list[str] = field(default_factory=list)


class MABAdapter:
    """Shadow-mode instrumentation for MemoryAgentBench.

    All components are injected and all are optional: with none of them the
    adapter still records candidate structure, conflicts and rankings, which is
    everything T4 needs. T5 supplies ``signals``; T6 supplies ``geometry`` and
    ``diff``.
    """

    def __init__(self, cfg=None, embedder=None, replica=None, audit: AuditLogger | None = None,
                 signals=None, geometry=None, diff=None, write_policy=None,
                 read_policy=None) -> None:
        self.cfg = cfg or _config.get_config()
        self.cfg.require_not_live()
        self.mode = self.cfg.mode
        self.embedder = embedder
        self.replica = replica
        self.audit = audit
        self.signals = signals
        self.geometry = geometry
        self.diff = diff
        self.write_policy = write_policy
        self.read_policy = read_policy

        self.facts: list[MemoryRecord] = []
        self.chunks: list[ChunkRecord] = []
        self._chunk_by_text: dict[str, ChunkRecord] = {}
        self._fact_by_id: dict[str, MemoryRecord] = {}
        self._fact_chunk: dict[str, str] = {}
        self._chunk_vec: dict[str, np.ndarray] = {}
        self._pending_question_id: Any = None
        self.write_index = WriteConflictIndex()
        self._read_index: ReadConflictIndex | None = None
        self.context_id: Any = None
        self.n_write_decisions = 0
        self.n_read_decisions = 0

    # ── embedding ────────────────────────────────────────────────────────────
    def embed(self, texts: Sequence[str]) -> np.ndarray | None:
        if self.embedder is None:
            return None
        return self.embedder.encode(list(texts))

    def _embed_one(self, text: str) -> np.ndarray | None:
        v = self.embed([text])
        return None if v is None else v[0]

    # ── store views ──────────────────────────────────────────────────────────
    def store_view(self) -> StoreView:
        """Fact-level view of everything admitted so far, in admission order."""
        return StoreView.from_records(self.facts)

    def chunk_store_view(self) -> StoreView:
        """Chunk-level view — the unit the native retriever actually indexes."""
        return StoreView.from_records([
            MemoryRecord(id=c.id, text=c.text, vector=self._chunk_vec.get(c.id),
                         version=c.index, metadata={"fact_ids": c.fact_ids})
            for c in self.chunks
        ])

    # ── read index (whole store — read path only) ────────────────────────────
    def read_index(self) -> ReadConflictIndex:
        if self._read_index is None:
            idx = ReadConflictIndex()
            for rec in self.facts:
                idx.add(rec.metadata.get("key"),
                        Entry(rec.version, rec.id, rec.text, rec.metadata.get("object")))
            self._read_index = idx
        return self._read_index

    # ── write path ───────────────────────────────────────────────────────────
    def probe_generator(self, cand: Candidate) -> list[str]:
        """Deterministic probes from DECISION-TIME information only.

        Must not use benchmark questions, future facts or evaluator output. When
        the fact parses, the probe is its own relation template with the object
        slot left open; otherwise the candidate's own leading text.
        """
        key = cand.metadata.get("key")
        if key:
            return [to_probe(key[0], key[1])]
        return [cand.text[:200]]

    def candidate_for(self, serial: int, text: str, chunk_index: int = 0) -> Candidate:
        key, obj = fact_key(text)
        cand = Candidate(
            id=f"fact:{serial}",
            text=text,
            vector=self._embed_one(text),
            op="ADD",
            version=serial,
            metadata={"context_id": self.context_id, "chunk_index": chunk_index,
                      "key": key, "relation": key[0] if key else None,
                      "subject": key[1] if key else None, "object": obj},
        )
        # Predecessor resolution is ONLINE and must not look ahead: only facts
        # with a strictly smaller serial have been observed at this point.
        prior = self.write_index.latest_before(key, serial)
        if prior is not None:
            cand = cand.with_prior(MemoryRecord(id=prior.id, text=prior.text,
                                                version=prior.version))
        return cand

    def before_memorize(self, message: str, context_id: Any = None,
                        chunk_index: int = 0) -> str:
        """Hook at ``agent.py`` ``send_message(..., memorizing=True)``.

        Returns ``message`` itself — the same object, not a copy — so the caller
        is byte-identical to the unhooked path by construction.
        """
        if self.mode == _config.MODE_OFF:
            return message
        self.context_id = context_id
        store = self.store_view()

        for serial, text in explode_facts(message):
            cand = self.candidate_for(serial, text, chunk_index)
            decision = self._shadow_write_decision(cand, store)
            self.n_write_decisions += 1

            if self.audit is not None:
                self.audit.log_write(
                    cand, geometry=self._geometry_of(cand, store),
                    diff=self._diff_of(cand), retrieval_effect=self._effect_of(cand, store),
                    decision=decision, native_action="ADD", store_size=len(store),
                    context_id=context_id, chunk_index=chunk_index)

            self._admit(cand, chunk_index)
            store = store.with_provisional(cand)   # native behaviour: always admit

        self._register_chunk(message, chunk_index)
        return message

    def _shadow_write_decision(self, cand: Candidate, store: StoreView) -> Decision:
        """Stage 0 emits PASS and nothing else. The policies that could emit
        anything else are gated behind the T8 human decision and are not written
        yet — that is deliberate, not an omission."""
        reasons = {"native_action": "ADD", "has_prior": cand.prior_id is not None}
        if self.write_policy is not None:
            d = self.write_policy.decide(self._geometry_of(cand, store),
                                         self._diff_of(cand),
                                         self._effect_of(cand, store),
                                         ctx=dict(cand.metadata))
            d.shadow = self.mode != _config.MODE_LIVE
            return d
        return Decision(action="PASS", reasons=reasons, shadow=True)

    def _admit(self, cand: Candidate, chunk_index: int) -> None:
        rec = MemoryRecord(id=cand.id, text=cand.text, vector=cand.vector,
                           version=cand.version, metadata=dict(cand.metadata))
        self.facts.append(rec)
        self._fact_by_id[rec.id] = rec
        self.write_index.observe(cand.metadata.get("key"),
                                 Entry(cand.version, cand.id, cand.text,
                                       cand.metadata.get("object")))
        self._read_index = None   # invalidate; rebuilt lazily on the read path

    def _register_chunk(self, text: str, index: int) -> ChunkRecord:
        existing = self._chunk_by_text.get(text)
        if existing is not None:
            return existing
        chunk = ChunkRecord(id=_text_id("chunk", text), text=text, index=index)
        for serial, _ in explode_facts(text):
            fid = f"fact:{serial}"
            chunk.fact_ids.append(fid)
            self._fact_chunk[fid] = chunk.id
        self.chunks.append(chunk)
        self._chunk_by_text[text] = chunk
        return chunk

    # ── optional module plumbing ─────────────────────────────────────────────
    def _geometry_of(self, cand: Candidate, store: StoreView) -> Any:
        if self.geometry is None or cand.vector is None or len(store) == 0:
            return None
        return self.geometry.compute(cand, store)

    def _diff_of(self, cand: Candidate) -> Any:
        if self.diff is None:
            return None
        return self.diff.compute_if_update(cand.prior_text, cand.text,
                                           ctx=dict(cand.metadata))

    def _effect_of(self, cand: Candidate, store: StoreView) -> Any:
        if self.replica is None or self.signals is None or cand.vector is None:
            return None
        probes = self.probe_generator(cand)
        eff = self.replica.simulate_insert(store, cand, probes)
        return self.signals.compute_delta(eff["before"], eff["after"], self_id=cand.id)

    # ── read path ────────────────────────────────────────────────────────────
    def on_retrieve(self, query: str, ranked_texts: Sequence[str],
                    scores: Sequence[float], top_k: int,
                    query_vector: Sequence[float] | None = None,
                    question_id: str | None = None,
                    score_kind: str = "similarity") -> Decision:
        """Hook at ``TextRetriever.retrieve``. Receives the FULL pre-truncation
        ranking; returns a shadow ``Decision`` the caller must ignore.

        ``score_kind="l2sq"`` means the caller passed FAISS's squared-L2
        distances (lower is better). They are converted here — in one testable
        place — to ``cos × 100`` via ``cos = 1 - d²/2``, which is exact for the
        L2-normalized embeddings both shipped embedders produce, and is a
        strictly decreasing transform, so the ranking is untouched.
        """
        if self.mode == _config.MODE_OFF:
            return Decision(action="PASS", shadow=True)

        scores = to_similarity(scores, score_kind)
        ids = []
        for i, text in enumerate(ranked_texts):
            chunk = self._chunk_by_text.get(text) or self._register_chunk(text, i)
            ids.append(chunk.id)

        view = RetrievalView(query=query,
                             query_vector=np.asarray(query_vector, dtype=np.float32)
                             if query_vector is not None else None,
                             ids=ids, scores=np.asarray(scores, dtype=np.float64),
                             top_k=top_k)
        return self.after_retrieval(view, self.store_view(), query,
                                    question_id=question_id)

    def after_retrieval(self, view: RetrievalView, store: StoreView, query: str,
                        question_id: str | None = None) -> Decision:
        """Stale-supersession detection — the primary read-side target.

        Uses only the retrieved chunks and the store. At read time the whole
        store is legitimately visible, so ``ReadConflictIndex.latest`` is the
        correct API here (and ``latest_before`` would be wrong).
        """
        idx = self.read_index()
        retrieved_chunks = set(view.top_ids)
        retrieved_facts = self.facts_in(retrieved_chunks)

        stale_hits = []
        for rec in retrieved_facts:
            newest = idx.superseder_of(rec.id)
            if newest is None:
                continue
            superseder_chunk = self._fact_chunk.get(newest.id)
            stale_hits.append({
                "old_id": rec.id, "new_id": newest.id,
                "old_version": rec.version, "new_version": newest.version,
                "superseder_retrieved": superseder_chunk in retrieved_chunks,
                "rank_of_superseder": view.rank_of(superseder_chunk)
                if superseder_chunk else None,
            })

        conflicted_keys = {rec.metadata.get("key") for rec in retrieved_facts
                           if idx.is_conflicted(rec.metadata.get("key"))}
        conflict = {"stale_in_topk": stale_hits,
                    "n_conflicted_keys_in_topk": len(conflicted_keys - {None}),
                    "n_facts_in_topk": len(retrieved_facts)}

        sig = None
        if self.signals is not None:
            sig = self.signals.compute(view)

        if self.read_policy is not None:
            decision = self.read_policy.decide(
                view, store, ctx={"signals": sig, "stale_hits": stale_hits})
            decision.shadow = self.mode != _config.MODE_LIVE
        else:
            decision = Decision(action="PASS", shadow=True,
                                reasons={"n_stale_in_topk": len(stale_hits)})

        self.n_read_decisions += 1
        if self.audit is not None:
            self.audit.log_read(view, decision, signals=sig, conflict=conflict,
                                store_size=len(store), question_id=question_id)
        return decision

    def facts_in(self, chunk_ids: Iterable[str]) -> list[MemoryRecord]:
        wanted = set(chunk_ids)
        out = []
        for chunk in self.chunks:
            if chunk.id in wanted:
                out.extend(self._fact_by_id[f] for f in chunk.fact_ids
                           if f in self._fact_by_id)
        return out

    # ── agent.py send_message callbacks ──────────────────────────────────────
    def on_send_message_enter(self, message: str, memorizing: bool = False,
                              query_id: Any = None, context_id: Any = None) -> None:
        if self.mode == _config.MODE_OFF:
            return
        if context_id is not None and context_id != self.context_id:
            self.context_id = context_id
        if memorizing:
            self.before_memorize(message, context_id=context_id,
                                 chunk_index=len(self.chunks))
        else:
            self._pending_question_id = query_id

    def on_send_message_exit(self, result: Any, message: str, memorizing: bool = False,
                             query_id: Any = None, context_id: Any = None) -> Any:
        """Returns ``result`` unchanged. Present so that live mode has a seam;
        in shadow it exists only to close the audit record."""
        return result

    def apply_read_decision(self, decision: Decision, scored, top_k: int):
        """Live-mode seam. Stage 0 must never reach it."""
        raise RuntimeError(
            "apply_read_decision is live-mode code and is gated behind the T8 "
            "decision. Stage 0 runs in off/shadow only."
        )


_ADAPTER: MABAdapter | None = None


def get_adapter(**kw) -> MABAdapter | None:
    """Process-wide adapter, or ``None`` when ``HNAV_MODE=off``.

    The benchmark hooks call this. It must never raise: a misconfigured H-Nav
    has to degrade to "no instrumentation", never to "broken benchmark".
    """
    global _ADAPTER
    try:
        cfg = _config.get_config()
        if cfg.mode == _config.MODE_OFF:
            return None
        if _ADAPTER is None:
            _ADAPTER = MABAdapter(cfg=cfg, **kw)
        return _ADAPTER
    except Exception:  # noqa: BLE001
        return None


def reset_adapter() -> None:
    global _ADAPTER
    _ADAPTER = None
