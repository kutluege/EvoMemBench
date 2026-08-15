#!/usr/bin/env python3
"""Re-embed chunks at the corrected length, and PROVE the page is faithful.  [T13]

Two jobs, and the second is the one that matters.

**Freshness.** Every cached vector this project holds sits under the pre-T12
namespace ``Qwen_Qwen3-Embedding-4B|float32``, written while ``max_length`` was
silently 512. Measured here: the longest memorize chunk in the four single-hop
subsets is **5,243 Qwen tokens**, so a 512-token budget captured under 10% of it.
This script re-embeds into ``…|float32|L8192`` and **never touches the old
namespace**, which is the provenance of every committed Stage-0 number.

**Fidelity.** Freshness alone is not enough, and at ``sh_64k`` the difference is
decisive: that subset is 17 chunks against ``top_k`` 10, so the chunk vectors
decide *which chunks reach the page at all*. A page chosen by H-Nav's own
embedder — however well configured — is an artifact unless it is the page the
BENCHMARK's retriever would have produced. So this script drives the benchmark's
own ``Qwen3Embedding4BEmbeddings`` over the same chunks and compares, following
the M0 precedent that earned the 1.0000 replica-fidelity claim: reconstruct
through the benchmark's own code path, then check agreement rather than assert it.

What the comparison can and cannot find
---------------------------------------
The two encoders are the same weights, the same mean-pooling-over-attention-mask,
the same L2 normalization and the same fp32. They differ in exactly two ways, and
those are the two the check is aimed at:

1. **Truncation.** The benchmark calls ``tokenizer(text, truncation=True)`` with
   NO ``max_length``, so it truncates at ``tokenizer.model_max_length`` =
   **131,072** — i.e. it does not truncate these chunks at all. H-Nav at 8192
   does not either (longest chunk 5,243). At 512 it did, on every chunk. So the
   corrected setting is not "better than the benchmark", it is *the same as* the
   benchmark; that is the point.
2. **Batching.** The benchmark embeds one text per forward pass; H-Nav batches
   with padding. Mask-weighted mean pooling makes padding mathematically inert,
   but float reduction order is not bitwise identical, so the residual is
   measured and reported instead of argued.

Three rankings are produced per question and compared:

``L8192_hnav``      corrected vectors, H-Nav's replica — what a Branch A run uses
``L8192_benchmark`` benchmark-class vectors, exact cosine — the reference page
``L512_hnav``       the stale cached vectors — the status quo being replaced

``L8192_hnav`` vs ``L8192_benchmark`` is the fidelity claim. ``L8192_hnav`` vs
``L512_hnav`` measures how much damage the defect was doing to page selection.

Facts are re-embedded too, and checked against their 512-namespace values: a
fact is one short sentence, far under either budget, so the vectors must be
identical. If they are, the frozen operating point and every committed detection
number carry over unchanged — which is worth establishing rather than assuming.

GPU discipline
--------------
``CUDA_VISIBLE_DEVICES`` is pinned by the caller to the card we own. It matters:
the benchmark's class constructs with ``device_map="auto"``, which would happily
allocate on the user's GPU0 and could OOM their server. With the variable set,
GPU0 is invisible to this process. The two ~17 GB fp32 models are loaded and
freed **sequentially**; they cannot coexist on one card.

    CUDA_VISIBLE_DEVICES=1 python hnav/deploy/refit_chunk_embeddings.py \\
        --subsets sh_6k sh_32k sh_64k
    python hnav/deploy/refit_chunk_embeddings.py --dry-run    # plan only, no GPU
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
from hnav.core.embedding import DiskCachedEmbedder, cache_key  # noqa: E402
from hnav.stage0.m2_retrieval_calibration import build_chunks  # noqa: E402
from hnav.stage1.calibrate_read_policy import (QUERY_TEMPLATE,  # noqa: E402
                                               RETRIEVAL_EXTRACT)

DATA = REPO / "In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench/data/Conflict_Resolution.json"
BENCH = REPO / "In-Episode-Knowledge/INEP-KNOW/MemoryAgentBench"
OUT = REPO / "stage0_results/stage1/chunk_embedding_refit.json"
CHUNK_SIZE = 4096
TOP_K = 10
LEGACY_KEY = "Qwen_Qwen3-Embedding-4B|float32"      # the pre-T12 namespace
# Agreement tolerance for "the same vector". Two fp32 forward passes that differ
# only in batch composition land far inside this; a truncation difference does
# not come close to it.
COS_TOL = 1e-4


# ── inputs ───────────────────────────────────────────────────────────────────
def subset_name(item: dict) -> str:
    return item["metadata"]["qa_pair_ids"][0].rsplit("_no", 1)[0] \
        .replace("factconsolidation_", "")


def load_subsets(names) -> dict:
    from hnav.adapters.mab_adapter import explode_facts
    data = json.loads(DATA.read_text(encoding="utf-8"))
    out = {}
    for item in data:
        name = subset_name(item)
        if name not in names:
            continue
        chunks, fallback = build_chunks(item["context"], CHUNK_SIZE)
        if fallback:
            raise SystemExit(
                f" REFUSED: nltk/punkt missing — {name} fell back to a chunker "
                "that is not the benchmark's. The whole point is fidelity.")
        queries = [RETRIEVAL_EXTRACT.search(QUERY_TEMPLATE.format(question=q)).group(1)
                   for q in item.get("questions", [])]
        out[name] = {
            "chunks": chunks,
            "facts": [t for _, t in explode_facts(item["context"])],
            "queries": queries,
        }
    missing = [n for n in names if n not in out]
    if missing:
        raise SystemExit(f" REFUSED: no dataset item for {missing}")
    return out


# ── ranking ──────────────────────────────────────────────────────────────────
def rank_pages(chunk_vecs: np.ndarray, query_vecs: np.ndarray, top_k: int):
    """Top-k chunk indices per query, by exact cosine on unit vectors.

    Both shipped index paths are exact flat searches over L2-normalized vectors
    (M0: replica vs the benchmark's FAISS agree at Kendall tau 1.0000 on 400/400
    pairs), so with identical vectors this reproduces either. ``argsort`` is
    stable, so ties resolve deterministically by chunk index.
    """
    sims = np.asarray(query_vecs, dtype=np.float64) @ np.asarray(
        chunk_vecs, dtype=np.float64).T
    return [list(np.argsort(-row, kind="stable")[:top_k]) for row in sims]


def compare_pages(a, b) -> dict:
    """Agreement between two page selections, set-wise and order-wise."""
    same_set = sum(1 for x, y in zip(a, b) if set(x) == set(y))
    same_order = sum(1 for x, y in zip(a, b) if list(x) == list(y))
    same_top1 = sum(1 for x, y in zip(a, b) if x[:1] == y[:1])
    jac = []
    for x, y in zip(a, b):
        sx, sy = set(x), set(y)
        jac.append(len(sx & sy) / len(sx | sy) if (sx | sy) else 1.0)
    return {"n": len(a), "same_set": same_set, "same_order": same_order,
            "same_top1": same_top1,
            "set_agreement": same_set / len(a) if a else None,
            "order_agreement": same_order / len(a) if a else None,
            "mean_jaccard": float(np.mean(jac)) if jac else None}


# ── encoders ─────────────────────────────────────────────────────────────────
def free() -> None:
    """Collect and release the CUDA caching allocator.

    Callers must NULL their references first — ``del`` on a parameter only drops
    the callee's binding, which would leave the ~17 GB of weights alive and make
    the second model OOM on a card that has room for exactly one.
    """
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def hnav_encode(cfg, payload, max_length: int, persist: bool) -> dict:
    """H-Nav's own embedder, writing into the ``L{max_length}`` namespace."""
    from hnav.core.embedding import HFEmbedder
    inner = HFEmbedder(model_name=cfg.embed_model, device=0,
                       dtype=cfg.embed_dtype, batch=cfg.embed_batch,
                       max_length=max_length)
    emb = DiskCachedEmbedder(inner, cfg.emb_cache_dir,
                             cache_key(cfg.embed_model, cfg.embed_dtype,
                                       max_length),
                             persist=persist)
    out = {}
    for name, blob in payload.items():
        out[name] = {k: emb.encode(v) for k, v in blob.items()}
        print(f"   {name}: chunks {len(blob['chunks'])}, facts {len(blob['facts'])}, "
              f"queries {len(blob['queries'])}", flush=True)
    stats = {"n_hits": emb.n_hits, "n_misses": emb.n_misses,
             "max_length": max_length, "dtype": cfg.embed_dtype,
             "namespace": emb.key}
    emb.inner = None
    inner.model = None
    del emb, inner
    free()
    return {"vectors": out, "stats": stats}


def benchmark_encode(payload) -> dict:
    """The BENCHMARK's own embedding class, driven over the same texts.

    Imported from the benchmark tree rather than transcribed — a transcription
    would prove only that two copies of the same code agree. Heavy imports stay
    inside this function so importing this module costs nothing
    (``test_no_torch_at_import.py``).
    """
    if str(BENCH) not in sys.path:
        sys.path.insert(0, str(BENCH))
    from methods.embedding_retriever import \
        Qwen3Embedding4BEmbeddings  # noqa: PLC0415

    enc = Qwen3Embedding4BEmbeddings()
    out = {}
    for name, blob in payload.items():
        out[name] = {
            "chunks": np.asarray(enc.embed_documents(blob["chunks"]),
                                 dtype=np.float32),
            "queries": np.asarray([enc.embed_query(q) for q in blob["queries"]],
                                  dtype=np.float32),
        }
        print(f"   {name}: benchmark-encoded {len(blob['chunks'])} chunks, "
              f"{len(blob['queries'])} queries", flush=True)
    tok_limit = int(getattr(enc.tokenizer, "model_max_length", 0))
    enc.model = None
    del enc
    free()
    return {"vectors": out, "tokenizer_model_max_length": tok_limit}


def legacy_chunk_vectors(cfg, payload) -> dict:
    """The stale 512-truncated vectors, read from the legacy namespace.

    Read-only and miss-intolerant: a miss would mean the comparison is against
    something other than what the committed prepasses actually used.
    """
    class _FailOnMiss:
        dim = 0

        def encode(self, texts):
            raise SystemExit(
                f" REFUSED: {len(texts)} text(s) absent from the legacy "
                f"namespace, first={texts[0][:60]!r}. The 'before' side of the "
                "comparison would not be the deployed status quo.")

    emb = DiskCachedEmbedder(_FailOnMiss(), cfg.emb_cache_dir, LEGACY_KEY,
                             persist=False)
    return {name: {"chunks": emb.encode(blob["chunks"]),
                   "queries": emb.encode(blob["queries"])}
            for name, blob in payload.items()}


# ── analysis ─────────────────────────────────────────────────────────────────
def vector_agreement(a: np.ndarray, b: np.ndarray) -> dict:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    cos = np.sum(a * b, axis=1) / (np.linalg.norm(a, axis=1)
                                   * np.linalg.norm(b, axis=1))
    dev = 1.0 - cos
    return {"n": int(a.shape[0]), "min_cosine": float(cos.min()),
            "mean_cosine": float(cos.mean()),
            "max_deviation": float(dev.max())}


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--subsets", nargs="*",
                    default=["sh_6k", "sh_32k", "sh_64k"])
    ap.add_argument("--max-length", type=int, default=8192)
    ap.add_argument("--top-k", type=int, default=TOP_K)
    ap.add_argument("--dry-run", action="store_true",
                    help="report the plan and the chunk inventory; load nothing")
    ap.add_argument("--no-benchmark-check", action="store_true",
                    help="skip the fidelity half. Then the run establishes "
                         "freshness only and MUST NOT be cited as fidelity.")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    cfg = _config.get_config()
    if "sh_262k" in args.subsets:
        print(" REFUSED: sh_262k is outside the campaign (pre-registration v2 "
              "section 2) and re-embedding 18,332 facts is not free.")
        return 2

    payload = load_subsets(args.subsets)
    print("=" * 92)
    print(" CHUNK EMBEDDING REFIT — inventory")
    print("=" * 92)
    for name, blob in payload.items():
        print(f"  {name:9s} chunks={len(blob['chunks']):3d} "
              f"facts={len(blob['facts']):5d} queries={len(blob['queries']):3d}")
    print(f"  legacy namespace (kept):  {LEGACY_KEY}")
    print(f"  new namespace (written):  "
          f"{cache_key(cfg.embed_model, cfg.embed_dtype, args.max_length)}")
    if args.dry_run:
        print("\n --dry-run: nothing loaded.")
        return 0

    print("\n[1/3] H-Nav embedder at max_length="
          f"{args.max_length}, dtype={cfg.embed_dtype} ...", flush=True)
    fresh = hnav_encode(cfg, payload, args.max_length, persist=True)

    print("\n[2/3] legacy 512-namespace vectors (read-only) ...", flush=True)
    legacy = legacy_chunk_vectors(cfg, payload)

    bench = None
    if not args.no_benchmark_check:
        print("\n[3/3] the BENCHMARK's own embedding class ...", flush=True)
        bench = benchmark_encode(payload)

    results = {}
    for name in payload:
        f = fresh["vectors"][name]
        pages_fresh = rank_pages(f["chunks"], f["queries"], args.top_k)
        pages_legacy = rank_pages(legacy[name]["chunks"], legacy[name]["queries"],
                                  args.top_k)
        row = {
            "n_chunks": len(payload[name]["chunks"]),
            "n_queries": len(payload[name]["queries"]),
            "retrieval_complete": len(payload[name]["chunks"]) <= args.top_k,
            "page_L8192_hnav_vs_L512_hnav": compare_pages(pages_fresh, pages_legacy),
        }
        if bench is not None:
            b = bench["vectors"][name]
            pages_bench = rank_pages(b["chunks"], b["queries"], args.top_k)
            row["vector_agreement_chunks"] = vector_agreement(f["chunks"], b["chunks"])
            row["vector_agreement_queries"] = vector_agreement(f["queries"], b["queries"])
            row["page_L8192_hnav_vs_benchmark"] = compare_pages(pages_fresh, pages_bench)
            row["page_benchmark_vs_L512_hnav"] = compare_pages(pages_bench, pages_legacy)
            row["chunk_agreement_L512_vs_benchmark"] = vector_agreement(
                legacy[name]["chunks"], b["chunks"])
        results[name] = row

    # Facts must be INVARIANT to the length change — they are one short sentence.
    # If that holds, the frozen operating point and every committed detection
    # number carry over to the new namespace untouched.
    fact_check = {}
    for name in payload:
        try:
            old = legacy_chunk_vectors(cfg, {name: {"chunks": payload[name]["facts"],
                                                    "queries": []}})[name]["chunks"]
        except SystemExit:
            fact_check[name] = {"status": "legacy facts absent"}
            continue
        fact_check[name] = vector_agreement(fresh["vectors"][name]["facts"], old)
        fact_check[name]["identical_within_tolerance"] = bool(
            fact_check[name]["max_deviation"] <= COS_TOL)

    payload_out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head": _git_head(),
        "purpose": ("re-embed memorize chunks at the corrected max_length and "
                    "prove the resulting page is the benchmark's own"),
        "namespaces": {"legacy_kept": LEGACY_KEY,
                       "written": fresh["stats"]["namespace"]},
        "embedder": fresh["stats"],
        "benchmark_tokenizer_model_max_length":
            None if bench is None else bench["tokenizer_model_max_length"],
        "top_k": args.top_k,
        "cos_tolerance": COS_TOL,
        "fact_vector_invariance": fact_check,
        "subsets": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload_out, indent=2), encoding="utf-8")

    print("\n" + "=" * 92)
    print(" RESULT")
    print("=" * 92)
    for name, row in results.items():
        print(f"\n {name}  ({row['n_chunks']} chunks, retrieval "
              f"{'complete' if row['retrieval_complete'] else 'INCOMPLETE'})")
        if "vector_agreement_chunks" in row:
            v = row["vector_agreement_chunks"]
            print(f"   chunk vectors vs BENCHMARK class: min cos {v['min_cosine']:.8f} "
                  f"(max deviation {v['max_deviation']:.2e})")
            q = row["vector_agreement_queries"]
            print(f"   query vectors vs BENCHMARK class: min cos {q['min_cosine']:.8f}")
            o = row["chunk_agreement_L512_vs_benchmark"]
            print(f"   OLD 512 chunk vectors vs benchmark: min cos "
                  f"{o['min_cosine']:.6f}  <- the defect, measured")
            p = row["page_L8192_hnav_vs_benchmark"]
            print(f"   PAGE fidelity (L8192 vs benchmark): set {p['same_set']}/{p['n']}, "
                  f"order {p['same_order']}/{p['n']}")
        p = row["page_L8192_hnav_vs_L512_hnav"]
        print(f"   page change vs the stale vectors: set {p['same_set']}/{p['n']} "
              f"identical, mean Jaccard {p['mean_jaccard']:.4f}")
    print(f"\n fact-vector invariance (short texts, must be identical):")
    for name, fc in fact_check.items():
        if "max_deviation" in fc:
            print(f"   {name}: max deviation {fc['max_deviation']:.2e} -> "
                  f"{'IDENTICAL' if fc['identical_within_tolerance'] else 'DIFFERS'}")
        else:
            print(f"   {name}: {fc['status']}")
    print(f"\n wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
