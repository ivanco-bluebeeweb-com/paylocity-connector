"""Extension declaration, capabilities, health check for Paylocity Connector."""
from __future__ import annotations
import json
from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "paylocity-connector",
    version="0.1.0",
    display_name="Paylocity",
    icon="icon.svg",
    capabilities=["paylocity:manage"],
    description="Official Imperal connector for Paylocity (C28. Payroll & Benefits Administration). Manage operations securely."
)

chat = ChatExtension(ext)

@ext.health_check
async def health_check(ctx) -> dict:
    raw = await ctx.secrets.get("paylocity_connections")
    try:
        count = len(json.loads(raw)) if raw else 0
    except Exception:
        count = 0
    return {
        "healthy": True,
        "detail": f"{count} Paylocity connection(s) configured." if count else "Not connected yet."
    }
