# Weekly Digest

One curated issue a week, produced by an automated pipeline instead of doomscrolling:

- **AI & Tech** — distilled from a week of the X timeline (capability jumps, strategic moves, tools worth adopting; ruthless bar, no hype).
- **The World** — US/world/geopolitics filtered by a *five-year test*: an item gets in only if a well-informed person five years from now would need to know it. Zero items is a valid week.
- **Newsletters** — the week's newsletter pile (AlphaSignal, Tim Ferriss, Wisereads) deduped, ranked, and compressed.

**Read it:** [issue archive](https://mvacaporale.github.io/weekly-digest/) · [RSS feed](https://mvacaporale.github.io/weekly-digest/feed.xml)

## How it works

Every Friday morning an always-on box:

1. Pulls the week's raw material — X home timeline (API), Wikipedia Current Events portal, unseen Readwise Reader feed items (cleaned of email-HTML bloat).
2. Runs one LLM judgment pass per track, each against a written spec that encodes the selection bar and voice. The specs are living documents — the filter is edited, not the outputs.
3. Runs a merge pass that unifies the three track notes into the single issue in [`digests/`](digests/), deduping stories that arrived through more than one source.
4. Rebuilds this site + feed ([`tools/make_site.py`](tools/make_site.py)) and pushes.

The digests are written for one specific reader — that's the point. Fork the idea, not the taste.
