"""RSS / Atom collection. Same item shape as before."""
from __future__ import annotations

import feedparser

from config import MAX_RSS_ENTRIES, RSS_FEEDS, USER_AGENT


def fetch_rss_updates(state: dict) -> list[dict]:
    seen = set(state.get("seen_links", []))
    new_items: list[dict] = []
    headers = {"User-Agent": USER_AGENT}

    for source_name, url in RSS_FEEDS.items():
        parsed = feedparser.parse(url, request_headers=headers)
        if parsed.bozo and not parsed.entries:
            print(f"[warning] Could not parse feed: {source_name}")
            continue
        added = 0
        for entry in parsed.entries[:MAX_RSS_ENTRIES]:
            link = entry.get("link")
            if not link or link in seen:
                continue
            new_items.append({
                "source": source_name,
                "type": "rss",
                "title": entry.get("title", "Untitled"),
                "link": link,
                "published": entry.get("published", "Unknown date"),
                "summary": (entry.get("summary") or "")[:500],
            })
            seen.add(link)
            added += 1
        print(f"[rss] {source_name}: {added} new / {len(parsed.entries)} in feed")

    state["seen_links"] = list(seen)
    return new_items