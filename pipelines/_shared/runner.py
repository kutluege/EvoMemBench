#!/usr/bin/env python3
"""Shared engine for the two frozen H-Nav pipelines.  [thin runner]

This module contains NO detection logic. Everything scientific lives in
``hnav/`` and stays covered by its test suite; a pipeline folder is a frozen
*configuration* — which geometry space, which operating-point artifact, which
subsets — plus this driver, which:

  1. verifies the frozen artifacts are byte-identical to what the campaign
     committed (sha256 pinned in ``pipeline.json``; for ABTT also the
     whitening fingerprint) — a silently re-frozen threshold would change the
     method while keeping its name;
  2. verifies the per-subset prepasses exist for the right geometry space
     (they are LLM-independent and are built once per subset, not per model);
  3. runs ``hnav/stage1/detector_gap.py`` once per subset against the
     answering model given on the command line (``HNAV_LLM_BASE_URL`` /
     ``HNAV_LLM_MODEL`` in the child environment; sh_64k gets a dry-run first
     and then ``--confirmatory``, exactly like the campaign);
  4. writes one results folder per model with the raw artifacts, a manifest,
     and a stratified Markdown report.

The embedding model is FROZEN at Qwen/Qwen3-Embedding-4B fp32 L8192. Swapping
the embedder invalidates every threshold and the whitening artifact (G1
measured that they do not transfer) and is deliberately out of scope here.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.config import get_config                                     # noqa: E402
from hnav.stage1.stale_suppression_probe import mcnemar_exact_p        # noqa: E402

MECHANISM = "detector_suppress"          # the shipped mechanism; others are logged
ALLOWED_SUBSETS = ("sh_6k", "sh_32k", "sh_64k")
SUBSET_ROLE = {"sh_6k": "calibration split", "sh_32k": "calibration split",
               "sh_64k": "held-out"}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_tag(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("_")


def load_pipeline(pipeline_dir: pathlib.Path) -> dict:
    spec = json.loads((pipeline_dir / "pipeline.json").read_text(encoding="utf-8"))
    spec["_dir"] = pipeline_dir
    return spec


# ── guards ───────────────────────────────────────────────────────────────────
def verify_frozen(spec: dict) -> list[str]:
    """Every check that must hold BEFORE any call is spent. Returns problems."""
    bad: list[str] = []
    op = REPO / spec["operating_point"]
    if not op.exists():
        return [f"operating point missing: {spec['operating_point']}"]
    got = sha256(op)
    if got != spec["operating_point_sha256"]:
        bad.append(
            f"operating point {spec['operating_point']} was MODIFIED since this "
            f"pipeline was frozen (sha256 {got[:12]}… != pinned "
            f"{spec['operating_point_sha256'][:12]}…). If the change is "
            f"deliberate, re-pin the hash in pipeline.json in the same commit.")
    art = json.loads(op.read_text(encoding="utf-8"))
    space = art.get("provenance", {}).get("geometry_space", "raw")
    if space != spec["geometry_space"]:
        bad.append(f"operating point is for geometry '{space}', pipeline says "
                   f"'{spec['geometry_space']}'")
    if spec["geometry_space"] == "abtt":
        wa = REPO / spec["whitening_artifact"]
        if not wa.exists():
            bad.append(f"whitening artifact missing: {spec['whitening_artifact']}")
        else:
            fp = json.loads(wa.read_text(encoding="utf-8"))["whitening"]["fingerprint"]
            if fp != spec["whitening_fingerprint"]:
                bad.append("whitening artifact fingerprint mismatch: "
                           f"{fp[:12]}… != pinned {spec['whitening_fingerprint'][:12]}…")
            op_fp = art.get("provenance", {}).get("whitening_fingerprint")
            if op_fp != spec["whitening_fingerprint"]:
                bad.append("operating point was frozen against a DIFFERENT "
                           f"whitening ({str(op_fp)[:12]}…)")
    cfg = get_config()
    if cfg.mode == "live":
        bad.append("HNAV_MODE=live is refused for pipeline runs")
    if cfg.embed_model != spec["embed_model"]:
        bad.append(f"HNAV_EMBED_MODEL={cfg.embed_model!r} but this pipeline's "
                   f"thresholds are only valid for {spec['embed_model']!r}. "
                   f"A new embedder needs a new calibration campaign, not this runner.")
    return bad


def prepass_file(cfg, subset: str, space: str) -> pathlib.Path:
    suffix = "_benchmarkpage" + ("_abtt" if space == "abtt" else "")
    return cfg.out_dir / f"stage1_prepass_{subset}{suffix}.json"


def verify_prepasses(spec: dict, subsets: list[str]) -> list[str]:
    cfg = get_config()
    bad = []
    for s in subsets:
        p = prepass_file(cfg, s, spec["geometry_space"])
        if not p.exists():
            extra = (f" --geometry-space abtt --whitening-artifact "
                     f"{spec['whitening_artifact']}"
                     if spec["geometry_space"] == "abtt" else "")
            bad.append(
                f"prepass missing for {s}: {p}\n"
                f"    build it ONCE (LLM-independent, reused for every model):\n"
                f"    python hnav/stage1/confirmatory_prepass.py --subset {s}"
                f"{extra}")
    return bad


# ── execution ────────────────────────────────────────────────────────────────
def detector_gap_cmd(spec: dict, subset: str, out: pathlib.Path,
                     dry_run: bool, smoke: bool) -> list[str]:
    cmd = [sys.executable, str(REPO / "hnav/stage1/detector_gap.py"),
           "--subsets", subset, "--harness", "retrieval",
           "--page-source", "benchmark", "--out", str(out)]
    if spec["geometry_space"] == "abtt":
        cmd += ["--geometry-space", "abtt",
                "--whitening-artifact", str(REPO / spec["whitening_artifact"])]
    if subset == "sh_64k":
        cmd.append("--confirmatory")
    if dry_run:
        cmd.append("--dry-run")
    if smoke:
        cmd.append("--smoke-llm")
    return cmd


def run_subset(spec: dict, subset: str, outdir: pathlib.Path, env: dict,
               dry_run: bool, smoke: bool) -> pathlib.Path:
    out = outdir / f"detector_gap_{subset}.json"
    if subset == "sh_64k" and not (dry_run or smoke):
        # the campaign discipline: budget + guard pre-flight before firing
        pre = subprocess.run(detector_gap_cmd(spec, subset, out, True, False),
                             cwd=REPO, env=env, capture_output=True, text=True)
        (outdir / "sh_64k_dryrun.log").write_text(pre.stdout + pre.stderr,
                                                  encoding="utf-8")
        if pre.returncode != 0:
            raise SystemExit(f"sh_64k dry-run failed (rc={pre.returncode}) — "
                             f"see {outdir / 'sh_64k_dryrun.log'}")
    r = subprocess.run(detector_gap_cmd(spec, subset, out, dry_run, smoke),
                       cwd=REPO, env=env)
    if r.returncode != 0:
        raise SystemExit(f"detector_gap failed on {subset} (rc={r.returncode})")
    return out


# ── analysis ─────────────────────────────────────────────────────────────────
def stratum_flags(res: dict, stratum: str, arm: str):
    out = []
    for q in res["per_question"]:
        if stratum == "all" or q["stratum"] == stratum:
            out.append(bool(q["arms"][arm]["correct"]))
    return out


def analyse_artifact(path: pathlib.Path) -> dict:
    art = json.loads(path.read_text(encoding="utf-8"))
    res = art["results"][0]
    fails = []
    for k in ("n_page_edit_mismatch", "n_containment_violations",
              "n_page_edit_errors"):
        if res.get(k, 0):
            fails.append(f"{k}={res[k]}")
    if not res["positive_control"]["ok"]:
        fails.append("positive control did not fire")
    aa = res["aa_floor"]
    if aa["b_native_only"] + aa["c_arm_only"] != 0:
        fails.append(f"A/A floor non-zero: {aa}")
    rows = {}
    for st in ("all", "conflicted", "unique"):
        nat = stratum_flags(res, st, "native")
        arm = stratum_flags(res, st, MECHANISM)
        if not nat:
            continue
        b = sum(1 for x, y in zip(nat, arm) if x and not y)
        c = sum(1 for x, y in zip(nat, arm) if y and not x)
        rows[st] = {"n": len(nat), "native": sum(nat), "hnav": sum(arm),
                    "net": c - b, "mcnemar_p": mcnemar_exact_p(b, c)}
    tok = res.get("tokens", {}).get(MECHANISM, {})
    return {"subset": res["subset"], "rows": rows, "void": fails,
            "aa_discordant": aa["b_native_only"] + aa["c_arm_only"],
            "token_delta_pct": tok.get("delta_pct"),
            "harm": res.get("harm", {}).get(MECHANISM, {})}


def write_report(spec: dict, outdir: pathlib.Path, analysed: list[dict],
                 manifest: dict) -> pathlib.Path:
    L = [f"# {spec['name']} — {manifest['llm_model']}", "",
         f"Run {manifest['started_utc']} · git `{manifest['git_head'][:12]}` · "
         f"endpoint `{manifest['llm_base_url']}` · mechanism `{MECHANISM}`",
         "",
         "| subset | role | stratum | n | native | H-Nav | net | McNemar p |",
         "|---|---|---|---|---|---|---|---|"]
    for a in analysed:
        for st, r in a["rows"].items():
            L.append(f"| {a['subset']} | {SUBSET_ROLE.get(a['subset'], '')} | {st} "
                     f"| {r['n']} | {r['native']} | {r['hnav']} | {r['net']:+d} "
                     f"| {r['mcnemar_p']:.4g} |")
    L += ["", "## Guards", ""]
    for a in analysed:
        state = "VALID" if not a["void"] else "VOID: " + "; ".join(a["void"])
        L.append(f"- `{a['subset']}`: {state} · A/A discordant {a['aa_discordant']} "
                 f"· token Δ {a['token_delta_pct']}% · harm {json.dumps(a['harm'])}")
    L += ["",
          "Strata from `stage0_results/question_strata.json` (parse-derived, "
          "model-independent). The conflicted stratum is the primary endpoint; "
          "the unique stratum is the do-no-harm check. Subsets are reported "
          "separately and are never pooled. One shot per model per subset: a "
          "void is reported, not re-rolled."]
    p = outdir / "REPORT.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ── entry point ──────────────────────────────────────────────────────────────
def main(pipeline_dir: pathlib.Path) -> int:
    spec = load_pipeline(pipeline_dir)
    ap = argparse.ArgumentParser(
        description=f"Run the frozen {spec['name']} pipeline against a new "
                    f"answering model.")
    ap.add_argument("--llm-model", required=True,
                    help="model name as served (e.g. Qwen/Qwen3-4B-Instruct-2507)")
    ap.add_argument("--llm-base-url", default="http://localhost:8003/v1")
    ap.add_argument("--subsets", nargs="+", default=list(spec["subsets"]),
                    choices=ALLOWED_SUBSETS)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact call budget per subset; send nothing")
    ap.add_argument("--smoke-llm", action="store_true",
                    help="plumbing test with the deterministic stub; writes "
                         "*_SMOKE.json, numbers meaningless")
    ap.add_argument("--tag", default=None,
                    help="results folder name (default: model tag + date)")
    args = ap.parse_args()

    problems = verify_frozen(spec) + verify_prepasses(spec, args.subsets)
    if problems:
        print("REFUSED — fix these first:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 2

    tag = args.tag or f"{model_tag(args.llm_model)}_{_dt.date.today().isoformat()}"
    outdir = pipeline_dir / "results" / tag
    if outdir.exists() and any(outdir.glob("detector_gap_*.json")) \
            and not (args.dry_run or args.smoke_llm):
        print(f"REFUSED: {outdir} already holds results. One shot per model — "
              f"use a different --tag only if this is genuinely a new "
              f"experiment, and say so in the thesis.", file=sys.stderr)
        return 2
    outdir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ,
               HNAV_LLM_MODEL=args.llm_model,
               HNAV_LLM_BASE_URL=args.llm_base_url,
               PYTHONIOENCODING="utf-8")
    manifest = {"pipeline": spec["name"], "geometry_space": spec["geometry_space"],
                "llm_model": args.llm_model, "llm_base_url": args.llm_base_url,
                "subsets": args.subsets, "mechanism": MECHANISM,
                "operating_point_sha256": spec["operating_point_sha256"],
                "embed_model": spec["embed_model"],
                "started_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                           capture_output=True, text=True
                                           ).stdout.strip(),
                "dry_run": args.dry_run, "smoke_llm": args.smoke_llm}
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=1),
                                              encoding="utf-8")

    arts = []
    for s in args.subsets:
        print(f"\n=== {spec['name']} · {s} ({SUBSET_ROLE[s]}) ===")
        arts.append(run_subset(spec, s, outdir, env, args.dry_run, args.smoke_llm))
    if args.dry_run:
        print("\ndry run complete — no calls were sent, no results were written")
        return 0

    analysed = [analyse_artifact(p) for p in arts if p.exists()]
    report = write_report(spec, outdir, analysed, manifest)
    print(f"\nreport: {report}")
    for a in analysed:
        c = a["rows"].get("conflicted", {})
        print(f"  {a['subset']:7s} conflicted {c.get('native')}→{c.get('hnav')}"
              f"/{c.get('n')}  {'VALID' if not a['void'] else 'VOID'}")
    return 0
