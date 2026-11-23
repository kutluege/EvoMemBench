import sys; sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib, csv
from collections import defaultdict
# my judgement grouping of the fine relations (see report); counts come from rel_stats.json written by analyse.py
here = pathlib.Path(__file__).parent
rs = json.load(open(here / "rel_stats.json", encoding="utf-8"))
A = ["was created in the country of", "died in the city of", "was born in the city of",
     "The chief executive officer of | is", "The chairperson of | is", "The name of the current head of the | government is",
     "was founded in the city of", "The name of the current head of state in | is", "The head coach of | is",
     "unparsed[The President of | is]", "unparsed[The Prime Minister of | is]", "The Governor of | is"]
A += [k for k in rs if "Attorney General" in k]
B_readme = ["The capital of | is", "The name of the current head of the | government is / unparsed[The Prime Minister of | is]"]
B_open = ["The headquarters of | is located in the city of", "is married to", "is located in the continent of",
          "The origianl broadcaster of | is", "The director of | is", "The original language of | is",
          "The original language of | is / was written in the language of"]
C = ["is a citizen of", "worked in the city of", "is employed by", "'s child is", "The univeristy where | was educated is",
     "was founded by", "was created by", "The author of | is", "was performed by", "was developed by",
     "The company that produced | is"]
D = ["is associated with the sport of", "speaks the language of", "works in the field of", "is famous for",
     "The type of music that | plays is", "The official language of | is", "plays the position of",
     "is affiliated with the religion of", "was written in the language of"]
allg = A + B_readme + B_open + C + D
assert len(set(allg)) == len(allg)
missing = set(rs) - set(allg); extra = set(allg) - set(rs)
print("unassigned", missing, "not in data", extra)
for name, g in (("A single-valued, sheet yes", A), ("B1 single-valued per README example, sheet no", B_readme),
                ("B2 single-valuedness open, sheet no", B_open), ("C multi-valued, time-bound values", C),
                ("D multi-valued, atemporal values", D)):
    ids = sum(rs[k]["ids"] for k in g); t = sum(rs[k]["texts"] for k in g); my = sum(rs[k]["model_yes_ids"] for k in g)
    myt = sum(rs[k]["model_yes_texts"] for k in g)
    print(f"{name}: relations={len(g)} ids={ids} texts={t} model_yes_ids={my} model_yes_texts={myt}")
    for k in g:
        print(f"    {k}: ids={rs[k]['ids']} texts={rs[k]['texts']}")
