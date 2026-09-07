"""Fixed-page crawl with robots.txt and content hashing."""
from __future__ import annotations

import hashlib
from datetime import datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config import CRAWL_PAGES, REQUEST_TIMEOUT, USER_AGENT


def is_crawl_allowed(url: str) -> bool:
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return False


def fetch_page_text(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def fetch_crawl_updates(state: dict) -> list[dict]:
    changed_pages: list[dict] = []
    hashes = state.setdefault("page_hashes", {})

    for page_name, url in CRAWL_PAGES.items():
        if not is_crawl_allowed(url):
            print(f"[skipped] robots.txt disallows crawling: {page_name}")
            continue
        try:
            text = fetch_page_text(url)
        except Exception as exc:
            print(f"[warning] Could not fetch {page_name}: {exc}")
            continue
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous_hash = hashes.get(url)
        if previous_hash != content_hash:
            changed_pages.append({
                "source": page_name,
                "type": "crawl",
                "title": f"{page_name} - content changed",
                "link": url,
                "published": datetime.now().isoformat(),
                "summary": text[:800],
            })
            hashes[url] = content_hash
            print(f"[crawl] {page_name}: changed")
        else:
            print(f"[crawl] {page_name}: unchanged")
    return changed_pages