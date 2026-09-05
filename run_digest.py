"""
run_digest.py
-------------
Fetch → summarize → email. One command for Colab or GitHub Actions.
"""
from __future__ import annotations

import argparse
import os
from datetime import date

from fetch_hybrid import fetch_all_updates
from send_email import send_digest
from summarize import digest_to_html, digest_to_text, summarize_items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-email", action="store_true", help="Print digest only")
    args = parser.parse_args()

    print("1/3 Fetching updates...")
    items = fetch_all_updates()
    print(f"    {len(items)} new/changed item(s)")

    print("2/3 Asking gpt-4.1-mini to write the digest...")
    digest = summarize_items(items)
    run_date = date.today().isoformat()
    text = digest_to_text(digest, run_date)
    html = digest_to_html(digest, run_date)
    print("\n----- DIGEST PREVIEW -----\n")
    print(text)
    print("\n--------------------------\n")

    if args.no_email or os.environ.get("DRY_RUN", "").lower() == "true":
        print("3/3 Email skipped.")
        return

    print("3/3 Sending Gmail...")
    send_digest(f"Your AI Radar Digest – {run_date}", html, text)
    print("    Sent.")


if __name__ == "__main__":
    main()
