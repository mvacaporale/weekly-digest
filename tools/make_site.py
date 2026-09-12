#!/usr/bin/env python3
"""Build the static site + RSS feed from digests/*.md into docs/.

Run from the repo root (any Python 3.10+ with the `markdown` package, e.g.:
    uv run --with markdown tools/make_site.py
).

Each digest is a markdown file named YYYY-Wnn.md with YAML frontmatter carrying
`summary:` (one-line theme, used as the RSS item description) and `last_edited:`
(YYYY-MM-DD, used as the pub date).
"""

import html
import re
from datetime import datetime, timezone
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://mvacaporale.github.io/weekly-digest"
FEED_TITLE = "Michelangelo's Weekly Digest"
FEED_DESC = "One curated weekly issue: AI and tech, world news that passes a five-year test, and the best of the newsletter pile."
MAX_FEED_ITEMS = 20

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="alternate" type="application/rss+xml" title="{feed_title}" href="{site}/feed.xml">
<style>
  :root {{ color-scheme: light dark; }}
  body {{ max-width: 44rem; margin: 2rem auto 6rem; padding: 0 1.25rem;
         font: 17px/1.65 Georgia, 'Times New Roman', serif;
         color: #1c1c1c; background: #fffdf8; }}
  @media (prefers-color-scheme: dark) {{ body {{ color: #d8d4cc; background: #191a1c; }}
    a {{ color: #8ab4d8; }} }}
  h1, h2, h3 {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; line-height: 1.25; }}
  h1 {{ font-size: 1.7rem; }} h2 {{ font-size: 1.25rem; margin-top: 2.2rem; }}
  a {{ color: #14538c; }}
  nav {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: .85rem; margin-bottom: 2.5rem; }}
  li {{ margin: .35rem 0; }}
  .issue-list li {{ margin: .8rem 0; }}
  .muted {{ opacity: .65; }}
  nav .gh {{ display: inline-flex; align-items: center; gap: .35em;
    border: 1px solid rgba(128,128,128,.45); border-radius: 6px;
    padding: .15em .55em; text-decoration: none; font-weight: 600; }}
  nav .gh:hover {{ border-color: currentColor; }}
  hr {{ border: none; border-top: 1px solid rgba(128,128,128,.35); margin: 2rem 0; }}
</style>
</head>
<body>
<nav><a href="{site}/">← All issues</a> · <a href="{site}/feed.xml">RSS</a> · <a class="gh" href="https://github.com/mvacaporale/weekly-digest"><svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg> Code &amp; specs on GitHub</a></nav>
{body}
</body>
</html>
"""


def parse(path: Path) -> dict:
    text = path.read_text()
    meta = {}
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if m:
        text = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    title_m = re.search(r"^# (.+)$", text, re.M)
    return {
        "slug": path.stem,
        "title": title_m.group(1).strip() if title_m else path.stem,
        "summary": meta.get("summary", ""),
        "date": meta.get("last_edited", ""),
        "body": text,
    }


def rfc822(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    except ValueError:
        d = datetime.now(timezone.utc)
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")


def main() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / ".nojekyll").touch()

    issues = sorted((parse(p) for p in (ROOT / "digests").glob("*.md")),
                    key=lambda i: i["slug"], reverse=True)

    for i in issues:
        body = markdown.markdown(i["body"], extensions=["extra"])
        (docs / f"{i['slug']}.html").write_text(
            PAGE.format(title=html.escape(i["title"]), body=body,
                        site=SITE, feed_title=html.escape(FEED_TITLE)))

    items_html = "\n".join(
        f'<li><a href="{SITE}/{i["slug"]}.html">{html.escape(i["title"])}</a>'
        f'<br><span class="muted">{html.escape(i["summary"])}</span></li>'
        for i in issues)
    index_body = (f"<h1>{html.escape(FEED_TITLE)}</h1>"
                  f"<p>{html.escape(FEED_DESC)}</p>"
                  f'<ul class="issue-list">\n{items_html}\n</ul>')
    index = PAGE.format(title=html.escape(FEED_TITLE), body=index_body,
                        site=SITE, feed_title=html.escape(FEED_TITLE))
    index = index.replace('<nav><a href="' + SITE + '/">← All issues</a> · ', "<nav>")
    (docs / "index.html").write_text(index)

    rss_items = "\n".join(f"""  <item>
    <title>{html.escape(i["title"])}</title>
    <link>{SITE}/{i["slug"]}.html</link>
    <guid>{SITE}/{i["slug"]}.html</guid>
    <pubDate>{rfc822(i["date"])}</pubDate>
    <description>{html.escape(i["summary"])}</description>
  </item>""" for i in issues[:MAX_FEED_ITEMS])
    (docs / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{html.escape(FEED_TITLE)}</title>
  <link>{SITE}/</link>
  <description>{html.escape(FEED_DESC)}</description>
  <language>en-us</language>
{rss_items}
</channel>
</rss>
""")
    print(f"site built: {len(issues)} issue(s)")


if __name__ == "__main__":
    main()
