"""
fetch_hybrid.py
---------------
Orchestrator. Public API is unchanged: fetch_all_updates().
"""
from datetime import datetime

from crawler.rss import fetch_rss_updates
from crawler.state import load_state, save_state
from crawler.web import fetch_crawl_updates, fetch_page_text, is_crawl_allowed

__all__ = [
    "fetch_all_updates",
    "fetch_rss_updates",
    "fetch_crawl_updates",
    "load_state",
    "save_state",
    "fetch_page_text",
    "is_crawl_allowed",
]


def fetch_all_updates():
    state = load_state()
    rss_items = fetch_rss_updates(state)
    crawl_items = fetch_crawl_updates(state)
    save_state(state)
    return rss_items + crawl_items


if __name__ == "__main__":
    print(f"Running hybrid fetch at {datetime.now().isoformat()}...\n")
    results = fetch_all_updates()
    if not results:
        print("No new updates found.")
    else:
        print(f"Found {len(results)} new/changed item(s):\n")
        for item in results:
            print(f"- [{item['type'].upper()}] [{item['source']}] {item['title']}")
            print(f"  {item['link']}\n")
