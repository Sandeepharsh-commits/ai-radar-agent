"""Load and save agent_state.json. Keeps seen_links + page_hashes."""
from __future__ import annotations

import json
import os

from config import SEEN_LINKS_CAP, STATE_FILE


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("seen_links", [])
        data.setdefault("page_hashes", {})
        return data
    return {"seen_links": [], "page_hashes": {}}


def save_state(state: dict) -> None:
    state["seen_links"] = list(state.get("seen_links", []))[-SEEN_LINKS_CAP:]
    state.setdefault("page_hashes", {})
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)