"""
Live Alpaca PAPER checks. Skipped unless paper credentials exist in the environment.

Never invents balances or prices. Asserts structure and truthful behavior only.
"""

from __future__ import annotations

import os

import pytest

from regret.brokers.alpaca import AlpacaCredentials
from regret.config import get_settings, reset_settings_cache
from regret.providers.alpaca import AlpacaProvider


def _paper_creds():
    reset_settings_cache()
    settings = get_settings()
    key = settings.alpaca_api_key or os.environ.get("ALPACA_API_KEY", "")
    secret = settings.alpaca_secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
    if not key or not secret:
        return None
    return AlpacaCredentials(environment="paper", api_key_id=key, api_secret=secret)


pytestmark = pytest.mark.skipif(_paper_creds() is None, reason="Alpaca paper credentials are not configured")


def test_paper_account_positions_orders_and_market_structure():
    provider = AlpacaProvider(_paper_creds(), account_access=True)
    account = provider.get_account()
    public = account.as_public_dict()
    assert public["status"] is None or isinstance(public["status"], str)
    for field in ("equity", "cash", "buying_power", "portfolio_value"):
        assert public[field] is None or isinstance(public[field], str)
        if public[field] is not None:
            assert public[field] != ""
    positions = provider.get_positions()
    assert isinstance(positions, list)
    for position in positions:
        assert position.symbol
        if position.qty is None:
            assert position.as_public_dict()["qty"] is None
    orders = provider.get_orders(status="open")
    assert isinstance(orders, list)
    market = provider.get_market_data("AAPL")
    assert market.symbol == "AAPL"
    assert market.available in {True, False}
    if not market.available:
        assert market.unavailable_reason
    else:
        assert market.source
        assert market.freshness is not None
