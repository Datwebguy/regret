from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from regret.cli.client import ApiClient
from regret.cli.config_store import load_config, save_config
from regret.errors import RegretError

app = typer.Typer(add_completion=False, no_args_is_help=True, help="REGRET command line")
console = Console()


def _client() -> ApiClient:
    return ApiClient()


def _show(data: object) -> None:
    console.print_json(data=data)


def _fail(exc: RegretError) -> None:
    console.print(f"[red]{exc.message}[/red]")
    raise typer.Exit(exc.status_code)


@app.command()
def setup(
    api_url: str = typer.Option("http://127.0.0.1:8000", help="REGRET API base URL"),
    email: Optional[str] = typer.Option(None),
    password: Optional[str] = typer.Option(None, prompt=False),
    register: bool = typer.Option(False, help="Create a new REGRET account"),
) -> None:
    """Configure the CLI and authenticate against the REGRET API."""
    cfg = load_config()
    cfg["api_url"] = api_url.rstrip("/")
    save_config(cfg)
    if not email or not password:
        console.print(f"Saved API URL: {cfg['api_url']}")
        console.print("Next: `regret setup --email you@domain --password ...` or `regret login`.")
        return
    client = _client()
    path = "/api/auth/register" if register else "/api/auth/login"
    try:
        result = client.post(path, json={"email": email, "password": password})
    except RegretError as exc:
        _fail(exc)
    cfg["token"] = result["token"]
    save_config(cfg)
    console.print(f"Authenticated as {result['user']['email']}")


@app.command()
def login(
    email: str = typer.Option(...),
    password: str = typer.Option(..., prompt=True, hide_input=True),
) -> None:
    setup(api_url=load_config().get("api_url", "http://127.0.0.1:8000"), email=email, password=password, register=False)


@app.command()
def status() -> None:
    client = _client()
    try:
        health = client.get("/api/health")
        me = client.get("/api/auth/me")
        alpaca = client.get("/api/alpaca/status")
    except RegretError as exc:
        _fail(exc)
    _show({"health": health, "user": me["user"], "alpaca": alpaca})


@app.command()
def portfolio() -> None:
    try:
        _show(_client().get("/api/portfolio"))
    except RegretError as exc:
        _fail(exc)


@app.command()
def analyze(
    symbol: str = typer.Argument(...),
    side: str = typer.Option("buy"),
    amount: Optional[float] = typer.Option(None, help="Notional dollar amount"),
    quantity: Optional[float] = typer.Option(None),
    stop: Optional[float] = typer.Option(None),
    target: Optional[float] = typer.Option(None),
    text: Optional[str] = typer.Option(None, help="Natural language trade request"),
) -> None:
    body: dict = {}
    if text:
        body["text"] = text
    else:
        body = {
            "symbol": symbol,
            "side": side,
            "notional": str(amount) if amount is not None else None,
            "quantity": str(quantity) if quantity is not None else None,
            "stop_price": str(stop) if stop is not None else None,
            "target_price": str(target) if target is not None else None,
        }
    try:
        result = _client().post("/api/analyze", json=body)
    except RegretError as exc:
        _fail(exc)
    decision = result.get("decision") or {}
    console.print(f"\nREGRET\n\n{result.get('intent', {}).get('symbol') or symbol}")
    console.print(f"Verdict: [bold]{result.get('verdict')}[/bold]")
    for reason in decision.get("reasons") or [result.get("summary")]:
        console.print(f"Why: {reason}")
    for i, item in enumerate((decision.get("why_not") or {}).get("items") or [], start=1):
        console.print(f"{i}. {item.get('title') or item.get('code')}: {item.get('message')}")
        if item.get("actual") or item.get("required"):
            console.print(f"   actual={item.get('actual')} required={item.get('required')}")
    proposal = result.get("order_proposal") or {}
    if proposal.get("allowed"):
        console.print("\nORDER REVIEW (not submitted)")
        console.print(f"  {proposal.get('side')} {proposal.get('symbol')} {proposal.get('estimated_notional') or proposal.get('quantity')}")
        console.print(f"  rules={proposal.get('rules')} risk_checks={proposal.get('risk_checks')}")
    else:
        console.print(f"No order proposal: {proposal.get('reason') or 'not allowed'}")
    console.print("Approval required before execution.")
    console.print(f"analysis_id: {result.get('analysis_id')}")
    _show(result)


rules_app = typer.Typer(help="Trading Constitution")
app.add_typer(rules_app, name="rules")


@rules_app.command("list")
def rules_list() -> None:
    try:
        _show(_client().get("/api/rules"))
    except RegretError as exc:
        _fail(exc)


@app.command()
def setups() -> None:
    try:
        _show(_client().get("/api/setups"))
    except RegretError as exc:
        _fail(exc)


@app.command()
def journal() -> None:
    try:
        data = _client().get("/api/journal")
    except RegretError as exc:
        _fail(exc)
    table = Table(title="Journal")
    table.add_column("When")
    table.add_column("Type")
    table.add_column("Symbol")
    table.add_column("Verdict")
    table.add_column("Action")
    table.add_column("Summary")
    for entry in data.get("entries") or []:
        table.add_row(
            entry.get("created_at") or "",
            entry.get("entry_type") or "",
            entry.get("symbol") or "",
            entry.get("verdict") or "",
            entry.get("user_action") or "",
            (entry.get("summary") or "")[:80],
        )
    console.print(table)


order_app = typer.Typer(help="Orders")
app.add_typer(order_app, name="order")


@order_app.command("status")
def order_status(order_id: str = typer.Argument(...)) -> None:
    try:
        _show(_client().get(f"/api/orders/{order_id}"))
    except RegretError as exc:
        _fail(exc)


@order_app.command("preview")
def order_preview(analysis_id: str = typer.Argument(...)) -> None:
    try:
        _show(_client().post("/api/orders/preview", json={"analysis_id": analysis_id}))
    except RegretError as exc:
        _fail(exc)


@order_app.command("confirm")
def order_confirm(
    approval_id: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", help="Required explicit confirmation"),
) -> None:
    if not yes:
        console.print("Refusing to execute without --yes.")
        raise typer.Exit(1)
    try:
        _show(_client().post("/api/orders/confirm", json={"approval_id": approval_id, "confirm": True}))
    except RegretError as exc:
        _fail(exc)


@app.command()
def monitor(symbol: str = typer.Argument(...)) -> None:
    try:
        _show(_client().get(f"/api/monitor/{symbol}"))
    except RegretError as exc:
        _fail(exc)


agent_app = typer.Typer(help="Autonomous AI Trading Agent commands")
app.add_typer(agent_app, name="agent")


@agent_app.command("run")
def agent_run(
    min_iv_rank: int = typer.Option(40, help="Minimum IV Rank threshold (0-100)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols to scan"),
) -> None:
    """Run a single autonomous scan, risk-gate check, and execution cycle."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    try:
        payload = {}
        if sym_list:
            payload["symbols"] = sym_list
        if min_iv_rank is not None:
            payload["min_iv_rank"] = min_iv_rank
        data = _client().post("/api/agent/run", json=payload)
        _show(data)
        return
    except RegretError:
        pass

    from regret.agents.autonomous_agent import AgentConfig, AutonomousOptionsAgent
    from regret.brokers.alpaca import AlpacaCredentials
    from regret.config import get_settings

    settings = get_settings()
    creds = AlpacaCredentials(
        environment=settings.regret_default_trading_environment,
        api_key_id=settings.alpaca_api_key or settings.alpaca_data_api_key_id,
        api_secret=settings.alpaca_secret_key or settings.alpaca_data_api_secret_key,
    )
    config = AgentConfig(
        environment=settings.regret_default_trading_environment,
        min_iv_rank=min_iv_rank,
    )
    if sym_list:
        config.symbols = sym_list
    agent = AutonomousOptionsAgent(creds, config=config)
    console.print(f"[cyan]Running autonomous agent cycle (Min IV Rank: {min_iv_rank}%)...[/cyan]")
    cycle_res = agent.run_cycle()
    _show(cycle_res.as_dict())


@agent_app.command("start")
def agent_start(
    interval: int = typer.Option(300, help="Scan interval in seconds (default: 300)"),
    min_iv_rank: int = typer.Option(40, help="Minimum IV Rank threshold (0-100)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols to scan"),
) -> None:
    """Start continuous 24/7 autonomous options trading loop."""
    import sys
    from regret.agents.autonomous_agent import AgentConfig, AutonomousOptionsAgent
    from regret.brokers.alpaca import AlpacaCredentials
    from regret.config import get_settings

    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    settings = get_settings()
    creds = AlpacaCredentials(
        environment=settings.regret_default_trading_environment,
        api_key_id=settings.alpaca_api_key or settings.alpaca_data_api_key_id,
        api_secret=settings.alpaca_secret_key or settings.alpaca_data_api_secret_key,
    )
    config = AgentConfig(
        environment=settings.regret_default_trading_environment,
        min_iv_rank=min_iv_rank,
        poll_interval_seconds=interval,
    )
    if sym_list:
        config.symbols = sym_list

    console.print(f"[bold green]🚀 Starting REGRET Autonomous Options Agent ({creds.environment})...[/bold green]")
    console.print(f"[cyan]📊 Symbols: {', '.join(config.symbols)} | Min IV Rank: {config.min_iv_rank}% | Poll: {interval}s[/cyan]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    agent = AutonomousOptionsAgent(creds, config=config)
    try:
        agent.run_forever(interval_seconds=interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Autonomous agent loop stopped by user.[/yellow]")
        sys.exit(0)


@agent_app.command("stats")
def agent_stats() -> None:
    """Show competition P&L metrics ($100k baseline) and agent execution status."""
    data = None
    try:
        data = _client().get("/api/agent/stats")
    except RegretError:
        pass

    if data is None:
        from regret.agents.autonomous_agent import AutonomousOptionsAgent
        from regret.brokers.alpaca import AlpacaCredentials
        from regret.config import get_settings

        settings = get_settings()
        creds = AlpacaCredentials(
            environment=settings.regret_default_trading_environment,
            api_key_id=settings.alpaca_api_key or settings.alpaca_data_api_key_id,
            api_secret=settings.alpaca_secret_key or settings.alpaca_data_api_secret_key,
        )
        agent = AutonomousOptionsAgent(creds)
        data = agent.get_stats()

    # 1. Summary Metrics Table
    table = Table(title="Alpaca Hackathon — Agent Competition Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in data.items():
        if not isinstance(v, (dict, list)):
            table.add_row(str(k), str(v))
    console.print(table)

    # 2. Live Option Positions Breakdown Table
    positions = data.get("positions_detail") or []
    if positions:
        pos_table = Table(title="Live Option Positions on Alpaca (PA3XUIGQ0VGB)")
        pos_table.add_column("Option Contract", style="cyan", no_wrap=True)
        pos_table.add_column("Side", style="magenta")
        pos_table.add_column("Qty", justify="right")
        pos_table.add_column("Entry Price", justify="right")
        pos_table.add_column("Mark Price", justify="right")
        pos_table.add_column("Unrealized P&L", justify="right", style="green")
        pos_table.add_column("Hedge Status", style="bold green")

        for pos in positions:
            side = pos.get("side", "").upper()
            pl = float(pos.get("unrealized_pl", 0.0))
            pl_style = "green" if pl >= 0 else "red"
            hedge_status = "PROTECTED (Long Wing)" if side == "LONG" else "BOUNDED (Short Premium)"
            
            pos_table.add_row(
                pos.get("symbol", ""),
                side,
                str(pos.get("qty", "")),
                f"${float(pos.get('avg_entry_price', 0)):.2f}",
                f"${float(pos.get('current_price', 0)):.2f}",
                f"[{pl_style}]${pl:+.2f}[/{pl_style}]",
                hedge_status,
            )
        console.print(pos_table)



options_app = typer.Typer(help="Options trading and screening commands")
app.add_typer(options_app, name="options")


@options_app.command("scan")
def options_scan(
    symbols: str = typer.Option("SPY,QQQ,IWM,NVDA", help="Comma-separated symbols to scan"),
    min_iv_rank: int = typer.Option(50, help="Minimum IV Rank threshold (0-100)"),
) -> None:
    """Scan options chains for high IV Rank and credit spread setups."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    try:
        data = _client().post("/api/analyze/options", json={"symbols": sym_list, "min_iv_rank": min_iv_rank})
        _show(data)
        return
    except RegretError:
        pass

    from decimal import Decimal
    from regret.brokers.alpaca import AlpacaCredentials
    from regret.config import get_settings
    from regret.services.options_strategy import OptionsStrategyService

    settings = get_settings()
    creds = AlpacaCredentials(
        environment=settings.regret_default_trading_environment,
        api_key_id=settings.alpaca_api_key or settings.alpaca_data_api_key_id,
        api_secret=settings.alpaca_secret_key or settings.alpaca_data_api_secret_key,
    )
    service = OptionsStrategyService(creds)
    console.print(f"[cyan]Scanning options for {', '.join(sym_list)} (Min IV Rank: {min_iv_rank}%)...[/cyan]")
    data = service.scan_and_propose(
        symbols=sym_list,
        min_iv_rank=min_iv_rank,
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=0,
    )
    _show(data)



if __name__ == "__main__":
    app()

