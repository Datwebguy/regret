from __future__ import annotations

import json
from typing import Any

import httpx

from regret.config import Settings, get_settings
from regret.engine.intent import ParsedIntent, parse_trade_text, validate_intent
from regret.logging_utils import get_logger

log = get_logger("llm")


def parse_intent_from_text(text: str, settings: Settings | None = None) -> ParsedIntent:
    """Parse with the deterministic regex engine first. Optionally refine via LLM."""
    deterministic = parse_trade_text(text)
    settings = settings or get_settings()
    if not settings.llm_configured:
        return deterministic
    refined = _llm_parse(text, settings)
    if refined is None:
        deterministic.notes.append("AI parse unavailable. Using deterministic parser only.")
        return deterministic
    merged = validate_intent(
        symbol=refined.get("symbol") or deterministic.symbol,
        side=refined.get("side") or (deterministic.side.value if deterministic.side else None),
        notional=refined.get("notional") if refined.get("notional") is not None else deterministic.notional,
        quantity=refined.get("quantity") if refined.get("quantity") is not None else deterministic.quantity,
        order_type=refined.get("order_type") or (deterministic.order_type.value if deterministic.order_type else None),
        limit_price=refined.get("limit_price") if refined.get("limit_price") is not None else deterministic.limit_price,
        stop_price=refined.get("stop_price") if refined.get("stop_price") is not None else deterministic.stop_price,
        target_price=refined.get("target_price") if refined.get("target_price") is not None else deterministic.target_price,
    )
    merged.raw_text = text
    merged.parse_source = "llm+validated"
    merged.notes.append("Natural language was parsed by the model and then validated by REGRET.")
    return merged


def explain_decision(payload: dict[str, Any], settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    if not settings.llm_configured:
        return None
    prompt = (
        "You explain a trading decision. You must not invent numbers. "
        "Only restate and explain the provided JSON. If a field is null, say it is unavailable. "
        "Be calm, concise, and non-promissory. Never guarantee outcomes.\n\n"
        f"{json.dumps(payload, default=str)[:8000]}"
    )
    text = _chat(prompt, settings)
    return text


def _llm_parse(text: str, settings: Settings) -> dict[str, Any] | None:
    prompt = (
        "Extract a trade intent as JSON with keys: symbol, side, notional, quantity, "
        "order_type, limit_price, stop_price, target_price. Use null when unknown. "
        "side must be buy or sell. Do not invent a stop or target if the user did not state one.\n\n"
        f"User: {text}"
    )
    raw = _chat(prompt, settings, json_mode=True)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def generate_options_thesis(
    symbol: str,
    iv_rank: float,
    stock_price: float,
    candidate_summary: str,
    macro_context: str = "",
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Generate structured strategic options thesis using Featherless AI open-source models."""
    settings = settings or get_settings()
    fallback_reasoning = (
        f"{symbol} at ${stock_price:.2f} displays elevated IV Rank ({iv_rank:.1f}%), "
        f"offering favorable statistical edge for defined-risk credit spreads."
    )
    if not settings.llm_configured:
        return {
            "thesis": fallback_reasoning,
            "regime": "High Volatility Reversion",
            "confidence": "high" if iv_rank > 70 else "medium",
            "provider": "deterministic",
        }

    prompt = (
        f"You are an elite quantitative options strategist analyzing {symbol} trading at ${stock_price:.2f}.\n"
        f"Market Metrics: IV Rank = {iv_rank:.1f}%. Candidates: {candidate_summary}.\n"
        f"{'Macro/News Context: ' + macro_context if macro_context else ''}\n\n"
        f"Provide a structured strategic thesis as JSON with keys:\n"
        f"- 'regime': short description of volatility/market regime (e.g. 'Elevated IV Rangebound')\n"
        f"- 'thesis': 2-sentence rationale for opening a defined-risk credit spread\n"
        f"- 'risk_focus': key risk factor to watch (e.g. 'Pin risk near $580 resistance')\n"
        f"- 'confidence': 'high', 'medium', or 'low'\n"
        f"Do not invent prices or guarantees. Respond ONLY with valid JSON."
    )
    raw = _chat(prompt, settings, json_mode=True)
    if raw:
        try:
            parsed = json.loads(raw)
            parsed["provider"] = f"featherless:{settings.effective_llm_model}"
            return parsed
        except Exception:
            pass

    return {
        "thesis": fallback_reasoning,
        "regime": "Elevated Implied Volatility",
        "confidence": "high" if iv_rank > 70 else "medium",
        "provider": "fallback",
    }


def _chat(prompt: str, settings: Settings, json_mode: bool = False) -> str | None:
    api_key = settings.effective_llm_api_key
    if not api_key:
        return None
    url = settings.effective_llm_base_url.rstrip("/") + "/chat/completions"
    model = settings.effective_llm_model
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
    except httpx.HTTPError:
        log.info("llm_unavailable transport_error")
        return None
    if response.status_code >= 400:
        log.info("llm_unavailable status=%s", response.status_code)
        return None
    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError):
        return None

