import sys; sys.stdout.reconfigure(encoding='utf-8')
import csv, gzip, json, pathlib, re
from collections import Counter, defaultdict

REPO = pathlib.Path(sys.argv[1])
D = REPO / "stage0_results" / "conflict_pairs"
SR = D / "strict_review"


def relation_of(g):
    p = g.get("parser") or {}
    a = ((p.get("fact_a_parsed") or {}).get("relation") or "unparsed").strip(" |")
    b = ((p.get("fact_b_parsed") or {}).get("relation") or "unparsed").strip(" |")
    return a if a == b else " / ".join(sorted((a, b)))


# surface template for unparsed sentences: "The <office> of <X> is <Y>." -> "The <office> of | is"
OFFICE = re.compile(r"^The (.+?) of .+ is .+$")
def surface(sent):
    m = OFFICE.match(sent)
    return f"The {m.group(1)} of | is" if m else "OTHER: " + sent


def fine_rel(g):
    p = g.get("parser") or {}
    out = []
    for side, sent in (("fact_a_parsed", g["fact_a"]), ("fact_b_parsed", g["fact_b"])):
        r = ((p.get(side) or {}).get("relation") or "").strip(" |")
        out.append(r if r else "unparsed[" + surface(sent) + "]")
    a, b = out
    return a if a == b else " / ".join(sorted((a, b)))


sheet = {r["review_id"]: r for r in csv.DictReader(open(SR / "strict_sheet.filled.csv", encoding="utf-8", newline=""))}
key = json.load(open(SR / "strict_key.json", encoding="utf-8"))["rows"]
gold = [json.loads(l) for l in gzip.open(D / "gold_conflict_dataset.jsonl.gz", "rt", encoding="utf-8")]
gid = {g["pair_id"]: g for g in gold}
model = {}
for r in csv.DictReader(open(D / "model_annotation" / "MODEL_LABELS.csv", encoding="utf-8", newline="")):
    model[r["pair_id"]] = (r["update_conflict"].strip().lower() == "yes", r["strict_conflict"].strip().lower() == "yes")
print("model rows", len(model), "gold rows", len(gold), "model ids not in gold", sum(1 for p in model if p not in gid))

# ---------------- Q1 sheet per relation (coarse and fine)
print("\n== Q1 per relation (fine, unparsed split by surface template)")
sheet_rel = defaultdict(lambda: [0, 0, []])
for rid, k in key.items():
    g = gid[k["shown_pair_id"]]
    assert relation_of(g) == k["relation"], rid
    fr = fine_rel(g)
    y = sheet[rid]["strict_conflict"] == "yes"
    sheet_rel[fr][0] += 1; sheet_rel[fr][1] += y; sheet_rel[fr][2].append(rid)
for fr in sorted(sheet_rel):
    n, y, ids = sheet_rel[fr]
    print(f"  {fr!r}: n={n} yes={y} {'MIXED' if 0<y<n else ''}")
print("relations on sheet", len(sheet_rel), "mixed", sum(1 for v in sheet_rel.values() if 0 < v[1] < v[0]))
table = {fr: (v[1] == v[0]) for fr, v in sheet_rel.items() if v[1] in (0, v[0])}

# ---------------- Q6 notes
print("\n== Q6 notes")
notes = {rid: r["notes"] for rid, r in sheet.items()}
withn = [rid for rid in sorted(notes) if notes[rid].strip()]
print("rows with notes", len(withn), "without", [rid for rid in sorted(notes) if not notes[rid].strip()])
dist = Counter(notes[r] for r in withn)
print("distinct note texts", len(dist))
for t, c in dist.most_common():
    print(f"  {c:3d} x len={len(t)} | {t}")
lens = [len(notes[r]) for r in withn]
print("note length chars min/median/max", min(lens), sorted(lens)[len(lens)//2], max(lens))
nonascii = [r for r in withn if any(ord(ch) > 127 for ch in notes[r])]
print("notes with non-ASCII chars", nonascii)
tr_chars = set("çğıöşüÇĞİÖŞÜ")
print("notes with Turkish letters", [r for r in withn if set(notes[r]) & tr_chars])
refs = Counter(m for r in withn for m in re.findall(r"S\d{3}", notes[r]))
print("row ids referenced in notes", dict(refs))
print("BORDERLINE rows", [r for r in withn if "BORDERLINE" in notes[r]])
print("'conservative rule' rows", [r for r in withn if "conservative rule" in notes[r]])
# positions: first noted row; do notes referring to Sxxx point backwards or forwards
for r in withn:
    for m in re.findall(r"S\d{3}", notes[r]):
        if m >= r:
            print("  forward/self reference", r, "->", m)
first_note = withn[0]
print("first row with note", first_note, "; rows before it all noteless:", all(not notes[r].strip() for r in sorted(notes) if r < first_note))
# instruction vocabulary overlap
readme = (SR / "strict_README.md").read_text(encoding="utf-8").split("---")[0].lower()
for phrase in ["conservative", "borderline", "logically possible", "single-holder", "mutually exclusive",
               "single origin", "exactly one", "co-holders", "consistent with", "same office", "wording"]:
    print(f"  phrase {phrase!r}: in notes {sum(phrase in notes[r].lower() for r in withn)}, in README {phrase in readme}")

# ---------------- Q4 prior
print("\n== Q4 prior answers")
ch = Counter()
for rid in sorted(key):
    pr = key[rid]["prior"]
    if not pr:
        continue
    now = sheet[rid]["strict_conflict"] == "yes"
    last = pr[-1]["strict"]
    allp = [p["strict"] for p in pr]
    tag = ("same" if last == now else ("yes->no" if last else "no->yes"))
    ch[tag] += 1
    if last != now or len(set(allp)) > 1 or len(pr) > 1:
        print(f"  {rid} prior={[(p['review_id'], p['strict']) for p in pr]} now={now} rel={key[rid]['relation']}")
print(ch)
print("prior yes total", sum(1 for k in key.values() if k["prior"] and k["prior"][-1]["strict"]),
      "of", sum(1 for k in key.values() if k["prior"]))

# ---------------- Q7 consequences
print("\n== Q7 dataset")
upd = [p for p, v in model.items() if v[0]]
print("model update yes pair ids", len(upd), "model strict yes among them", sum(model[p][1] for p in upd),
      "strict yes with update no", sum(1 for p, v in model.items() if v[1] and not v[0]))
texts = defaultdict(list)
for p in upd:
    g = gid[p]
    texts[frozenset((g["fact_a"], g["fact_b"]))].append(p)
print("distinct sentence pairs", len(texts))
incons = [t for t, ps in texts.items() if len({model[p][1] for p in ps}) > 1]
print("text groups with inconsistent model strict", len(incons))
tyes = sum(1 for t, ps in texts.items() if any(model[p][1] for p in ps))
print("texts with model strict yes (any copy)", tyes)
# also: text groups where some copies have update no
mixed_upd = 0
allpairs_by_text = defaultdict(list)
for p in model:
    g = gid[p]; allpairs_by_text[frozenset((g["fact_a"], g["fact_b"]))].append(p)
for t in texts:
    if len({model[p][0] for p in allpairs_by_text[t]}) > 1: mixed_upd += 1
print("update-yes texts that have another labelled copy with update no", mixed_upd)

rel_stats = defaultdict(lambda: {"ids": 0, "texts": set(), "model_yes_ids": 0, "model_yes_texts": set()})
for p in upd:
    g = gid[p]; fr = fine_rel(g); t = frozenset((g["fact_a"], g["fact_b"]))
    s = rel_stats[fr]; s["ids"] += 1; s["texts"].add(t)
    if model[p][1]: s["model_yes_ids"] += 1; s["model_yes_texts"].add(t)

print("\n  relation | ids | texts | model yes ids | sheet table | implied yes ids | flips ids (y->n / n->y) | flips texts")
tot = Counter()
uncovered = []
for fr in sorted(rel_stats, key=lambda r: -rel_stats[r]["ids"]):
    s = rel_stats[fr]
    n, nt, my = s["ids"], len(s["texts"]), s["model_yes_ids"]
    if fr in table:
        v = table[fr]
        imp = n if v else 0
        yn = my if not v else 0
        ny = (n - my) if v else 0
        tyn = len(s["model_yes_texts"]) if not v else 0
        tny = (nt - len(s["model_yes_texts"])) if v else 0
        tot["ids"] += n; tot["texts"] += nt; tot["imp"] += imp; tot["yn"] += yn; tot["ny"] += ny
        tot["tyn"] += tyn; tot["tny"] += tny; tot["my"] += my; tot["impt"] += nt if v else 0
        print(f"  {fr} | {n} | {nt} | {my} | {'yes' if v else 'no'} | {imp} | {yn}/{ny} | {tyn}/{tny}")
    else:
        uncovered.append((fr, n, nt, my, len(s["model_yes_texts"])))
print("covered totals", dict(tot))
print("UNCOVERED by sheet:")
for u in uncovered:
    print("  ", u)
print("uncovered ids", sum(u[1] for u in uncovered), "texts", sum(u[2] for u in uncovered), "model yes ids", sum(u[3] for u in uncovered))
json.dump({fr: {"ids": s["ids"], "texts": len(s["texts"]), "model_yes_ids": s["model_yes_ids"],
                "model_yes_texts": len(s["model_yes_texts"])} for fr, s in rel_stats.items()},
          open(pathlib.Path(__file__).parent / "rel_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
