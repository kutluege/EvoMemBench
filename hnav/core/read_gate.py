"""Two-stage read gate: geometric filter + bidirectional NLI.  [T9]

Faz A of the Stage-1 plan (``STAGE1_PLAN.md`` §2). The gate DECIDES whether a
retrieved candidate set contains verified conflict groups and names each group's
LATEST member; it never touches a ranking. Rerank execution belongs to
``read_policy.py``, which is built in Faz B — the division exists so that the
verification pipeline can be tested to the repo's closed-form standard before
any intervention code exists.

Stage 1 — geometric filter
    Pairs of retrieved candidates with cosine ≥ ``cos_pair`` form edges;
    connected components of those edges are *tentative* groups. A tentative
    group survives only if its minimum leave-one-out span residual — the QR
    residual of a member against the span of ALL OTHER candidates in the set,
    the same ``qr_residual`` the write path uses — is below ``r_min``. The
    whole stage is preconditioned on ranking ambiguity: ``nmargin`` below /
    ``H_z`` above the frozen Stage-0 thresholds, consumed ONLY through
    ``RetrievalSignalSet.for_policy()`` so the raw-score entropy can never
    reach a decision (hard rule 6; the AST scan in
    ``test_no_raw_entropy_in_policy.py`` covers this module).

Stage 2 — bidirectional NLI
    Every within-group pair is scored in both directions by an
    :class:`NLIClient`. A pair is a **verified conflict** only if the
    contradiction score clears ``nli_contradiction`` in BOTH directions
    (A⇒B and B⇒A). One-directional contradiction — e.g. entailment one way —
    is rejected: supersession in this arena is symmetric disagreement about
    the same slot, not refinement. Final groups are connected components of
    verified edges only.

Optional pair screen — the Note-1 mitigation seam (Faz B).
    The Faz A audit measured that the NLI cross-encoder falsely verifies
    same-template/DIFFERENT-SUBJECT pairs as bidirectional contradiction
    ("Thomas Kyd was born in London." vs "Marlowe was born in London."
    → 0.999 both directions), so NLI alone cannot carry subject identity.
    ``ReadGate(pair_filter=...)`` lets the ADAPTER supply identity evidence
    (e.g. equality of its parsed ``(relation, subject)`` key) as an extra
    screen on cosine-passed pairs, BEFORE any NLI is spent on them. The core
    stays benchmark-agnostic: the filter is an opaque callable on two
    :class:`~hnav.core.types.MemoryRecord` objects; ``None`` (the default)
    preserves the Faz A behaviour exactly. Rejections are counted in
    ``GateDecision.n_pairs_filter_rejected``.

Threshold provenance. Defaults are the FROZEN Stage-0 calibration values
(``stage0_results/final/m3_headroom.json``, fit on sh_6k+sh_32k only,
``unfit_for_analysis: false``): ``nmargin < 0.0048``, ``H_z > 1.9569``,
``r_min < 0.1924``; ``cos_pair`` defaults to the mean of M1b's best-F1 taus on
the same calibration split (0.91, 0.93 → 0.92). They are exposed as parameters
because Faz B tunes them coverage-balanced — on sh_6k+sh_32k ONLY, never on
sh_64k/sh_262k. Note the coupling stated rather than hidden: for a two-member
group whose other candidates are unrelated, the leave-one-out residual is
``sqrt(1 − cos²)``, so the frozen ``r_min`` implies pair cosine ≳ 0.981 — the
default gate is deliberately precision-first until Faz B rebalances it.

Benchmark-agnostic by construction: LATEST is named through an
adapter-supplied ``latest_key`` callable (serials live in the adapter, hard
rule "core imports nothing from a benchmark"); absent one, the
:class:`~hnav.core.types.MemoryRecord` ``version`` field is used, and any
missing or tied key yields ``latest_id=None`` rather than a guess.

torch/transformers are imported only inside :class:`CrossEncoderNLI.__init__`;
importing this module is free (``test_no_torch_at_import.py``).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

import numpy as np

from .geometry import qr_residual
from .retrieval_signals import POLICY_FORBIDDEN
from .types import MemoryRecord

__all__ = [
    "NMARGIN_CAL", "H_Z_CAL", "R_MIN_CAL", "COS_PAIR_CAL", "NLI_CONTRA_DEFAULT",
    "NLI_MODEL_DEFAULT", "GateThresholds", "NLIScores", "NLIClient", "StubNLI",
    "CrossEncoderNLI", "PairCheck", "ConflictGroup", "GateDecision", "ReadGate",
    "build_nli",
]

# ── frozen Stage-0 calibration values (sh_6k + sh_32k ONLY) ──────────────────
# Full precision from stage0_results/final/m3_headroom.json ("thresholds",
# fit_subsets ["sh_6k","sh_32k"], unfit_for_analysis false). Rounded forms
# quoted in KAPI_KARARI.md §1: nmargin<0.0048, H_z>1.9569, r_min<0.1924.
NMARGIN_CAL = 0.004764391389658354
H_Z_CAL = 1.9569327964981853
R_MIN_CAL = 0.19236616622633881
# Mean of M1b best-F1 taus on the calibration split (sh_6k 0.91, sh_32k 0.93).
COS_PAIR_CAL = 0.92
# Probability-majority baseline for the bidirectional contradiction criterion.
NLI_CONTRA_DEFAULT = 0.5

NLI_MODEL_DEFAULT = "cross-encoder/nli-deberta-v3-large"

_AMBIGUITY_MODES = ("any", "all", "none")


@dataclass(frozen=True)
class GateThresholds:
    """Every tunable of the gate, in one auditable frozen object.

    ``None`` disables the corresponding screen. Faz B may retune these
    coverage-balanced on the calibration split; the defaults above are the
    frozen Stage-0 baseline and their provenance is in the module docstring.
    """

    nmargin: float | None = NMARGIN_CAL       # ambiguity: nmargin BELOW this
    H_z: float | None = H_Z_CAL               # ambiguity: H_z ABOVE this
    r_min: float | None = R_MIN_CAL           # group min LOO residual BELOW this
    cos_pair: float | None = COS_PAIR_CAL     # pair cosine AT LEAST this
    nli_contradiction: float = NLI_CONTRA_DEFAULT   # both directions AT LEAST this
    ambiguity_mode: str = "any"               # "any" | "all" | "none"

    def __post_init__(self) -> None:
        if self.ambiguity_mode not in _AMBIGUITY_MODES:
            raise ValueError(
                f"ambiguity_mode={self.ambiguity_mode!r} not in {_AMBIGUITY_MODES}")

    def to_dict(self) -> dict:
        return asdict(self)


# ── NLI interface ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class NLIScores:
    """One directed premise→hypothesis judgement, as probabilities."""

    entailment: float
    neutral: float
    contradiction: float

    @property
    def label(self) -> str:
        best, best_v = "entailment", self.entailment
        for name, v in (("neutral", self.neutral),
                        ("contradiction", self.contradiction)):
            if v > best_v:
                best, best_v = name, v
        return best

    def to_dict(self) -> dict:
        d = asdict(self)
        d["label"] = self.label
        return d


@runtime_checkable
class NLIClient(Protocol):
    """Everything the gate needs from an NLI engine.

    ``score_pairs`` takes directed ``(premise, hypothesis)`` pairs and returns
    one :class:`NLIScores` per pair, in order. Direction matters; the gate
    submits both directions itself.
    """

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[NLIScores]: ...


class StubNLI:
    """Deterministic rule-based NLI. TEST USE ONLY — like ``HashEmbedder``,
    it carries no semantics and no threshold may be fit against it.

    Rules, in order:
      1. an exact ``(premise, hypothesis)`` entry in ``overrides`` wins;
      2. identical texts → entailment;
      3. token-overlap ratio ≥ ``min_overlap`` (same template, changed slot —
         the arena's supersession shape) → contradiction;
      4. otherwise → neutral.

    Pure function of its inputs: same pair, same scores, in any process.
    """

    ENTAIL = (0.94, 0.05, 0.01)
    CONTRA = (0.03, 0.07, 0.90)
    NEUTRAL = (0.05, 0.90, 0.05)

    def __init__(self, overrides: Mapping[tuple[str, str], tuple[float, float, float]] | None = None,
                 min_overlap: float = 0.6) -> None:
        self.overrides = dict(overrides or {})
        self.min_overlap = float(min_overlap)

    def score(self, premise: str, hypothesis: str) -> NLIScores:
        if (premise, hypothesis) in self.overrides:
            e, n, c = self.overrides[(premise, hypothesis)]
        elif premise == hypothesis:
            e, n, c = self.ENTAIL
        elif self._overlap(premise, hypothesis) >= self.min_overlap:
            e, n, c = self.CONTRA
        else:
            e, n, c = self.NEUTRAL
        return NLIScores(entailment=e, neutral=n, contradiction=c)

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[NLIScores]:
        return [self.score(p, h) for p, h in pairs]

    @staticmethod
    def _overlap(a: str, b: str) -> float:
        from difflib import SequenceMatcher  # stdlib; local to keep import cost nil
        return SequenceMatcher(a=(a or "").split(), b=(b or "").split(),
                               autojunk=False).ratio()


class CrossEncoderNLI:
    """MNLI-class cross-encoder (default ``cross-encoder/nli-deberta-v3-large``).

    torch and transformers are imported in ``__init__``, never at module import
    time — same lazy pattern as :class:`~hnav.core.embedding.HFEmbedder`. The
    label order is read from the checkpoint's ``id2label`` rather than assumed,
    so a differently-ordered NLI head cannot silently swap entailment and
    contradiction.

    ``device``: an int selects ``cuda:{n}`` when CUDA is available (GPU1 by
    default, alongside the fp32 embedder — DeBERTa-v3-large is ~435M params,
    ~1.7 GB of fp32 weights, small next to the embedder's ~17 GB); a string
    (``"cpu"``, ``"cuda:0"``) is used verbatim.
    """

    def __init__(self, model_name: str = NLI_MODEL_DEFAULT, device: int | str = 1,
                 dtype: str = "float32", batch: int = 16, max_length: int = 256) -> None:
        import torch  # noqa: PLC0415 — deliberate: keeps module import torch-free
        from transformers import (AutoModelForSequenceClassification,  # noqa: PLC0415
                                  AutoTokenizer)

        self._torch = torch
        self.model_name = model_name
        self.batch = int(batch)
        self.max_length = int(max_length)
        if isinstance(device, int):
            self.device = f"cuda:{device}" if torch.cuda.is_available() else "cpu"
        else:
            self.device = str(device)
        torch_dtype = {"float32": torch.float32, "float16": torch.float16,
                       "bfloat16": torch.bfloat16}[dtype]
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, torch_dtype=torch_dtype).to(self.device)
        self.model.eval()

        id2label = {int(k): str(v).lower() for k, v in self.model.config.id2label.items()}
        self._idx: dict[str, int] = {}
        for i, lab in id2label.items():
            if "entail" in lab:
                self._idx["entailment"] = i
            elif "contra" in lab:
                self._idx["contradiction"] = i
            elif "neutral" in lab:
                self._idx["neutral"] = i
        if set(self._idx) != {"entailment", "neutral", "contradiction"}:
            raise ValueError(f"{model_name} id2label={id2label} is not a 3-way NLI head")

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[NLIScores]:
        if not pairs:
            return []
        out: list[NLIScores] = []
        for s in range(0, len(pairs), self.batch):
            chunk = list(pairs[s: s + self.batch])
            enc = self.tok([p for p, _ in chunk], [h for _, h in chunk],
                           padding=True, truncation=True, max_length=self.max_length,
                           return_tensors="pt").to(self.device)
            with self._torch.no_grad():
                logits = self.model(**enc).logits.float()
                probs = self._torch.softmax(logits, dim=-1).cpu().numpy()
            for row in probs:
                out.append(NLIScores(
                    entailment=float(row[self._idx["entailment"]]),
                    neutral=float(row[self._idx["neutral"]]),
                    contradiction=float(row[self._idx["contradiction"]])))
        return out

    def score(self, premise: str, hypothesis: str) -> NLIScores:
        return self.score_pairs([(premise, hypothesis)])[0]


def build_nli(cfg) -> CrossEncoderNLI:
    """The configured real NLI engine. Importing this module never loads it;
    only calling this does (same contract as ``embedding.build_embedder``)."""
    return CrossEncoderNLI(model_name=cfg.nli_model, device=cfg.nli_device,
                           dtype=cfg.nli_dtype, batch=cfg.nli_batch)


# ── gate output ──────────────────────────────────────────────────────────────
@dataclass
class PairCheck:
    """Evidence for one unordered pair that reached the NLI stage."""

    id_a: str
    id_b: str
    cos: float
    contra_ab: float = float("nan")
    contra_ba: float = float("nan")
    entail_ab: float = float("nan")
    entail_ba: float = float("nan")
    verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConflictGroup:
    """A verified conflict group. ``latest_id`` is ``None`` when the recency
    key is missing or tied — the gate refuses to guess, and a group without a
    LATEST is unactionable downstream by construction."""

    member_ids: list[str]
    latest_id: str | None
    stale_ids: list[str]
    residuals: dict[str, float]           # leave-one-out span residual per member
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GateDecision:
    """What the gate concluded, with the full evidence trail. Decision only —
    holding one of these mutates nothing anywhere."""

    ambiguous: bool
    n_candidates: int = 0
    n_pairs_screened: int = 0
    n_pairs_cos: int = 0
    n_pairs_filter_rejected: int = 0
    n_groups_cos: int = 0
    n_groups_geometric: int = 0
    n_pairs_nli: int = 0
    n_pairs_verified: int = 0
    groups: list[ConflictGroup] = field(default_factory=list)
    pair_checks: list[PairCheck] = field(default_factory=list)
    reasons: dict = field(default_factory=dict)

    @property
    def has_verified_conflict(self) -> bool:
        return bool(self.groups)

    def to_dict(self) -> dict:
        return asdict(self)


# ── the gate ─────────────────────────────────────────────────────────────────
def _components(n: int, edges: Sequence[tuple[int, int]]) -> list[list[int]]:
    """Connected components of size ≥ 2, members ascending, deterministic."""
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    by_root: dict[int, list[int]] = {}
    for i in range(n):
        by_root.setdefault(find(i), []).append(i)
    return [sorted(m) for _, m in sorted(by_root.items()) if len(m) >= 2]


class ReadGate:
    """The two-stage gate. Construct once, call :meth:`decide` per retrieval.

    ``nli`` is required: verification without stage 2 is not verification.
    Tests use :class:`StubNLI`; live runs use :func:`build_nli`.

    ``pair_filter`` is the optional identity screen described in the module
    docstring: a callable ``(rec_a, rec_b) -> bool`` applied to every pair
    that passes the cosine screen; ``False`` drops the edge before NLI.
    """

    def __init__(self, nli: NLIClient, thresholds: GateThresholds | None = None,
                 pair_filter: Callable[[MemoryRecord, MemoryRecord], bool] | None = None,
                 ) -> None:
        self.nli = nli
        self.thresholds = thresholds or GateThresholds()
        self.pair_filter = pair_filter

    # ── ambiguity precondition ───────────────────────────────────────────────
    def _ambiguity(self, signal_view) -> tuple[bool, dict]:
        thr = self.thresholds
        if thr.ambiguity_mode == "none":
            return True, {"ambiguity_mode": "none"}
        if signal_view is None:
            raise ValueError(
                "ambiguity precondition needs retrieval signals; pass a "
                "RetrievalSignalSet (or its for_policy() mapping), or set "
                "ambiguity_mode='none'")
        pol = signal_view.for_policy() if hasattr(signal_view, "for_policy") \
            else dict(signal_view)
        for name in POLICY_FORBIDDEN:
            if name in pol:
                raise ValueError(f"forbidden signal {name!r} may not reach the gate")

        nm = float(pol.get("nmargin", float("nan")))
        hz = float(pol.get("H_z", float("nan")))
        flags = []
        nm_flag = hz_flag = False
        if thr.nmargin is not None:
            nm_flag = bool(np.isfinite(nm) and nm < thr.nmargin)
            flags.append(nm_flag)
        if thr.H_z is not None:
            hz_flag = bool(np.isfinite(hz) and hz > thr.H_z)
            flags.append(hz_flag)
        if not flags:                       # both screens disabled → vacuous
            amb = True
        elif thr.ambiguity_mode == "any":
            amb = any(flags)
        else:
            amb = all(flags)
        return amb, {"ambiguity_mode": thr.ambiguity_mode,
                     "nmargin_flag": nm_flag, "H_z_flag": hz_flag}

    # ── decision ─────────────────────────────────────────────────────────────
    def decide(self, candidates: Sequence[MemoryRecord],
               signal_view=None,
               latest_key: Callable[[MemoryRecord], Any] | None = None,
               ) -> GateDecision:
        """Inspect ``candidates`` (the retrieved page, ranked order) and return
        a :class:`GateDecision`. Mutates nothing: not the records, not the
        ranking, not the store.
        """
        recs = list(candidates)
        thr = self.thresholds
        ambiguous, amb_reasons = self._ambiguity(signal_view)
        dec = GateDecision(ambiguous=ambiguous, n_candidates=len(recs),
                           reasons={"thresholds": thr.to_dict(), **amb_reasons})
        if not ambiguous or len(recs) < 2:
            return dec

        missing = [r.id for r in recs if r.vector is None]
        if missing:
            raise ValueError(f"{len(missing)} candidate(s) without a vector, "
                             f"first={missing[0]!r}; embed before gating")
        mat = np.stack([np.asarray(r.vector, dtype=np.float64) for r in recs])
        sims = mat @ mat.T
        n = len(recs)

        # stage 1a: cosine screen, then the optional identity screen
        all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        dec.n_pairs_screened = len(all_pairs)
        edges = []
        for i, j in all_pairs:
            if thr.cos_pair is not None and sims[i, j] < thr.cos_pair:
                continue
            if self.pair_filter is not None and not self.pair_filter(recs[i], recs[j]):
                dec.n_pairs_filter_rejected += 1
                continue
            edges.append((i, j))
        dec.n_pairs_cos = len(edges)
        dec.reasons["pair_filter_active"] = self.pair_filter is not None

        tentative = _components(n, edges)
        dec.n_groups_cos = len(tentative)

        # stage 1b: leave-one-out span residual (the r_min family)
        loo: dict[int, float] = {}
        for i in sorted({i for g in tentative for i in g}):
            r, _ = qr_residual(mat[i], np.delete(mat, i, axis=0))
            loo[i] = float(r[0])
        geo_groups = [g for g in tentative
                      if thr.r_min is None or min(loo[i] for i in g) < thr.r_min]
        dec.n_groups_geometric = len(geo_groups)

        # stage 2: bidirectional NLI over every within-group pair
        pair_list: list[tuple[int, int]] = []
        directed: list[tuple[str, str]] = []
        for g in geo_groups:
            for a in range(len(g)):
                for b in range(a + 1, len(g)):
                    i, j = g[a], g[b]
                    pair_list.append((i, j))
                    directed.append((recs[i].text, recs[j].text))
                    directed.append((recs[j].text, recs[i].text))
        dec.n_pairs_nli = len(pair_list)

        nli_scores = self.nli.score_pairs(directed) if directed else []
        verified_edges: list[tuple[int, int]] = []
        for k, (i, j) in enumerate(pair_list):
            ab, ba = nli_scores[2 * k], nli_scores[2 * k + 1]
            ok = (ab.contradiction >= thr.nli_contradiction
                  and ba.contradiction >= thr.nli_contradiction)
            dec.pair_checks.append(PairCheck(
                id_a=recs[i].id, id_b=recs[j].id, cos=float(sims[i, j]),
                contra_ab=ab.contradiction, contra_ba=ba.contradiction,
                entail_ab=ab.entailment, entail_ba=ba.entailment, verified=ok))
            if ok:
                verified_edges.append((i, j))
        dec.n_pairs_verified = len(verified_edges)

        # final groups: components of VERIFIED edges only
        key_fn = latest_key or (lambda r: r.version)
        for g in _components(n, verified_edges):
            dec.groups.append(self._finalize(g, recs, loo, key_fn))
        return dec

    @staticmethod
    def _finalize(members: list[int], recs: list[MemoryRecord],
                  loo: Mapping[int, float],
                  key_fn: Callable[[MemoryRecord], Any]) -> ConflictGroup:
        vals = [key_fn(recs[i]) for i in members]
        note = ""
        latest_id: str | None = None
        if any(v is None for v in vals):
            note = "recency key missing for at least one member"
        else:
            mx = max(vals)
            if vals.count(mx) > 1:
                note = "recency key tied at the maximum"
            else:
                latest_id = recs[members[vals.index(mx)]].id
        member_ids = [recs[i].id for i in members]
        stale = [m for m in member_ids if m != latest_id] if latest_id else []
        return ConflictGroup(
            member_ids=member_ids, latest_id=latest_id, stale_ids=stale,
            residuals={recs[i].id: float(loo[i]) for i in members}, note=note)
