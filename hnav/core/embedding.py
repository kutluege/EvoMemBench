"""Embedder interface + implementations.  [T3]

One protocol, three implementations:

* :class:`HashEmbedder`     — deterministic pseudo-random unit vectors seeded by
  ``sha256(text)``. Test-only. No model, no GPU, no network. Every numeric test
  in ``hnav/tests/`` runs against this, which is what lets the whole numeric core
  be verified on a machine with no torch.
* :class:`HFEmbedder`       — the real one. Loads Qwen3-Embedding-4B in-process on
  the GPU. **torch/transformers are imported inside ``__init__``**, never at
  module import time, so importing this module on a torchless machine is safe.
* :class:`OpenAIEmbedder`   — an OpenAI-compatible ``/v1/embeddings`` endpoint,
  for the T4+ path where the benchmark itself is running against a served model.

:class:`HFEmbedder`'s pooling mirrors ``Qwen3Embedding4BEmbeddings`` at
``MemoryAgentBench/methods/embedding_retriever.py:58`` — mean pooling over the
attention mask, then L2 normalization — so H-Nav's geometry is the geometry the
benchmark's own retriever operates in.

The disk cache layout is **byte-compatible with T1's**
(``hnav/stage0/m1_geometry_calibration.py``): ``<sha256(model|dtype||text)>.npy``
under ``HNAV_CACHE_DIR/emb``. T2 and everything after therefore reuse T1's
~26k embeddings for free, as the brief requires.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

import numpy as np

__all__ = ["EmbedderProtocol", "HashEmbedder", "HFEmbedder", "OpenAIEmbedder",
           "DiskCachedEmbedder", "cache_key", "l2_normalize"]


@runtime_checkable
class EmbedderProtocol(Protocol):
    """Everything H-Nav needs from an embedder.

    ``encode`` returns an ``(n, dim)`` float32 array of **L2-normalized** rows,
    in the same order as ``texts``.
    """

    dim: int

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...


def l2_normalize(v: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalization matching ``Qwen3EmbeddingMemory._l2_normalize``
    (``qwen3_embedding_memory.py:131``): a zero vector is returned unchanged."""
    v = np.asarray(v, dtype=np.float32)
    if v.ndim == 1:
        n = float(np.linalg.norm(v))
        return v / (n + 1e-10) if n > 0 else v
    n = np.linalg.norm(v, axis=1, keepdims=True)
    out = np.where(n > 0, v / (n + 1e-10), v)
    return out.astype(np.float32)


def cache_key(model: str, dtype: str) -> str:
    """The cache namespace. Identical to ``Embedder.key`` in T1."""
    return f"{model}|{dtype}".replace("/", "_")


def _cache_path(cache_dir: Path, key: str, text: str) -> Path:
    h = hashlib.sha256((key + "||" + text).encode()).hexdigest()
    return cache_dir / f"{h}.npy"


# ── test embedder ────────────────────────────────────────────────────────────
class HashEmbedder:
    """Deterministic unit vectors seeded by the text hash. TEST USE ONLY.

    Properties the tests rely on:
      * ``encode`` is a pure function of the text — same text, same vector, in
        any process, on any platform;
      * distinct texts give near-orthogonal vectors in expectation, so nothing
        accidentally lands at cosine 1.0;
      * identical texts give cosine exactly 1.0, which is what makes the
        exact-duplicate and tie fixtures meaningful.

    It carries no semantics whatsoever. No threshold may be fit against it.
    """

    def __init__(self, dim: int = 64, salt: str = "hnav") -> None:
        self.dim = int(dim)
        self.salt = salt

    def _one(self, text: str) -> np.ndarray:
        seed = int.from_bytes(
            hashlib.sha256((self.salt + "||" + text).encode()).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        return l2_normalize(rng.standard_normal(self.dim).astype(np.float32))

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not len(texts):
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.stack([self._one(t) for t in texts])


# ── disk cache wrapper ───────────────────────────────────────────────────────
class DiskCachedEmbedder:
    """Wrap any embedder with the shared on-disk cache.

    Kept separate from :class:`HFEmbedder` so that the cache can be exercised in
    tests against :class:`HashEmbedder`.
    """

    def __init__(self, inner: EmbedderProtocol, cache_dir: Path, key: str) -> None:
        self.inner = inner
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.key = key
        self.dim = getattr(inner, "dim", 0)
        self.n_hits = 0
        self.n_misses = 0

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        out: list[np.ndarray | None] = [None] * len(texts)
        todo: list[int] = []
        for i, t in enumerate(texts):
            p = _cache_path(self.cache_dir, self.key, t)
            if p.exists():
                out[i] = np.load(p)
                self.n_hits += 1
            else:
                todo.append(i)
        if todo:
            self.n_misses += len(todo)
            fresh = self.inner.encode([texts[i] for i in todo])
            for j, i in enumerate(todo):
                out[i] = fresh[j]
                np.save(_cache_path(self.cache_dir, self.key, texts[i]), fresh[j])
        if not len(texts):
            return np.zeros((0, self.dim), dtype=np.float32)
        stacked = np.stack([np.asarray(o, dtype=np.float32) for o in out])  # type: ignore[arg-type]
        self.dim = stacked.shape[1]
        return stacked


# ── real embedders (lazy heavy imports) ──────────────────────────────────────
class HFEmbedder:
    """In-process HuggingFace embedder, mean-pooled + L2-normalized.

    torch and transformers are imported in ``__init__``. Importing this module
    costs nothing and pulls in nothing; ``hnav/tests/test_no_torch_at_import.py``
    asserts exactly that.
    """

    def __init__(self, model_name: str, device: int = 1, dtype: str = "float32",
                 batch: int = 32, max_length: int = 512) -> None:
        import torch  # noqa: PLC0415 — deliberate: keeps module import torch-free
        from transformers import AutoModel, AutoTokenizer  # noqa: PLC0415

        self._torch = torch
        self.model_name = model_name
        self.batch = batch
        self.max_length = max_length
        self.device = f"cuda:{device}" if torch.cuda.is_available() else "cpu"
        self.dtype_name = dtype
        torch_dtype = {"float32": torch.float32, "float16": torch.float16,
                       "bfloat16": torch.bfloat16}[dtype]
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, torch_dtype=torch_dtype).to(self.device)
        self.model.eval()
        self.dim = int(self.model.config.hidden_size)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not len(texts):
            return np.zeros((0, self.dim), dtype=np.float32)
        chunks = []
        for s in range(0, len(texts), self.batch):
            batch_texts = list(texts[s: s + self.batch])
            enc = self.tok(batch_texts, padding=True, truncation=True,
                           max_length=self.max_length, return_tensors="pt").to(self.device)
            with self._torch.no_grad():
                res = self.model(**enc)
            last = res.last_hidden_state if hasattr(res, "last_hidden_state") else res[0]
            mask = enc["attention_mask"].unsqueeze(-1).expand(last.size()).to(last.dtype)
            pooled = (last * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            pooled = self._torch.nn.functional.normalize(pooled, p=2, dim=1)
            chunks.append(pooled.float().cpu().numpy())
        return np.vstack(chunks)


class OpenAIEmbedder:
    """An OpenAI-compatible ``/v1/embeddings`` endpoint (vLLM on :8001).

    Used when the benchmark process itself needs embeddings; the ``openai``
    client is imported lazily for the same reason as torch above.
    """

    def __init__(self, base_url: str, model: str, api_key: str = "EMPTY",
                 batch: int = 32, dim: int = 0) -> None:
        from openai import OpenAI  # noqa: PLC0415

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.batch = batch
        self.dim = dim

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not len(texts):
            return np.zeros((0, self.dim), dtype=np.float32)
        rows: list[np.ndarray] = []
        for s in range(0, len(texts), self.batch):
            resp = self.client.embeddings.create(
                model=self.model, input=list(texts[s: s + self.batch]))
            rows.extend(np.asarray(d.embedding, dtype=np.float32) for d in resp.data)
        out = l2_normalize(np.stack(rows))
        self.dim = out.shape[1]
        return out


def build_embedder(cfg, cached: bool = True) -> EmbedderProtocol:
    """Construct the configured real embedder, wrapped in the shared disk cache.

    Importing this module never triggers a model load; only calling this does.
    """
    inner = HFEmbedder(cfg.embed_model, cfg.embed_device, cfg.embed_dtype, cfg.embed_batch)
    if not cached:
        return inner
    return DiskCachedEmbedder(inner, cfg.emb_cache_dir,
                              cache_key(cfg.embed_model, cfg.embed_dtype))
