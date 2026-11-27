import re

files = [
    r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site\smt1\struktur-data.html",
    r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site\smt2\basis-data.html",
    r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site\smt2\proses-bisnis.html",
    r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site\smt2\komunikasi-bisnis-teknis.html",
    r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site\smt2\analisis-visualisasi-data.html",
]

for f in files:
    s = open(f, encoding="utf-8").read()
    js_vars = re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*\[", s)
    q_items = len(re.findall(r"q-item", s))
    data_opts = len(re.findall(r"data-options", s))
    print(f.split("\\")[-1], "js_vars=", js_vars, "q-item=", q_items, "data-options=", data_opts)
    m = re.search(r"<section[^>]*(?:quiz|pg)[^>]*>(.*?)</section>", s, re.I | re.S)
    if m:
        print("  quiz sample:", m.group(1)[:300].replace("\n", " "))

