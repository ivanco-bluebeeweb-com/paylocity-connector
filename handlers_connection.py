"""Connection lifecycle for Paylocity Connector."""
from __future__ import annotations
import json, uuid
from imperal_sdk import ActionResult
from paylocity_client import PaylocityClient
from app import chat
from schemas import (
    NoParams,
    ConnectParams, ConnectionIdParams, ConnectionList, ConnectionRecord, DeleteResult
)

_SECRET = "paylocity_connections"

def _mask(value: str) -> str:
    return value[:4] + "…" + value[-4:] if len(value) > 10 else "***"

async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET)
    if not raw: return []
    try: data = json.loads(raw)
    except: return []
    return data if isinstance(data, list) else []

async def _save_connections(ctx, conns: list[dict]) -> None:
    await ctx.secrets.set(_SECRET, json.dumps(conns))

async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    conns = await _load_connections(ctx)
    if not conns: return None
    if not connection_id:
        for c in conns:
            if c.get("is_active"):
                return c
        return conns[0]
    for c in conns:
        if c["id"] == connection_id:
            return c
    return None

@chat.function(
    "connect_paylocity",
    "Connect your own Paylocity account with API Token and Company ID.",
    action_type="write",
    chain_callable=True,
    event="paylocity-connector.connect_paylocity",
    effects=["create:connection"],
    data_model=ConnectParams
)
async def connect_paylocity(ctx, params: ConnectParams) -> ActionResult[ConnectionRecord]:
    """Connect a new Paylocity company."""
    client = PaylocityClient(
        api_token=params.api_token,
        company_id=params.company_id,
        base_url=params.base_url
    )
    v_res = await client.verify_auth()
    if v_res.get("status") == "error":
        return ActionResult.error(
            f"Authentication failed: {v_res.get('message', 'invalid credentials')}",
            code=v_res.get("code", "UNAUTHORIZED")
        )

    cid = str(uuid.uuid4())
    rec = {
        "id": cid,
        "label": params.label.strip() or f"Paylocity {params.company_id}",
        "masked_key": _mask(params.api_token),
        "api_token": params.api_token,
        "company_id": params.company_id,
        "base_url": params.base_url,
        "is_active": True
    }
    conns = await _load_connections(ctx)
    for c in conns:
        c["is_active"] = False
    conns.append(rec)
    await _save_connections(ctx, conns)
    return ActionResult.success(ConnectionRecord(
        id=rec["id"],
        label=rec["label"],
        masked_key=rec["masked_key"],
        company_id=rec["company_id"],
        base_url=rec["base_url"],
        is_active=rec["is_active"]
    ), summary="Paylocity connected.")

@chat.function(
    "list_connections",
    "List connected Paylocity accounts without exposing sensitive tokens.",
    action_type="read",
    chain_callable=True,
    event="paylocity-connector.list_connections",
    data_model=NoParams
)
async def list_connections(ctx, params: NoParams) -> ActionResult[ConnectionList]:
    """List connections."""
    conns = await _load_connections(ctx)
    records = [
        ConnectionRecord(
            id=c["id"],
            label=c.get("label", ""),
            masked_key=c.get("masked_key", "***"),
            company_id=c.get("company_id", ""),
            base_url=c.get("base_url", ""),
            is_active=c.get("is_active", False)
        )
        for c in conns
    ]
    return ActionResult.success(ConnectionList(connections=records, total=len(records)), summary="Connections listed.")

@chat.function(
    "disconnect_paylocity",
    "Disconnect a Paylocity account.",
    action_type="write",
    chain_callable=True,
    event="paylocity-connector.disconnect_paylocity",
    effects=["delete:connection"],
    data_model=ConnectionIdParams
)
async def disconnect_paylocity(ctx, params: ConnectionIdParams) -> ActionResult[DeleteResult]:
    """Disconnect an account."""
    conns = await _load_connections(ctx)
    target_id = params.connection_id
    if not target_id:
        active = await resolve_connection(ctx)
        if not active:
            return ActionResult.error("No active connection to disconnect", code="NOT_FOUND")
        target_id = active["id"]

    new_conns = [c for c in conns if c["id"] != target_id]
    if len(new_conns) == len(conns):
        return ActionResult.error("Connection not found", code="NOT_FOUND")

    if new_conns and not any(c.get("is_active") for c in new_conns):
        new_conns[0]["is_active"] = True

    await _save_connections(ctx, new_conns)
    return ActionResult.success(DeleteResult(
        id=target_id,
        deleted=True,
        message="Connection removed successfully"
    ), summary="Paylocity disconnected.")
