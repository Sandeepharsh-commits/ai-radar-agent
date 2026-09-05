"""
fetch_hybrid.py
---------------
Hybrid collection layer for the AI Radar Agent.
RSS/Atom where available, polite crawl + content-hash for pages with no feed.
"""
import json
import os
import hashlib
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from datetime import datetime

STATE_FILE = os.environ.get("STATE_FILE", "agent_state.json")
USER_AGENT = "AI-Radar-Agent/1.0 (personal learning project; polite periodic check)"
REQUEST_TIMEOUT = 15

RSS_FEEDS = {
    "Azure Updates": "https://www.microsoft.com/releasecommunications/api/v2/azure/rss",
    "MS Tech Community - AI": "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=AIPlatformBlog",
    "MS Tech Community - Integration": "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/board?board.id=IntegrationsonAzureBlog",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://feeds.feedburner.com/venturebeat/SZYF",
    "Azure Functions Host (GitHub releases)": "https://github.com/Azure/azure-functions-host/releases.atom",
    "Azure Functions Core Tools (GitHub releases)": "https://github.com/Azure/azure-functions-core-tools/releases.atom",
    "Logic Apps (GitHub releases)": "https://github.com/Azure/logicapps/releases.atom",
    "Azure SDK for .NET (GitHub releases)": "https://github.com/Azure/azure-sdk-for-net/releases.atom",
    "API Management changelog (GitHub)": "https://github.com/Azure/API-Management/commits/main.atom",
}

CRAWL_PAGES = {
    "Azure API Management - breaking changes": "https://learn.microsoft.com/en-us/azure/api-management/breaking-changes/overview",
    "Azure Event Grid - What's new": "https://learn.microsoft.com/en-us/azure/event-grid/whats-new",
    "Azure Service Bus overview (watch for release notes)": "https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-overview",
    "Logic Apps agent workflows": "https://learn.microsoft.com/en-us/azure/logic-apps/agent-workflows-concepts",
}

INTEGRATION_HINTS = (
    "api management", "apim", "logic app", "service bus", "event grid",
    "function", "integration", "servicebus", "eventhub", "event hub",
    "mcp", "ai gateway", "connector", "workflow", "bicep", "arm template",
)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_links": [], "page_hashes": {}}


def save_state(state):
    state["seen_links"] = state["seen_links"][-500:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_rss_updates(state):
    seen = set(state["seen_links"])
    new_items = []
    headers = {"User-Agent": USER_AGENT}
    for source_name, url in RSS_FEEDS.items():
        parsed = feedparser.parse(url, request_headers=headers)
        if parsed.bozo and not parsed.entries:
            print(f"[warning] Could not parse feed: {source_name}")
            continue
        added = 0
        for entry in parsed.entries[:10]:
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


def is_crawl_allowed(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return False


def fetch_page_text(url):
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def fetch_crawl_updates(state):
    changed_pages = []
    for page_name, url in CRAWL_PAGES.items():
        if not is_crawl_allowed(url):
            print(f"[skipped] robots.txt disallows crawling: {page_name}")
            continue
        try:
            text = fetch_page_text(url)
        except Exception as e:
            print(f"[warning] Could not fetch {page_name}: {e}")
            continue
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous_hash = state["page_hashes"].get(url)
        if previous_hash != content_hash:
            changed_pages.append({
                "source": page_name,
                "type": "crawl",
                "title": f"{page_name} - content changed",
                "link": url,
                "published": datetime.now().isoformat(),
                "summary": text[:800],
            })
            state["page_hashes"][url] = content_hash
            print(f"[crawl] {page_name}: changed")
        else:
            print(f"[crawl] {page_name}: unchanged")
    return changed_pages


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