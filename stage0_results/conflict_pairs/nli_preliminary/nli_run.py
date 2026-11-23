"""Score sentence pairs with a locally cached MNLI model, both directions. Offline only.

usage: python -I nli_run.py <pkgs_dir> <pairs.json> <out.json>
pairs.json: [{"id": ..., "a": ..., "b": ...}, ...]
out.json:   {id: {"ab": [contradiction, neutral, entailment], "ba": [...]}}
"""
import json
import os
import sys

pkgs, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, pkgs)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402
from transformers import AutoModelForSequenceClassification, AutoTokenizer  # noqa: E402

MODEL = "microsoft/deberta-large-mnli"
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()
assert model.config.id2label[0] == "CONTRADICTION" and model.config.id2label[2] == "ENTAILMENT"

pairs = json.load(open(src, encoding="utf-8"))
out = {}
BATCH = 32
torch.set_num_threads(max(1, (os.cpu_count() or 4) - 2))


def score(prem, hyp):
    res = []
    for i in range(0, len(prem), BATCH):
        enc = tok(prem[i:i + BATCH], hyp[i:i + BATCH], return_tensors="pt", padding=True,
                  truncation=True, max_length=256)
        with torch.no_grad():
            p = torch.softmax(model(**enc).logits, dim=-1)
        res += [[round(float(x), 4) for x in row] for row in p]
        print(f"{min(i + BATCH, len(prem))}/{len(prem)}", flush=True)
    return res


a = [p["a"] for p in pairs]
b = [p["b"] for p in pairs]
ab, ba = score(a, b), score(b, a)
for p, x, y in zip(pairs, ab, ba):
    out[p["id"]] = {"ab": x, "ba": y}
json.dump(out, open(dst, "w", encoding="utf-8"))
print("done", len(out))
