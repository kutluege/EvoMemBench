#!/usr/bin/env python3
"""Per-model preflight gate for the multi-model campaign.  [E2E-5]

Runs BEFORE any of the 4,500 completions a model costs, and refuses the model
rather than let it produce a number that looks valid and is not.

Why each check exists — every one of these is a way a substituted answering
model silently ruins the experiment:

1. ``served_name``   vLLM advertises whatever ``--served-model-name`` says. Get
                     it wrong and the artifacts carry the *reference* model's
                     name; nothing downstream would ever notice.
2. ``prompt_fits``   The frozen harness sends the benchmark's own RAG prompt —
                     up to 169,810 characters on sh_64k. Tokens per character
                     differ per tokenizer, so "42.5k tokens" is a Qwen fact,
                     not a universal one. This measures the real longest prompt
                     with THIS model's tokenizer. A prompt over the served
                     context aborts mid-campaign with an API error.
3. ``generates``     The longest prompt, through the exact harness call.
4. ``no_reasoning``  ``GENERATION_MAX_TOKENS = 10`` (the benchmark's own
                     ``generation_max_length``). A thinking model spends all ten
                     tokens thinking and scores ~0 — a model-capability claim
                     that is really a serving-mode artifact. Serve such models
                     non-thinking, or exclude them; never report the 0.
5. ``deterministic`` The same prompt twice must give the same string. The
                     campaign's A/A floor (native vs native_repeat) must be 0
                     discordant or the run is void; catching non-determinism
                     here costs one call instead of 1,500.
6. ``short_prompt``  An sh_6k question end-to-end, so a failure that only shows
                     on small contexts is caught too.
7. ``one_shot``      No results folder for this model may exist yet.

Tool-call formatting is deliberately NOT checked: this benchmark is plain
question answering, the harness never sends a ``tools`` array, and no tool-call
parser is enabled for any model. Enabling one could only add a parse failure
mode. That is recorded in the preflight record rather than left implicit.

Usage:
    python hnav/deploy/preflight_model.py --model-key phi4_mini \
        --model-path /mnt/nvmes/nvme1/models/Phi-4-mini-instruct \
        --served-name microsoft/Phi-4-mini-instruct \
        --base-url http://localhost:8003/v1
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import types

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hnav.config import get_config                                     # noqa: E402
from hnav.stage1.calibrate_read_policy import (GENERATION_MAX_TOKENS,  # noqa: E402
                                               SYSTEM_MESSAGE)

ARMS_DIRS = ("hnav_raw", "hnav_idonly", "hnav_geo")
# The reasoning markers a chat model may emit into `content` when it is served
# in thinking mode. Any of them means the ten-token budget is being spent on
# reasoning, not on the answer.
THINK_MARKERS = ("<think>", "</think>", "<reasoning>", "<|thinking|>",
                 "<seed:think>", "◁think▷")


def _plan(subset: str) -> dict:
    """The REAL plan for one subset, built through the campaign's own code —
    not a reimplementation. Uses the parser cell, whose native prompts are the
    longest arm and are operating-point independent."""
    from hnav.stage1.detector_gap import (ReplayNLI, decide_all,  # noqa: PLC0415
                                          frozen_cell, load_context,
                                          plan_subset)
    cfg = get_config()
    args = types.SimpleNamespace(
        page_source="benchmark", geometry_space="raw", prepass_tag="",
        allow_unstamped_prepass=False, _whitener=None, _ces=None,
        harness="retrieval", max_questions=None, pair_screen="parser",
        operating_point=None, subsets=[subset])
    ctx = load_context(cfg, [subset], args)
    cell = frozen_cell("raw", "parser")
    pp, table, recs = (ctx["prepasses"][subset], ctx["tables"][subset],
                       ctx["records"][subset])
    decisions = decide_all(pp, recs, [cell], ReplayNLI(pp["nli_table"]), None)
    return plan_subset(ctx["items"][subset], subset, pp, decisions, 0, table,
                       None, harness="retrieval", page_source="benchmark")


def longest_prompt(plan: dict) -> tuple[str, int]:
    best, n = "", 0
    for q in plan["questions"]:
        for arm in q["arms"].values():
            p = arm["prompt"]
            if len(p) > n:
                best, n = p, len(p)
    return best, n


def count_tokens(model_path: str, prompt: str) -> dict:
    """Tokens for the full chat-formatted request, with this model's own
    tokenizer. Falls back to raw encoding plus a template allowance if the
    installed transformers cannot render the model's chat template."""
    from transformers import AutoTokenizer                    # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
    msgs = [{"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}]
    try:
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      tokenize=True)
        return {"n_tokens": len(ids), "method": "apply_chat_template",
                "exact": True}
    except Exception as exc:                                  # noqa: BLE001
        # Some templates reject a system turn; merging it into the user turn is
        # what those templates do internally anyway, so the count stays honest.
        try:
            ids = tok.apply_chat_template(
                [{"role": "user", "content": SYSTEM_MESSAGE + "\n\n" + prompt}],
                add_generation_prompt=True, tokenize=True)
            return {"n_tokens": len(ids), "method": "chat_template_merged_system",
                    "exact": True, "note": str(exc)[:200]}
        except Exception as exc2:                             # noqa: BLE001
            body = len(tok.encode(SYSTEM_MESSAGE + "\n\n" + prompt))
            return {"n_tokens": body + 64, "method": "raw_encode_plus_64",
                    "exact": False, "note": f"{str(exc)[:120]} | {str(exc2)[:120]}"}


def ask(client, model: str, prompt: str) -> dict:
    """The EXACT call the harness makes — same messages, temperature and
    max_tokens. Anything else here would preflight a different experiment."""
    cfg = get_config()
    t0 = time.time()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_MESSAGE},
                  {"role": "user", "content": prompt}],
        temperature=cfg.llm_temperature, max_tokens=GENERATION_MAX_TOKENS)
    msg = resp.choices[0].message
    return {"content": msg.content or "",
            "reasoning_content": getattr(msg, "reasoning_content", None) or "",
            "finish_reason": resp.choices[0].finish_reason,
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "latency_s": round(time.time() - t0, 2)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-key", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--served-name", required=True)
    ap.add_argument("--base-url", default="http://localhost:8003/v1")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-token-count", action="store_true",
                    help="advisory only; the served endpoint still reports its "
                         "own prompt_tokens for the longest prompt")
    args = ap.parse_args(argv)

    cfg = get_config()
    rec: dict = {"model_key": args.model_key, "model_path": args.model_path,
                 "served_name": args.served_name, "base_url": args.base_url,
                 "harness": {"system_message": SYSTEM_MESSAGE,
                             "max_tokens": GENERATION_MAX_TOKENS,
                             "temperature": cfg.llm_temperature,
                             "sends_tools": False,
                             "tool_parser_enabled": False,
                             "tool_check": "N/A - this benchmark is plain QA; "
                                           "the harness never sends a tools "
                                           "array, so no tool-call parser is "
                                           "enabled for any model"},
                 "checks": {}}
    checks = rec["checks"]

    def gate(name, ok, **extra):
        checks[name] = dict(ok=bool(ok), **extra)
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}"
              + ("  " + json.dumps(extra, default=str)[:220] if extra else ""))
        return bool(ok)

    print(f"== preflight {args.model_key} ==")

    # ── 7. one shot ──────────────────────────────────────────────────────────
    existing = []
    for arm in ARMS_DIRS:
        res = REPO / "pipelines" / arm / "results"
        if res.is_dir():
            existing += [str(p.relative_to(REPO).as_posix()) for p in res.iterdir()
                         if p.is_dir() and any(p.glob("detector_gap_*.json"))
                         and args.model_key.lower() in p.name.lower()]
    gate("one_shot", not existing, existing=existing)

    # ── 1. the served name ───────────────────────────────────────────────────
    from openai import OpenAI                                 # noqa: PLC0415
    client = OpenAI(base_url=args.base_url, api_key=cfg.llm_api_key)
    try:
        models = client.models.list()
        served = [m.id for m in models.data]
        ctx_len = next((getattr(m, "max_model_len", None) for m in models.data
                        if m.id == args.served_name), None)
    except Exception as exc:                                  # noqa: BLE001
        return 1 if not gate("served_name", False, error=str(exc)[:300]) else 0
    gate("served_name", args.served_name in served, served=served,
         served_max_model_len=ctx_len)

    # ── 2. does the longest real prompt fit ──────────────────────────────────
    plan = _plan("sh_64k")
    prompt64, chars = longest_prompt(plan)
    tok = ({"n_tokens": None, "method": "skipped", "exact": False}
           if args.skip_token_count else count_tokens(args.model_path, prompt64))
    budget_ok = (ctx_len is None or tok["n_tokens"] is None
                 or tok["n_tokens"] + GENERATION_MAX_TOKENS <= ctx_len)
    gate("prompt_fits", budget_ok, longest_prompt_chars=chars,
         tokens=tok, served_max_model_len=ctx_len,
         headroom=(None if (ctx_len is None or tok["n_tokens"] is None)
                   else ctx_len - tok["n_tokens"] - GENERATION_MAX_TOKENS))

    # ── 3/4/5. the longest prompt, through the harness call, twice ───────────
    try:
        a = ask(client, args.served_name, prompt64)
        b = ask(client, args.served_name, prompt64)
    except Exception as exc:                                  # noqa: BLE001
        gate("generates", False, error=str(exc)[:400])
        _write(rec, args)
        return 1
    gate("generates", bool(a["content"].strip()), output=a["content"][:120],
         finish_reason=a["finish_reason"], latency_s=a["latency_s"],
         server_prompt_tokens=a["prompt_tokens"])
    leaked = [m for m in THINK_MARKERS if m in a["content"]]
    gate("no_reasoning", not leaked and not a["reasoning_content"],
         markers=leaked, reasoning_content=a["reasoning_content"][:120])
    gate("deterministic", a["content"] == b["content"],
         first=a["content"][:80], second=b["content"][:80])

    # ── 6. a short prompt too ────────────────────────────────────────────────
    small = _plan("sh_6k")
    q0 = small["questions"][0]
    s = ask(client, args.served_name, q0["arms"]["native"]["prompt"])
    gate("short_prompt", bool(s["content"].strip()),
         output=s["content"][:120], truths=q0["truths"],
         latency_s=s["latency_s"])

    rec["ok"] = all(c["ok"] for c in checks.values())
    _write(rec, args)
    print(f"\n  PREFLIGHT {'PASSED' if rec['ok'] else 'FAILED'} "
          f"for {args.model_key}")
    return 0 if rec["ok"] else 1


def _write(rec: dict, args) -> None:
    out = pathlib.Path(args.out) if args.out else (
        get_config().out_dir / "campaign" / args.model_key / "preflight.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8",
                   newline="\n")
    print(f"  written: {out}")


if __name__ == "__main__":
    raise SystemExit(main())
