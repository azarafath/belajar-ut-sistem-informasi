import glob
import html
import json
import os
import re
import subprocess

SRC_ROOT = r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\netlify-site"
DST_ROOT = r"c:\Users\ahmad.fathoni\Herd\MAINAJA\UT SM 2\belajar-ut-astro"
DATA_DIR = os.path.join(DST_ROOT, "src", "data", "courses")
PUBLIC_DIR = os.path.join(DST_ROOT, "public")
NODE_EXE = r"C:\Users\ahmad.fathoni\.config\herd\bin\nvm\v24.11.0\node.exe"


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def extract_sections(body_html):
    sections = []
    pos = 0
    while True:
        m = re.search(r"<section\b[^>]*>", body_html[pos:], re.I)
        if not m:
            break
        start = pos + m.start()
        depth = 0
        for tm in re.finditer(r"<(/?)section\b[^>]*>", body_html[start:], re.I):
            if tm.group(1) == "/":
                depth -= 1
                if depth == 0:
                    end = start + tm.end()
                    sections.append(body_html[start:end])
                    pos = end
                    break
            else:
                depth += 1
        else:
            break
    return sections


def parse_pg_item(q_html, opts_html, ans_html, default_mod="Umum"):
    q_text = strip_tags(q_html)
    ans_text = strip_tags(ans_html)
    ans_clean = re.sub(r"^Kunci:\s*", "", ans_text, flags=re.I).strip()
    km = re.match(r"^([A-E]|Benar|Salah)\b\s*(.*)$", ans_clean, re.I)
    if km:
        letter = km.group(1).upper() if len(km.group(1)) == 1 else km.group(1).capitalize()
        expl = km.group(2).strip()
        if expl.startswith("(") and expl.endswith(")"):
            expl = expl[1:-1].strip()
    else:
        letter = ""
        expl = ans_clean

    options = []
    li_matches = re.findall(r"<li[^>]*>(.*?)</li>", opts_html, re.I | re.S)
    if li_matches:
        raw_parts = [strip_tags(x) for x in li_matches]
    else:
        raw_opt = strip_tags(opts_html)
        raw_parts = [x.strip() for x in re.split(r"\s*\|\s*|\s+(?=[A-E]\.\s)", raw_opt) if x.strip()]

    for p in raw_parts:
        om = re.match(r"^([A-E])\.\s*(.+)$", p, re.I)
        if om:
            options.append({"letter": om.group(1).upper(), "text": om.group(2).strip()})
        else:
            options.append({"letter": "", "text": p})

    mod_m = re.match(r"^\[?(M\d+)", q_text, re.I)
    mod = mod_m.group(1).upper() if mod_m else default_mod
    return {
        "module": mod,
        "question": q_text,
        "options": options,
        "answerLetter": letter,
        "explanation": expl,
    }


def extract_inline_q_items(sec_html):
    items = []
    pos = 0
    while True:
        m = re.search(r'<div\s+class=["\'][^"\']*\bq-item\b[^"\']*["\'][^>]*>', sec_html[pos:], re.I)
        if not m:
            break
        start = pos + m.start()
        depth = 0
        end = start
        for tm in re.finditer(r"<(/?)div\b[^>]*>", sec_html[start:], re.I):
            if tm.group(1) == "/":
                depth -= 1
                if depth == 0:
                    end = start + tm.end()
                    break
            else:
                depth += 1
        block = sec_html[start:end]
        pos = end

        qm = re.search(r"<strong[^>]*>(.*?)</strong>", block, re.I | re.S)
        q_html = qm.group(1) if qm else ""
        am = re.search(r'<span\s+class=["\'][^"\']*\bans-pill\b[^"\']*["\'][^>]*>(.*?)</span>', block, re.I | re.S)
        ans_html = am.group(1) if am else ""

        opts_html = ""
        um = re.search(r'<ul[^>]*>(.*?)</ul>', block, re.I | re.S)
        if um:
            opts_html = um.group(0)
        else:
            inner = block[qm.end():] if qm else block
            # First check if there is a <div> before ans-pill
            found_div = False
            for dm in re.finditer(r"<div[^>]*>(.*?)</div>", inner, re.I | re.S):
                if "ans-pill" not in dm.group(0):
                    opts_html = dm.group(1)
                    found_div = True
                    break
            if not found_div:
                # Options are raw text between </strong> and <div...ans-pill
                ans_div_m = re.search(r"<div[^>]*>.*?ans-pill", inner, re.I | re.S)
                if ans_div_m:
                    opts_html = inner[:ans_div_m.start()]

        if q_html and ans_html:
            items.append((q_html, opts_html, ans_html))
    return items


def eval_js_var(raw_html, var_name):
    # Extract script blocks and evaluate variable with node
    scripts = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", raw_html, re.I | re.S)
    for sc in scripts:
        if re.search(rf"\b(?:const|let|var)\s+{var_name}\s*=", sc):
            # Take up to the end of the array literal using bracket matching
            m = re.search(rf"\b(?:const|let|var)\s+{var_name}\s*=\s*(\[)", sc)
            if not m:
                continue
            start = m.start(1)
            code = f"const {var_name} = " + sc[start:]
            # Find matching closing bracket of the array
            in_str = None
            esc = False
            depth = 0
            end_idx = None
            for idx, ch in enumerate(sc[start:], start=start):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == in_str:
                        in_str = None
                else:
                    if ch in ("'", '"', "`"):
                        in_str = ch
                    elif ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            end_idx = idx + 1
                            break
            if end_idx:
                arr_src = sc[start:end_idx]
                res = subprocess.run(
                    [NODE_EXE, "-e", "const fs=require('fs'); const s=fs.readFileSync(0,'utf8'); const v=eval('('+s+')'); process.stdout.write(JSON.stringify(v));"],
                    input=arr_src, capture_output=True, text=True, encoding="utf-8"
                )
                if res.returncode == 0 and res.stdout:
                    return json.loads(res.stdout)
    return None


def parse_course(fpath, semester):
    slug = os.path.splitext(os.path.basename(fpath))[0]
    raw = open(fpath, "r", encoding="utf-8").read()

    title_m = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    title = html.unescape(title_m.group(1).strip()) if title_m else slug

    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', raw, re.I)
    meta_desc = html.unescape(desc_m.group(1)) if desc_m else ""

    top_span_m = re.search(r'<div class="topbar-left">.*?<span>(.*?)</span>', raw, re.I | re.S)
    short_label = strip_tags(top_span_m.group(1)) if top_span_m else title

    cover_m = re.search(r'<div class="cover">(.*?)</div>\s*<section', raw, re.I | re.S)
    cover_html = cover_m.group(1) if cover_m else ""
    hw_m = re.search(r'<div class="handwritten"[^>]*>(.*?)</div>', cover_html, re.I | re.S)
    cover_tag = strip_tags(hw_m.group(1)) if hw_m else f"Semester {semester}"
    cover_tag_color_m = re.search(r'<div class="handwritten"[^>]*style="[^"]*color:\s*([^;"]+)', cover_html, re.I)
    cover_tag_color = cover_tag_color_m.group(1).strip() if cover_tag_color_m else "#2563eb"

    h1_m = re.search(r"<h1>(.*?)</h1>", cover_html, re.I | re.S)
    h1_title = strip_tags(h1_m.group(1)) if h1_m else title

    p_m = re.search(r"<p[^>]*>(.*?)</p>", cover_html, re.I | re.S)
    cover_desc = strip_tags(p_m.group(1)) if p_m else meta_desc

    badges = []
    for bm in re.finditer(r'<span class="badge"[^>]*style="[^"]*background:\s*([^;"]+)[^"]*"[^>]*>(.*?)</span>', cover_html, re.I | re.S):
        badges.append({"bg": bm.group(1).strip(), "text": strip_tags(bm.group(2))})

    main_m = re.search(r"<main[^>]*>(.*?)</main>", raw, re.I | re.S)
    main_html = main_m.group(1) if main_m else raw
    sections = extract_sections(main_html)

    content_sections = []
    nav_items = []
    pg_questions = []
    essay_questions = []

    for sec in sections:
        id_m = re.search(r'<section[^>]*\bid=["\']([^"\']+)["\']', sec, re.I)
        sec_id = id_m.group(1) if id_m else ""

        is_quiz_sec = (
            sec_id in ("quiz", "quiz-pg", "quiz-essay", "pg", "essay")
            or 'id="tk-pg"' in sec
            or 'id="tk-essay"' in sec
            or 'id="pg-container"' in sec
            or 'id="bd-quiz"' in sec
            or 'id="pb-quiz-container"' in sec
            or 'id="kbt-quiz"' in sec
            or bool(re.search(r'class=["\'][^"\']*\bquiz-grid\b', sec))
        )

        if is_quiz_sec:
            inline_items = extract_inline_q_items(sec)
            for q_h, o_h, a_h in inline_items:
                if o_h.strip() and re.search(r"\bA\.\s", strip_tags(o_h)):
                    pg_questions.append(parse_pg_item(q_h, o_h, a_h))
                else:
                    q_t = strip_tags(q_h)
                    a_t = re.sub(r"^(?:Jawaban|Kunci):\s*", "", strip_tags(a_h), flags=re.I).strip()
                    essay_questions.append({"question": q_t, "answer": a_t})
        else:
            h2_m = re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.I | re.S)
            h2_text = strip_tags(h2_m.group(1)) if h2_m else sec_id
            clean_desc = re.sub(r"^Modul\s+\d+\s*:\s*", "", h2_text, flags=re.I)
            short = sec_id.upper() if re.match(r"^m\d+$", sec_id, re.I) else ("Ahli" if sec_id == "ahli" else "Glosarium")
            nav_items.append({"id": sec_id, "label": short, "desc": clean_desc})
            content_sections.append({
                "id": sec_id,
                "title": h2_text,
                "html": sec,
                "text": strip_tags(sec),
            })

    # Evaluate JS arrays
    for vn in ("pgList", "qs", "kbtQuestions", "pgData"):
        arr = eval_js_var(raw, vn)
        if arr:
            for row in arr:
                if isinstance(row, list) and len(row) >= 3:
                    pg_questions.append(parse_pg_item(str(row[0]), str(row[1]), str(row[2])))
                elif isinstance(row, dict) and "q" in row:
                    pg_questions.append(parse_pg_item(str(row["q"]), str(row.get("opts", "")), str(row.get("ans", ""))))

    raw_tests = eval_js_var(raw, "rawTests")
    if raw_tests:
        for grp in raw_tests:
            gtitle = grp.get("title", "")
            mm = re.search(r"Modul\s+(\d+)", gtitle, re.I)
            def_mod = f"M{mm.group(1)}" if mm else "Umum"
            for row in grp.get("items", []):
                if isinstance(row, list) and len(row) >= 3:
                    pg_questions.append(parse_pg_item(f"[{def_mod}] {row[0]}" if not str(row[0]).startswith("[M") else str(row[0]), str(row[1]), str(row[2]), def_mod))

    js_essay = eval_js_var(raw, "essayList")
    if js_essay:
        for row in js_essay:
            if isinstance(row, list) and len(row) >= 2:
                essay_questions.append({"question": strip_tags(str(row[0])), "answer": strip_tags(str(row[1]))})

    # Deduplicate PG questions
    seen_q = set()
    dedup_pg = []
    for q in pg_questions:
        key = q["question"]
        if key not in seen_q:
            seen_q.add(key)
            q["num"] = len(dedup_pg) + 1
            dedup_pg.append(q)

    for idx, eq in enumerate(essay_questions, start=1):
        eq["num"] = idx

    return {
        "slug": slug,
        "semester": semester,
        "url": f"/smt{semester}/{slug}",
        "canonical": f"https://belajar-ut.azf.my.id/smt{semester}/{slug}.html",
        "title": title,
        "shortLabel": short_label,
        "h1": h1_title,
        "metaDesc": meta_desc,
        "coverTag": cover_tag,
        "coverTagColor": cover_tag_color,
        "coverDesc": cover_desc,
        "badges": badges,
        "navItems": nav_items,
        "sections": content_sections,
        "pgQuestions": dedup_pg,
        "essayQuestions": essay_questions,
    }


def extract_catalog():
    idx_path = os.path.join(SRC_ROOT, "index.html")
    raw = open(idx_path, "r", encoding="utf-8").read()
    catalog = {"1": [], "2": []}
    for smt in ("1", "2"):
        pm = re.search(rf'<section class="semester-panel" data-semester="{smt}"[^>]*>(.*?)</section>', raw, re.I | re.S)
        if not pm:
            continue
        panel_html = pm.group(1)
        for cm in re.finditer(r"<a\s+class=['\"]course-card['\"]\s+href=['\"]([^'\"]+)['\"]>(.*?)</a>", panel_html, re.I | re.S):
            href = cm.group(1).strip()
            inner = cm.group(2)
            meta = strip_tags(re.search(r'<div class="course-meta">(.*?)</div>', inner, re.S).group(1))
            name = strip_tags(re.search(r'<h2 class="course-name">(.*?)</h2>', inner, re.S).group(1))
            desc = strip_tags(re.search(r'<p[^>]*>(.*?)</p>', inner, re.S).group(1))
            cta = strip_tags(re.search(r'<span class="cta-open">(.*?)</span>', inner, re.S).group(1))
            badges = []
            for bm in re.finditer(r'<span class="badge"[^>]*style="[^"]*background:\s*([^;"]+)[^"]*"[^>]*>(.*?)</span>', inner, re.I | re.S):
                badges.append({"bg": bm.group(1).strip(), "text": strip_tags(bm.group(2))})
            slug = href.rstrip("/").split("/")[-1]
            catalog[smt].append({
                "slug": slug,
                "href": href,
                "meta": meta,
                "name": name,
                "desc": desc,
                "badges": badges,
                "cta": cta,
            })
    return catalog


def main():
    os.makedirs(os.path.join(DATA_DIR, "smt1"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "smt2"), exist_ok=True)

    catalog = extract_catalog()
    with open(os.path.join(DST_ROOT, "src", "data", "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    search_index = []

    for smt in (1, 2):
        folder = os.path.join(SRC_ROOT, f"smt{smt}")
        for fpath in sorted(glob.glob(os.path.join(folder, "*.html"))):
            data = parse_course(fpath, smt)
            out_path = os.path.join(DATA_DIR, f"smt{smt}", f"{data['slug']}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            search_index.append({
                "type": "Matkul",
                "semester": smt,
                "course": data["shortLabel"],
                "title": data["h1"],
                "snippet": data["coverDesc"][:160],
                "url": data["url"],
                "keywords": f"semester {smt} smt{smt} {data['shortLabel']} {data['h1']}".lower(),
            })
            for sec in data["sections"]:
                search_index.append({
                    "type": "Materi" if sec["id"].startswith("m") else "Ahli/Ref",
                    "semester": smt,
                    "course": data["shortLabel"],
                    "title": sec["title"],
                    "snippet": sec["text"][:160],
                    "url": f"{data['url']}#{sec['id']}",
                    "keywords": f"{data['shortLabel']} {sec['title']} {sec['text'][:500]}".lower(),
                })
            for q in data["pgQuestions"]:
                search_index.append({
                    "type": "Soal PG",
                    "semester": smt,
                    "course": data["shortLabel"],
                    "title": q["question"][:110],
                    "snippet": f"Kunci: {q['answerLetter']} — {q['explanation'][:100]}",
                    "url": f"{data['url']}#quiz-pg",
                    "keywords": f"{data['shortLabel']} {q['question']} {q['explanation']}".lower(),
                })

            print(f"smt{smt}/{data['slug']}: {len(data['sections'])} sections, {len(data['pgQuestions'])} PG, {len(data['essayQuestions'])} Essay")

    with open(os.path.join(PUBLIC_DIR, "search-index.json"), "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False)
    print(f"Total search index entries: {len(search_index)}")


if __name__ == "__main__":
    main()
