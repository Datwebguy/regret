from __future__ import annotations

from sqlalchemy.orm import Session

from regret.services import connections

PORTFOLIO_UNAVAILABLE = "Portfolio check unavailable because no brokerage is connected."


def get_book(db: Session, user_id: str, environment: str | None = None) -> dict:
    conn = connections.connection_for_execution(db, user_id, environment)
    if conn is None:
        return {
            "connected": False,
            "account": None,
            "positions": [],
            "orders": [],
            "message": "Your portfolio is not connected yet.",
            "reason": PORTFOLIO_UNAVAILABLE,
        }
    book = connections.provider_for(conn).book()
    book["connection"] = connections.public_connection(conn)
    return book


def get_positions(db: Session, user_id: str, environment: str | None = None) -> dict:
    book = get_book(db, user_id, environment)
    if not book.get("connected"):
        return {
            "connected": False,
            "positions": [],
            "message": book.get("message"),
            "reason": book.get("reason"),
        }
    return {
        "connected": True,
        "environment": book.get("environment"),
        "positions": book.get("positions") or [],
    }


def get_orders(db: Session, user_id: str, environment: str | None = None) -> dict:
    book = get_book(db, user_id, environment)
    if not book.get("connected"):
        return {
            "connected": False,
            "orders": [],
            "message": "Connect a brokerage to see open brokerage orders.",
        }
    return {
        "connected": True,
        "environment": book.get("environment"),
        "orders": book.get("orders") or [],
    }
