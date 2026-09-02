from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from regret.cli.client import ApiClient
from regret.errors import RegretError

mcp = MCPServer("regret")


def _api() -> ApiClient:
    return ApiClient()


def _call(method: str, path: str, **kwargs: Any) -> str:
    client = _api()
    try:
        if method == "GET":
            data = client.get(path, **kwargs)
        elif method == "POST":
            data = client.post(path, **kwargs)
        elif method == "DELETE":
            data = client.delete(path, **kwargs)
        else:
            return json.dumps({"error": "unsupported_method"})
    except RegretError as exc:
        return json.dumps(exc.to_dict())
    return json.dumps(data, default=str)


@mcp.tool()
def regret_get_account() -> str:
    """Retrieve the authenticated user's real Alpaca account snapshot."""
    return _call("GET", "/api/account")


@mcp.tool()
def regret_get_portfolio() -> str:
    """Retrieve the authenticated user's real Alpaca portfolio and positions."""
    return _call("GET", "/api/portfolio")


@mcp.tool()
def regret_analyze_trade(
    text: str = "",
    symbol: str = "",
    side: str = "buy",
    notional: str = "",
    quantity: str = "",
    stop_price: str = "",
    target_price: str = "",
) -> str:
    """Analyze a proposed trade through the REGRET decision engine. Does not execute."""
    body: dict[str, Any] = {}
    if text:
        body["text"] = text
    if symbol:
        body["symbol"] = symbol
        body["side"] = side
    if notional:
        body["notional"] = notional
    if quantity:
        body["quantity"] = quantity
    if stop_price:
        body["stop_price"] = stop_price
    if target_price:
        body["target_price"] = target_price
    return _call("POST", "/api/analyze", json=body)


@mcp.tool()
def regret_check_rules() -> str:
    """List the user's Trading Constitution rules."""
    return _call("GET", "/api/rules")


@mcp.tool()
def regret_calculate_risk(
    symbol: str,
    side: str = "buy",
    notional: str = "",
    quantity: str = "",
    stop_price: str = "",
    target_price: str = "",
) -> str:
    """Run a full analysis and return the deterministic risk block only."""
    raw = regret_analyze_trade(
        symbol=symbol,
        side=side,
        notional=notional,
        quantity=quantity,
        stop_price=stop_price,
        target_price=target_price,
    )
    data = json.loads(raw)
    if "decision" in data:
        return json.dumps(data["decision"].get("risk") or data, default=str)
    return raw


@mcp.tool()
def regret_find_setups(notional: str = "1000") -> str:
    """Scan the user's watchlist with the shared decision engine."""
    return _call("POST", "/api/setups", json={"notional": notional, "side": "buy"})


@mcp.tool()
def regret_get_portfolio_context() -> str:
    """Return the user's real portfolio context. Empty if no brokerage is connected."""
    return _call("GET", "/api/portfolio")


@mcp.tool()
def regret_create_order_proposal(analysis_id: str) -> str:
    """Create an order proposal/preview. Does not submit to Alpaca."""
    return _call("POST", "/api/orders/preview", json={"analysis_id": analysis_id})


@mcp.tool()
def regret_create_trade_plan(analysis_id: str) -> str:
    """Create an order preview and approval record. Does not execute."""
    return regret_create_order_proposal(analysis_id)


@mcp.tool()
def regret_review_order(approval_id: str) -> str:
    """Describe how to review an approval. Does not execute and does not invent order state."""
    return json.dumps(
        {
            "approval_id": approval_id,
            "submitted": False,
            "message": "Review the proposal from regret_create_order_proposal. Then call regret_execute_approved_order with confirm=true. This tool cannot send an order.",
        }
    )


@mcp.tool()
def regret_approve_order(approval_id: str, confirm: bool = False) -> str:
    """Approve and send a previously previewed order. confirm must be true."""
    return regret_execute_trade(approval_id, confirm=confirm)


@mcp.tool()
def regret_execute_approved_order(approval_id: str, confirm: bool = False) -> str:
    """Execute a previously approved order through REGRET safety checks. Not a raw Alpaca place_order."""
    return regret_execute_trade(approval_id, confirm=confirm)


@mcp.tool()
def regret_get_order_status(order_id: str) -> str:
    """Refresh and return the real Alpaca order status. Submitted is not filled."""
    return _call("GET", f"/api/orders/{order_id}")


@mcp.tool()
def regret_get_trade_status(order_id: str) -> str:
    """Refresh and return the real Alpaca order status."""
    return regret_get_order_status(order_id)


@mcp.tool()
def regret_monitor_trade(symbol: str) -> str:
    """Monitor an open thesis for a symbol using live market data."""
    return _call("GET", f"/api/monitor/{symbol}")


@mcp.tool()
def regret_get_journal() -> str:
    """Return the user's real decision journal."""
    return _call("GET", "/api/journal")


@mcp.tool()
def regret_get_behavior_insights() -> str:
    """Return behavioral insights only when enough real trades exist."""
    return _call("GET", "/api/insights")


@mcp.tool()
def regret_execute_trade(approval_id: str, confirm: bool = False) -> str:
    """
    Execute a previously previewed trade.

    This tool cannot bypass the approval gate. An approval_id from
    regret_create_trade_plan is required, and confirm must be true.
    """
    if not confirm:
        return json.dumps(
            {
                "error": "approval_required",
                "message": "Explicit confirmation is required. Call regret_create_trade_plan first, then regret_execute_trade with confirm=true and the approval_id.",
            }
        )
@mcp.tool()
def regret_options_scan(symbols: str = "SPY,QQQ,IWM", min_iv_rank: int = 50) -> str:
    """Scan options chains for high IV Rank and credit spread opportunities with risk gate checks."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return _call("POST", "/api/analyze/options", json={"symbols": sym_list, "min_iv_rank": min_iv_rank})


@mcp.tool()
def regret_agent_run_cycle() -> str:
    """Trigger a single autonomous AI trading agent cycle (market scan, risk checks, and execution)."""
    return _call("POST", "/api/agent/run")


@mcp.tool()
def regret_agent_stats() -> str:
    """Return Alpaca Hackathon competition stats ($100k starting balance baseline, net P&L, and open positions)."""
    return _call("GET", "/api/agent/stats")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

