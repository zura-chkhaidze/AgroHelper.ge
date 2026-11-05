#!/usr/bin/env python3
"""
AgroHelper blog builder (no dependencies, Python 3.8+).

Usage:   python build.py
Input:   content/blog/<slug>.ka.md  and/or  content/blog/<slug>.en.md
Output:  blog/ , en/blog/ (rebuilt from scratch on every run - never edit by hand)
         sitemap.xml (rewritten on every run)

Front matter of every .md file:
---
title: ...
description: ...      (max ~155 characters)
category: ...
date: 2026-11-03
updated: 2026-11-03   (optional)
image: /img/blog/x.webp  (optional, article cover)
---
Markdown subset: ## / ### headings, paragraphs, - lists, 1. lists, > notes,
**bold**, [text](url), ![alt](src), and a line {{cta}} for an in-article app banner.
"""
import html, re, shutil, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content" / "blog"
SITE = "https://agrohelper.ge"
HOME_LASTMOD = "2026-11-02"
PLAY = "https://play.google.com/store/apps/details?id=ge.agrohelper.app"
APPSTORE = "https://apps.apple.com/us/app/agrohelper/id6761626943"
LOGO = SITE + "/logo.png"
OG_DEFAULT = SITE + "/og-image.jpg"

T = {
    "ka": {
        "home": "მთავარი", "blog": "ბლოგი", "download": "ჩამოტვირთვა",
        "blog_title": "აგრო ბლოგი — მცენარეთა დაავადებები, მოვლა და რჩევები | AgroHelper",
        "blog_desc": "პრაქტიკული სტატიები ფერმერებისა და მებაღეებისთვის: მცენარეთა დაავადებები, მორწყვა, მავნებლები და მოსავლის მოვლა.",
        "blog_h1": "აგრო ბლოგი",
        "blog_sub": "პრაქტიკული რჩევები მცენარეთა დაავადებებზე, მოვლასა და მოსავლის დაცვაზე.",
        "top_title": "გადაუღე მცენარეს ფოტო — AgroHelper დაავადებას ამოიცნობს",
        "top_text": "AI სკანერი, აგრო ასისტენტი და აგრო ბაზარი ერთ აპლიკაციაში.",
        "mid_title": "არ ხარ დარწმუნებული, რა დაემართა მცენარეს?",
        "mid_text": "გადაუღე ფოტო AgroHelper-ს და მიიღე დიაგნოზის მინიშნება წამებში.",
        "end_title": "იზრუნე შენს მცენარეებზე უფრო ჭკვიანურად",
        "end_text": "ჩამოტვირთე AgroHelper: AI დიაგნოსტიკა, პერსონალური აგრო ასისტენტი და ყოველდღიური აგრო სიახლეები.",
        "disclaimer": "სტატია ზოგადი ინფორმაციისთვისაა. პრეპარატის დოზა და გამოყენების წესი ყოველთვის პრეპარატის ეტიკეტის მიხედვით დაიცავი ან გაიარე კონსულტაცია აგრონომთან.",
        "related": "იხილე ასევე", "read": "კითხვა", "min": "წთ", "updated": "განახლებულია",
        "by": "AgroHelper-ის გუნდი", "rights": "© 2026 AgroHelper. ყველა უფლება დაცულია.",
        "empty": "პირველი სტატიები მალე გამოქვეყნდება.",
    },
    "en": {
        "home": "Home", "blog": "Blog", "download": "Download",
        "blog_title": "Agro Blog — Plant Diseases, Care Guides & Farming Tips | AgroHelper",
        "blog_desc": "Practical articles for farmers and gardeners: plant diseases, watering, pests and crop care.",
        "blog_h1": "Agro Blog",
        "blog_sub": "Practical advice on plant diseases, crop care and protecting your harvest.",
        "top_title": "Snap a photo of your plant — AgroHelper identifies the disease",
        "top_text": "AI scanner, farming assistant and agro marketplace in one app.",
        "mid_title": "Not sure what is wrong with your plant?",
        "mid_text": "Take a photo with AgroHelper and get a diagnosis hint in seconds.",
        "end_title": "Take care of your plants, the smarter way",
        "end_text": "Download AgroHelper: AI diagnostics, a personal farming assistant and daily agro news.",
        "disclaimer": "This article is for general information. Always follow the product label for dosage and use, or consult a local agronomist.",
        "related": "Related articles", "read": "read", "min": "min", "updated": "Updated",
        "by": "AgroHelper Team", "rights": "© 2026 AgroHelper. All rights reserved.",
        "empty": "The first articles are coming soon.",
    },
}

CSS = """
:root{--forest:#1a3a1e;--leaf:#2d7a3a;--mint:#5cb87a;--lime:#a8e063;--cream:#f5f0e8;--bark:#3d2b1f;--mist:#e8f4ea}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:"DM Sans",sans-serif;background:var(--cream);color:var(--bark);line-height:1.75;font-size:17px}
a{color:var(--leaf)}
img{max-width:100%;height:auto}
.nav{position:sticky;top:0;z-index:10;background:var(--forest);color:#fff;display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.7rem 5%}
.nav a{color:#fff;text-decoration:none}
.brand{display:flex;align-items:center;gap:.5rem;font-family:"Playfair Display",serif;font-weight:700;font-size:1.25rem}
.brand img{width:34px;height:34px;object-fit:contain}
.brand span{color:var(--lime)}
.nav-links{display:flex;align-items:center;gap:1.2rem;font-size:.95rem}
.nav-links .lang{border:1px solid rgba(255,255,255,.4);border-radius:6px;padding:.15rem .55rem;font-size:.85rem}
.nav-links .dl{background:var(--lime);color:var(--forest);font-weight:600;border-radius:999px;padding:.35rem 1rem}
.wrap{max-width:760px;margin:0 auto;padding:2.5rem 5% 3rem}
.wide{max-width:1080px}
.crumbs{font-size:.85rem;color:#7a6a5a;margin-bottom:1rem}
.crumbs a{color:#7a6a5a}
.cat{display:inline-block;background:var(--mist);color:var(--leaf);font-weight:600;font-size:.8rem;padding:.2rem .8rem;border-radius:999px;margin-bottom:.8rem}
h1{font-family:"Playfair Display",serif;color:var(--forest);font-size:2.3rem;line-height:1.25;margin-bottom:.8rem}
h2{font-family:"Playfair Display",serif;color:var(--forest);font-size:1.6rem;line-height:1.3;margin:2.2rem 0 .8rem}
h3{color:var(--forest);font-size:1.15rem;margin:1.5rem 0 .5rem}
.meta{font-size:.9rem;color:#7a6a5a;margin-bottom:1.5rem}
.article p,.article ul,.article ol,.article blockquote,.article figure{margin-bottom:1.1rem}
.article ul,.article ol{padding-left:1.4rem}
.article li{margin-bottom:.45rem}
.article blockquote{background:var(--mist);border-left:4px solid var(--leaf);padding:.9rem 1.1rem;border-radius:0 10px 10px 0}
.article figure img{border-radius:14px;display:block;width:100%}
.article figcaption{font-size:.85rem;color:#7a6a5a;margin-top:.4rem}
.cover{border-radius:16px;margin-bottom:1.5rem;width:100%;display:block}
.cta{background:var(--mist);border:1px solid #cfe5d3;border-radius:16px;padding:1.2rem 1.4rem;margin:1.5rem 0}
.cta strong{display:block;font-family:"Playfair Display",serif;font-size:1.15rem;color:var(--forest);margin-bottom:.2rem}
.cta p{margin:0 0 .9rem;font-size:.95rem}
.cta.big{background:var(--forest);border:0;text-align:center;padding:2rem 1.5rem;margin-top:2.5rem}
.cta.big strong{color:#fff;font-size:1.5rem}
.cta.big p{color:#d8e8da;font-size:1rem}
.btns{display:flex;flex-wrap:wrap;gap:.6rem}
.cta.big .btns{justify-content:center}
.btn{display:inline-block;text-decoration:none;font-weight:600;font-size:.95rem;border-radius:999px;padding:.55rem 1.3rem;background:var(--forest);color:#fff}
.cta.big .btn{background:var(--lime);color:var(--forest)}
.note{font-size:.85rem;color:#7a6a5a;margin-top:1.5rem;border-top:1px solid #ddd3c2;padding-top:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:1.4rem;margin-top:1.5rem}
.card{background:#fff;border-radius:16px;overflow:hidden;text-decoration:none;color:var(--bark);display:flex;flex-direction:column;box-shadow:0 2px 14px rgba(26,58,30,.08);transition:transform .2s}
.card:hover{transform:translateY(-3px)}
.thumb{height:150px;background:linear-gradient(135deg,var(--leaf),var(--mint));display:flex;align-items:flex-end;padding:0;color:#fff;font-weight:600;overflow:hidden}
.thumb span{padding:.9rem}
.thumb img{width:100%;height:150px;object-fit:cover;display:block}
.card .body{padding:1.1rem 1.2rem 1.3rem}
.card h3{margin:0 0 .4rem;font-family:"Playfair Display",serif;font-size:1.15rem;line-height:1.35}
.card p{font-size:.92rem;line-height:1.55;color:#6b5b4b}
.card .m{font-size:.8rem;color:#8a7a6a;margin-top:.6rem}
footer{background:var(--forest);color:#cfe0d1;text-align:center;padding:1.6rem 5%;font-size:.9rem}
footer a{color:var(--lime)}
@media(max-width:640px){h1{font-size:1.8rem}.nav-links a.hide-m{display:none}body{font-size:16px}
.nav{padding:.6rem 4%;gap:.4rem}.brand{font-size:1.02rem;gap:.35rem}.brand img{width:26px;height:26px}
.nav-links{gap:.55rem;font-size:.85rem}.nav-links .lang{padding:.1rem .4rem;font-size:.78rem}.nav-links .dl{padding:.3rem .75rem;font-size:.8rem}
.cta.big{padding:1.6rem 1rem}}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@400;500;600&display=swap">')

esc = html.escape


def play_url(slug, pos):
    ref = quote(f"utm_source=blog&utm_medium={pos}&utm_campaign={slug}", safe="")
    return f"{PLAY}&referrer={ref}"


def parse(path):
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        sys.exit(f"{path.name}: missing front matter")
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for req in ("title", "description", "date"):
        if not meta.get(req):
            sys.exit(f"{path.name}: front matter '{req}' is required")
    if len(meta["description"]) > 170:
        print(f"WARNING {path.name}: description is {len(meta['description'])} chars (aim for <=155)")
    slug, lang = path.name[:-3].rsplit(".", 1)
    for src in [meta.get("image", "")] + re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", m.group(2)):
        if src.startswith("/") and not (ROOT / src.lstrip("/")).exists():
            print(f"WARNING {path.name}: image file not found: {src}")
    meta.update(slug=slug, lang=lang, body=m.group(2).strip())
    return meta


def inline(text):
    t = esc(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: '<a href="%s"%s>%s</a>' % (
                   m.group(2), ' rel="noopener" target="_blank"' if m.group(2).startswith("http") else "", m.group(1)), t)
    return t


def cta_block(a, kind):
    t = T[a["lang"]]
    pos = {"top": "top", "mid": "mid", "end": "bottom"}[kind]
    title, text = t[kind + "_title"], t[kind + "_text"]
    cls = "cta big" if kind == "end" else "cta"
    return (f'<div class="{cls}"><strong>{esc(title)}</strong><p>{esc(text)}</p><div class="btns">'
            f'<a class="btn" href="{esc(play_url(a["slug"], pos))}" target="_blank" rel="noopener">Google Play</a>'
            f'<a class="btn" href="{esc(APPSTORE)}" target="_blank" rel="noopener">App Store</a></div></div>')


def render_md(a):
    out, buf, lst = [], [], None

    def flush_p():
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
            buf.clear()

    def flush_l():
        nonlocal lst
        if lst:
            out.append("<%s>%s</%s>" % (lst[0], "".join("<li>%s</li>" % inline(i) for i in lst[1]), lst[0]))
            lst = None

    for line in a["body"].split("\n"):
        s = line.strip()
        if not s:
            flush_p(); flush_l(); continue
        if s == "{{cta}}":
            flush_p(); flush_l(); out.append(cta_block(a, "mid")); continue
        if s.startswith("### "):
            flush_p(); flush_l(); out.append("<h3>%s</h3>" % inline(s[4:])); continue
        if s.startswith("## "):
            flush_p(); flush_l(); out.append("<h2>%s</h2>" % inline(s[3:])); continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)$", s)
        if m:
            flush_p(); flush_l()
            out.append('<figure><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>'
                       % (esc(m.group(2)), esc(m.group(1)), esc(m.group(1)))); continue
        if s.startswith("> "):
            flush_p(); flush_l(); out.append("<blockquote>%s</blockquote>" % inline(s[2:])); continue
        m = re.match(r"^(-|\d+\.)\s+(.*)$", s)
        if m:
            flush_p()
            kind = "ul" if m.group(1) == "-" else "ol"
            if lst and lst[0] != kind:
                flush_l()
            if not lst:
                lst = (kind, [])
            lst[1].append(m.group(2)); continue
        flush_l(); buf.append(s)
    flush_p(); flush_l()
    return "\n".join(out)


def url_for(lang, slug=None):
    base = "/blog/" if lang == "ka" else "/en/blog/"
    return base + (slug + "/" if slug else "")


def home_url(lang):
    return "/" if lang == "ka" else "/?lang=en"


def head(lang, title, desc, canonical, alts, og_image, og_type, extra_ld="", noindex=False):
    alt_tags = ""
    if alts:
        for l, u in alts.items():
            alt_tags += f'<link rel="alternate" hreflang="{l}" href="{SITE}{u}">\n'
        alt_tags += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alts["ka"]}">\n'
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    loc = "ka_GE" if lang == "ka" else "en_US"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{SITE}{canonical}">
{alt_tags}<link rel="icon" href="/logo.png">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="AgroHelper">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{canonical}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:locale" content="{loc}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(og_image)}">
{FONTS}
<style>{CSS}</style>
{extra_ld}</head>
<body>
"""


def nav(lang, switch_url, slug):
    t = T[lang]
    other = "EN" if lang == "ka" else "KA"
    return f"""<header class="nav">
<a class="brand" href="{home_url(lang)}"><img src="/logo.png" alt="AgroHelper">Agro<span>Helper</span></a>
<nav class="nav-links">
<a class="hide-m" href="{home_url(lang)}">{t['home']}</a>
<a href="{url_for(lang)}">{t['blog']}</a>
<a class="lang" href="{switch_url}">{other}</a>
<a class="dl" href="{esc(play_url(slug or 'blog-index', 'nav'))}" target="_blank" rel="noopener">{t['download']}</a>
</nav>
</header>
"""


def footer(lang):
    t = T[lang]
    return f'<footer><a href="{home_url(lang)}">AgroHelper</a> · <a href="{url_for(lang)}">{t["blog"]}</a><br>{t["rights"]}</footer>\n</body>\n</html>\n'


def card(a):
    t = T[a["lang"]]
    thumb = (f'<img src="{esc(a["image"])}" alt="" loading="lazy">' if a.get("image")
             else '<span>%s</span>' % esc(a.get("category", "")))
    return (f'<a class="card" href="{url_for(a["lang"], a["slug"])}"><div class="thumb">{thumb}</div>'
            f'<div class="body"><h3>{esc(a["title"])}</h3><p>{esc(a["description"])}</p>'
            f'<div class="m">{read_min(a)} {t["min"]} · {a["date"]}</div></div></a>')


def read_min(a):
    return max(1, round(len(a["body"].split()) / 200))


def build():
    arts = [parse(p) for p in sorted(CONTENT.glob("*.md"))]
    for a in arts:
        if a["lang"] not in T:
            sys.exit(f"Unknown language in file name: {a['slug']}.{a['lang']}.md")
    by_slug = {}
    for a in arts:
        by_slug.setdefault(a["slug"], {})[a["lang"]] = a
    langs_present = {a["lang"] for a in arts}

    for d in (ROOT / "blog", ROOT / "en" / "blog"):
        if d.exists():
            shutil.rmtree(d)

    sitemap = [("/", HOME_LASTMOD), ("/?lang=en", HOME_LASTMOD)]

    # blog index pages
    for lang in sorted(langs_present):
        t = T[lang]
        items = sorted([a for a in arts if a["lang"] == lang], key=lambda x: x["date"], reverse=True)
        other = "en" if lang == "ka" else "ka"
        alts = {"ka": url_for("ka"), "en": url_for("en")} if len(langs_present) == 2 else None
        switch = url_for(other) if other in langs_present else home_url(other)
        page = head(lang, t["blog_title"], t["blog_desc"], url_for(lang), alts, OG_DEFAULT, "website")
        page += nav(lang, switch, None)
        page += f'<main class="wrap wide"><h1>{t["blog_h1"]}</h1><p>{t["blog_sub"]}</p>'
        page += '<div class="grid">' + "".join(card(a) for a in items) + "</div></main>\n"
        page += footer(lang)
        out = ROOT / url_for(lang).strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        sitemap.append((url_for(lang), max(a.get("updated", a["date"]) for a in items)))

    # article pages
    for a in arts:
        lang, slug = a["lang"], a["slug"]
        t = T[lang]
        pair = by_slug[slug]
        alts = {l: url_for(l, slug) for l in ("ka", "en") if l in pair} if len(pair) == 2 else None
        other = "en" if lang == "ka" else "ka"
        switch = url_for(other, slug) if other in pair else (url_for(other) if other in langs_present else home_url(other))
        canonical = url_for(lang, slug)
        modified = a.get("updated", a["date"])
        # Facebook/LinkedIn do not reliably show WebP previews: use a JPG/PNG for og:image
        cover = a.get("image", "")
        og = a.get("og_image", "")
        if not og and cover:
            if cover.lower().endswith(".webp"):
                cand = cover.rsplit(".", 1)[0] + ".jpg"
                if (ROOT / cand.lstrip("/")).exists():
                    og = cand
                else:
                    print(f"WARNING {slug}.{lang}.md: add {cand} (JPG copy of the cover) so Facebook can show the preview image")
            else:
                og = cover
        image = SITE + og if og.startswith("/") else OG_DEFAULT
        ld = """<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
{"@type":"Article","headline":%s,"description":%s,"inLanguage":"%s","datePublished":"%s","dateModified":"%s","image":%s,
"mainEntityOfPage":"%s","author":{"@type":"Organization","name":"AgroHelper","url":"%s/"},
"publisher":{"@type":"Organization","name":"AgroHelper","logo":{"@type":"ImageObject","url":"%s"}}},
{"@type":"BreadcrumbList","itemListElement":[
{"@type":"ListItem","position":1,"name":%s,"item":"%s%s"},
{"@type":"ListItem","position":2,"name":%s,"item":"%s%s"},
{"@type":"ListItem","position":3,"name":%s,"item":"%s%s"}]}]}
</script>
""" % (jd(a["title"]), jd(a["description"]), lang, a["date"], modified, jd(image), SITE + canonical, SITE, LOGO,
       jd(t["home"]), SITE, home_url(lang), jd(t["blog"]), SITE, url_for(lang), jd(a["title"]), SITE, canonical)
        page = head(lang, a["title"] + " | AgroHelper", a["description"], canonical, alts, image, "article", ld)
        page += nav(lang, switch, slug)
        cover = f'<img class="cover" src="{esc(a["image"])}" alt="{esc(a["title"])}">' if a.get("image") else ""
        page += f'<main class="wrap"><div class="crumbs"><a href="{home_url(lang)}">{t["home"]}</a> › <a href="{url_for(lang)}">{t["blog"]}</a></div>'
        page += f'<article class="article"><span class="cat">{esc(a.get("category", ""))}</span><h1>{esc(a["title"])}</h1>'
        page += f'<div class="meta">{t["by"]} · {a["date"]} · {read_min(a)} {t["min"]}'
        if modified != a["date"]:
            page += f' · {t["updated"]}: {modified}'
        page += f'</div>{cover}{cta_block(a, "top")}{render_md(a)}{cta_block(a, "end")}'
        page += f'<p class="note">{t["disclaimer"]}</p></article>'
        rel = [r for r in arts if r["lang"] == lang and r["slug"] != slug][:3]
        if rel:
            page += f'<h2>{t["related"]}</h2><div class="grid">' + "".join(card(r) for r in rel) + "</div>"
        page += "</main>\n" + footer(lang)
        out = ROOT / canonical.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        sitemap.append((canonical, modified))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in sitemap:
        xml.append(f"  <url>\n    <loc>{esc(SITE + loc)}</loc>\n    <lastmod>{mod}</lastmod>\n  </url>")
    xml.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("\n".join(xml), encoding="utf-8")
    print(f"Built {len(arts)} article file(s), {len(sitemap)} sitemap URL(s).")


def jd(s):
    import json
    return json.dumps(s, ensure_ascii=False)


if __name__ == "__main__":
    build()