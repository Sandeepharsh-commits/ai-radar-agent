"""
Static crawler settings. Secrets stay in environment variables.
"""
import os

STATE_FILE = os.environ.get("STATE_FILE", "agent_state.json")
USER_AGENT = "AI-Radar-Agent/1.0 (personal learning project; polite periodic check)"
REQUEST_TIMEOUT = 15
MAX_RSS_ENTRIES = 10
SEEN_LINKS_CAP = 500

ALLOWED_DOMAINS = {
    "microsoft.com",
    "azure.microsoft.com",
    "learn.microsoft.com",
    "techcommunity.microsoft.com",
    "devblogs.microsoft.com",
    "github.com",
    "techcrunch.com",
    "venturebeat.com",
    "feedburner.com",
}

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "utm_id",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ocid",
    "ref",
    "ref_src",
}

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
