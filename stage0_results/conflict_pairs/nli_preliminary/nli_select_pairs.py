"""Select the sentence pairs of the preliminary NLI measurement of 23 November 2026.

usage: python -I nli_select_pairs.py <repo> <out_dir>
writes <out_dir>/pairs.json (id, a, b) for nli_run.py and <out_dir>/meta.json (the
same rows with relation, tier, parser flags, model labels and groups).

Exploratory, as run; no tests. Groups: every distinct sentence pair the model
annotator calls an update conflict; pairs with the same referent and relation
whose values it calls compatible; every pair a human has labelled; up to 150
evaluation-set negatives of each of three kinds (seed 20261123).
"""
import collections
import csv
import gzip
import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
repo, out = sys.argv[1], sys.argv[2]
R = repo + "/stage0_results/conflict_pairs/"
gold = {}
with gzip.open(R + "gold_conflict_dataset.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        g = json.loads(line)
        gold[g["pair_id"]] = g
model = {r["pair_id"]: r for r in csv.DictReader(
    open(R + "model_annotation/MODEL_LABELS.csv", encoding="utf-8", newline=""))}


def tk(g):
    return frozenset((g["fact_a"], g["fact_b"]))


def rel(g):
    p = g["parser"]
    a = (p.get("fact_a_parsed") or {}).get("relation")
    b = (p.get("fact_b_parsed") or {}).get("relation")
    return a if a == b else f"{a} || {b}"


items = {}


def add(pid, group):
    g = gold[pid]
    t = tk(g)
    if t in items:
        items[t]["groups"].add(group)
        return
    m = model.get(pid)
    items[t] = {"pair_id": pid, "a": g["fact_a"], "b": g["fact_b"], "relation": rel(g), "tier": g["tier"],
                "same_subject": g["parser"].get("same_subject"),
                "same_relation": g["parser"].get("same_relation"),
                "same_object": g["parser"].get("same_object"),
                "model": {c: m[c] for c in ("same_referent", "same_relation", "values_incompatible",
                                            "update_conflict", "strict_conflict")} if m else None,
                "groups": {group}}


for pid in sorted(model):
    if model[pid]["update_conflict"] == "yes":
        add(pid, "update_yes")
for pid in sorted(model):
    m = model[pid]
    if m["update_conflict"] == "no" and m["same_referent"] == "yes" and m["same_relation"] == "yes":
        add(pid, "compatible_values")
for k in json.load(open(R + "human_pilot/pilot_key.json", encoding="utf-8"))["rows"].values():
    add(k["pair_id"], "human")
for k in json.load(open(R + "disagreement_review/disagreement_key.json", encoding="utf-8"))["rows"].values():
    add(k["shown_pair_id"], "human")

rng = random.Random(20261123)
neg = sorted(p for p, g in gold.items() if g["tier"] == "negative" and g["in_eval_set"] and p in model)
rng.shuffle(neg)
kinds = collections.Counter()
for pid in neg:
    m = model[pid]
    kind = ("neg_diff_subject_same_relation" if (m["same_referent"] == "no" and m["same_relation"] == "yes")
            else "neg_same_subject_diff_relation" if (m["same_referent"] == "yes" and m["same_relation"] == "no")
            else "neg_both_differ" if (m["same_referent"] == "no" and m["same_relation"] == "no") else None)
    if kind and kinds[kind] < 150 and tk(gold[pid]) not in items:
        kinds[kind] += 1
        add(pid, kind)

rows = []
for i, v in enumerate(items.values()):
    v["id"] = f"n{i:05d}"
    v["groups"] = sorted(v["groups"])
    rows.append(v)
json.dump([{"id": v["id"], "a": v["a"], "b": v["b"]} for v in rows],
          open(out + "/pairs.json", "w", encoding="utf-8"))
json.dump(rows, open(out + "/meta.json", "w", encoding="utf-8"))
print(len(rows), collections.Counter(g for v in rows for g in v["groups"]))
