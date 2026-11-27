import glob
import json
import os

ROOT = r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\belajar-ut-astro"
DATA_DIR = os.path.join(ROOT, "src", "data", "courses")
OUT_PATH = os.path.join(ROOT, "public", "search-index.json")

search_index = []
for smt in (1, 2):
    for fpath in sorted(glob.glob(os.path.join(DATA_DIR, f"smt{smt}", "*.json"))):
        d = json.load(open(fpath, "r", encoding="utf-8"))
        search_index.append({
            "type": "Matkul",
            "semester": smt,
            "course": d["shortLabel"],
            "title": d["h1"],
            "snippet": d["coverDesc"][:160],
            "url": d["url"],
            "keywords": f"semester {smt} smt{smt} {d['shortLabel']} {d['h1']}".lower(),
        })
        for s in d["sections"]:
            search_index.append({
                "type": "Materi" if s["id"].startswith("m") else "Ahli/Ref",
                "semester": smt,
                "course": d["shortLabel"],
                "title": s["title"],
                "snippet": s["text"][:160],
                "url": f"{d['url']}#{s['id']}",
                "keywords": f"{d['shortLabel']} {s['title']} {s['text'][:500]}".lower(),
            })
        for q in d["pgQuestions"]:
            search_index.append({
                "type": "Soal PG",
                "semester": smt,
                "course": d["shortLabel"],
                "title": q["question"][:110],
                "snippet": f"Kunci: {q['answerLetter']} — {q['explanation'][:100]}",
                "url": f"{d['url']}#quiz-pg",
                "keywords": f"{d['shortLabel']} {q['question']} {q['explanation']}".lower(),
            })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(search_index, f, ensure_ascii=False)
print("Total search index entries:", len(search_index))
