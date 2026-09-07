"""RSS / Atom collection. Same item shape as before."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import feedparser

from config import MAX_RSS_ENTRIES, RSS_FEEDS, USER_AGENT
from crawler.urlutil import is_allowed_url, normalize_url


def _seen_set(links: list) -> set[str]:
    seen = set()
    for link in links:
        if not link:
            continue
        seen.add(link)
        seen.add(normalize_url(link))
    return seen


def _entry_time(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def fetch_rss_updates(state: dict, lookback_hours: int | None = None) -> list[dict]:
    seen = _seen_set(state.get("seen_links", []))
    new_items: list[dict] = []
    headers = {"User-Agent": USER_AGENT}
    cutoff = None
    if lookback_hours:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        print(f"[rss] lookback {lookback_hours}h since {cutoff.isoformat()}")

    per_feed = MAX_RSS_ENTRIES
    if lookback_hours:
        per_feed = max(MAX_RSS_ENTRIES, 40)

    for source_name, url in RSS_FEEDS.items():
        parsed = feedparser.parse(url, request_headers=headers)
        if parsed.bozo and not parsed.entries:
            print(f"[warning] Could not parse feed: {source_name}")
            continue
        added = 0
        skipped_domain = 0
        skipped_old = 0
        for entry in parsed.entries[:per_feed]:
            raw_link = entry.get("link")
            if not raw_link:
                continue
            link = normalize_url(raw_link)
            if not is_allowed_url(link):
                skipped_domain += 1
                continue

            published_at = _entry_time(entry)
            if cutoff is not None:
                if published_at is None or published_at < cutoff:
                    skipped_old += 1
                    continue
            elif raw_link in seen or link in seen:
                continue

            new_items.append({
                "source": source_name,
                "type": "rss",
                "title": entry.get("title", "Untitled"),
                "link": link,
                "published": entry.get("published") or entry.get("updated") or "Unknown date",
                "summary": (entry.get("summary") or "")[:500],
            })
            seen.add(link)
            seen.add(raw_link)
            added += 1
        extra = ""
        if skipped_domain:
            extra += f", skipped {skipped_domain} off-domain"
        if skipped_old:
            extra += f", skipped {skipped_old} older than lookback"
        print(f"[rss] {source_name}: {added} new / {len(parsed.entries)} in feed{extra}")

    state["seen_links"] = list(seen)
    return new_items
