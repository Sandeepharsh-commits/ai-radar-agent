"""
summarize.py
------------
Send new items to Azure Foundry gpt-4.1-mini and render the digest email.
"""
from __future__ import annotations

import html
import json
import os
from datetime import date

from openai import AzureOpenAI, OpenAI


SYSTEM_PROMPT = """You are AI Radar for Sunny, an Azure integration developer.
He cares about: Azure API Management, Logic Apps, Service Bus, Event Grid,
Azure Functions, Integration Service Environment patterns, AI gateway / MCP
in APIM, connectors, and how industry AI changes affect integration work.

Given raw news items, produce a plain-language daily digest.

Return JSON only with this shape:
{
  "intro": "2-4 sentences on what mattered today for an Azure integration developer",
  "must_know": [
    {
      "title": "short title",
      "why_it_matters": "1-2 sentences tied to integration work",
      "link": "original url",
      "source": "source name"
    }
  ],
  "worth_watching": [
    {
      "title": "short title",
      "why_it_matters": "1 sentence",
      "link": "original url",
      "source": "source name"
    }
  ],
  "skip_reason": "optional one-liner if the day was quiet"
}

Rules:
- Prefer primary Microsoft / Azure sources over reprints
- Rank APIM, Logic Apps, Service Bus, Functions, Event Grid, AI-gateway first
- Industry AI news only if it changes tools, models, or architecture he might use
- No hype, no emojis, no invented facts
- If an item is a noisy marketing post, leave it out
- Use the provided links unchanged
- Keep must_know to at most 6 items, worth_watching to at most 6
"""


def _client():
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    api_key = os.environ["AZURE_OPENAI_API_KEY"]
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")

    if endpoint.endswith("/openai/v1") or "services.ai.azure.com" in endpoint:
        base = endpoint if endpoint.endswith("/openai/v1") else f"{endpoint}/openai/v1"
        return OpenAI(base_url=base if base.endswith("/") else base + "/", api_key=api_key)

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )


def summarize_items(items: list[dict]) -> dict:
    if not items:
        return {
            "intro": "No new items passed the filter today.",
            "must_know": [],
            "worth_watching": [],
            "skip_reason": "Quiet day — no matching items in range.",
        }

    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
    payload = [
        {
            "source": item.get("source"),
            "type": item.get("type"),
            "title": item.get("title"),
            "link": item.get("link"),
            "published": item.get("published"),
            "summary": item.get("summary", "")[:500],
        }
        for item in items[:40]
    ]

    client = _client()
    response = client.chat.completions.create(
        model=deployment,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Date: {date.today().isoformat()}\n"
                    f"Items:\n{json.dumps(payload, ensure_ascii=False)}"
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    data.setdefault("intro", "")
    data.setdefault("must_know", [])
    data.setdefault("worth_watching", [])
    return data


_SERVICE_RULES = [
    ("APIM / AI Gateway", ("api management", "apim", "ai gateway", "mcp")),
    ("Logic Apps", ("logic app",)),
    ("Service Bus", ("service bus",)),
    ("Event Grid", ("event grid",)),
    ("Functions", ("azure function", "functions host", "durable function")),
    ("Integration Patterns", ("integration service environment", "connector", "integration")),
    ("Industry AI", ("openai", "gpt-", "llm", "anthropic", "claude", "gemini")),
]

_DEFAULT_SERVICE = "Other"

_SERVICE_COLORS = {
    "APIM / AI Gateway": "#0078d4",
    "Logic Apps": "#8764b8",
    "Service Bus": "#00b294",
    "Event Grid": "#ca5010",
    "Functions": "#c19c00",
    "Integration Patterns": "#498205",
    "Industry AI": "#c239b3",
    "Other": "#767676",
}

_SERVICE_BACKGROUNDS = {
    "APIM / AI Gateway": "#deecf9",
    "Logic Apps": "#efe8f5",
    "Service Bus": "#dff6f2",
    "Event Grid": "#fce9dc",
    "Functions": "#fff4ce",
    "Integration Patterns": "#e6f2d8",
    "Industry AI": "#f9e0f5",
    "Other": "#f3f2f1",
}


def _tag_service(item: dict) -> str:
    haystack = f"{item.get('title', '')} {item.get('why_it_matters', '')} {item.get('source', '')}".lower()
    for service, keywords in _SERVICE_RULES:
        if any(keyword in haystack for keyword in keywords):
            return service
    return _DEFAULT_SERVICE


def _group_by_service(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(_tag_service(item), []).append(item)
    return grouped


def digest_to_text(digest: dict, run_date: str | None = None) -> str:
    run_date = run_date or date.today().isoformat()
    must = digest.get("must_know") or []
    watch = digest.get("worth_watching") or []
    lines = [
        f"AI Radar Digest — {run_date}",
        f"{len(must)} must-know · {len(watch)} worth watching",
        "",
        digest.get("intro", "").strip(),
        "",
    ]

    def render_group(items: list[dict], heading: str) -> None:
        lines.append(heading)
        lines.append("=" * len(heading))
        grouped = _group_by_service(items)
        for service, group_items in grouped.items():
            lines.append(f"\n[{service}]")
            for item in group_items:
                lines.append(f"* {item.get('title')}")
                lines.append(f"  {item.get('why_it_matters')}")
                lines.append(f"  {item.get('link')}  ({item.get('source')})")
        lines.append("")

    if must:
        render_group(must, "MUST KNOW")
    if watch:
        render_group(watch, "WORTH WATCHING")
    if digest.get("skip_reason") and not must and not watch:
        lines.append(digest["skip_reason"])
    lines.append("Generated by AI Radar Agent.")
    return "\n".join(lines)


def _item_card(item: dict, accent: str) -> str:
    title = html.escape(str(item.get("title") or ""))
    link = html.escape(str(item.get("link") or "#"), quote=True)
    why = html.escape(str(item.get("why_it_matters") or ""))
    source = html.escape(str(item.get("source") or ""))
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="margin:0 0 10px 0;background:#ffffff;border:1px solid #e8e8e8;
                  border-left:3px solid {accent};border-radius:6px;">
      <tr>
        <td style="padding:14px 16px;">
          <a href="{link}" style="color:#1a1a1a;font-size:15px;font-weight:600;
             text-decoration:none;line-height:1.4;">{title}</a>
          <p style="margin:6px 0 8px;color:#4a4a4a;font-size:13.5px;line-height:1.5;">{why}</p>
          <span style="display:inline-block;color:#8a8a8a;font-size:11.5px;
                text-transform:uppercase;letter-spacing:.04em;">{source}</span>
        </td>
      </tr>
    </table>"""


def _service_section(items: list[dict], accent: str) -> str:
    grouped = _group_by_service(items)
    blocks = []
    for service, group_items in grouped.items():
        color = _SERVICE_COLORS.get(service, accent)
        chip_bg = _SERVICE_BACKGROUNDS.get(service, "#f3f2f1")
        cards = "".join(_item_card(i, color) for i in group_items)
        label = html.escape(service)
        blocks.append(f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 18px;">
          <tr><td style="padding:0 0 8px 2px;">
            <span style="display:inline-block;background:{chip_bg};color:{color};
                  font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
                  padding:3px 9px;border-radius:12px;">{label}</span>
          </td></tr>
          <tr><td>{cards}</td></tr>
        </table>""")
    return "".join(blocks)


def digest_to_html(digest: dict, run_date: str | None = None) -> str:
    run_date = run_date or date.today().isoformat()
    must = digest.get("must_know") or []
    watch = digest.get("worth_watching") or []
    intro = html.escape(str(digest.get("intro") or ""))
    must_html = (
        _service_section(must, "#d13438")
        if must
        else '<p style="color:#8a8a8a;font-size:14px;">Nothing urgent today.</p>'
    )
    watch_html = (
        _service_section(watch, "#0078d4")
        if watch
        else '<p style="color:#8a8a8a;font-size:14px;">No extra items.</p>'
    )
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#eef1f4;font-family:'Segoe UI',Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f4;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0"
               style="max-width:640px;width:100%;background:#ffffff;border-radius:10px;overflow:hidden;">
          <tr>
            <td style="background:#0b3d91;padding:28px 32px;">
              <p style="margin:0 0 6px;color:#cfe4ff;font-size:11px;font-weight:700;
                        letter-spacing:.12em;text-transform:uppercase;">AI Radar</p>
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">
                Digest — {html.escape(run_date)}
              </h1>
              <p style="margin:10px 0 0;color:#d8e7fb;font-size:13px;">
                {len(must)} must-know &nbsp;&middot;&nbsp; {len(watch)} worth watching
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px 4px;">
              <p style="margin:0;color:#333;font-size:15px;line-height:1.6;">{intro}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 4px;">
              <h2 style="margin:0 0 12px;font-size:14px;color:#d13438;font-weight:700;
                         letter-spacing:.03em;text-transform:uppercase;border-bottom:2px solid #f3d3d4;
                         padding-bottom:6px;">Must Know</h2>
              {must_html}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 32px 24px;">
              <h2 style="margin:0 0 12px;font-size:14px;color:#0078d4;font-weight:700;
                         letter-spacing:.03em;text-transform:uppercase;border-bottom:2px solid #cfe4ff;
                         padding-bottom:6px;">Worth Watching</h2>
              {watch_html}
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px 24px;border-top:1px solid #eee;">
              <p style="margin:0;color:#9a9a9a;font-size:11.5px;">
                Generated by AI Radar Agent · Azure used only for the LLM.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
