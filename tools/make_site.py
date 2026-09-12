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
  hr {{ border: none; border-top: 1px solid rgba(128,128,128,.35); margin: 2rem 0; }}
</style>
</head>
<body>
<nav><a href="{site}/">← All issues</a> · <a href="{site}/feed.xml">RSS</a> · <a href="https://github.com/mvacaporale/weekly-digest">How this is made</a></nav>
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
