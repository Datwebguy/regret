from __future__ import annotations

from typing import Any


class RegretError(Exception):
    """Base application error with a truthful, user-safe message."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "regret_error",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class NotFoundError(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "not_found"), status_code=404, **kwargs)


class UnauthorizedError(RegretError):
    def __init__(self, message: str = "Authentication required.", **kwargs: Any) -> None:
        super().__init__(message, code="unauthorized", status_code=401, **kwargs)


class ForbiddenError(RegretError):
    def __init__(self, message: str = "You do not have access to this resource.", **kwargs: Any) -> None:
        super().__init__(message, code="forbidden", status_code=403, **kwargs)


class IntegrationUnavailable(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            code=kwargs.pop("code", "integration_unavailable"),
            status_code=kwargs.pop("status_code", 503),
            **kwargs,
        )


class DataUnavailable(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message,
            code=kwargs.pop("code", "data_unavailable"),
            status_code=kwargs.pop("status_code", 503),
            **kwargs,
        )


class ValidationFailed(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "validation_failed"), status_code=422, **kwargs)


class ApprovalRequired(RegretError):
    def __init__(self, message: str = "Explicit approval is required before execution.", **kwargs: Any) -> None:
        super().__init__(message, code="approval_required", status_code=409, **kwargs)


class StaleDecision(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="stale_decision", status_code=409, **kwargs)


class DuplicateExecution(RegretError):
    def __init__(self, message: str = "This approved execution was already submitted.", **kwargs: Any) -> None:
        super().__init__(message, code="duplicate_execution", status_code=409, **kwargs)


class OrderRejected(RegretError):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="order_rejected", status_code=422, **kwargs)


class RateLimited(RegretError):
    def __init__(self, message: str = "Too many attempts. Try again later.", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "rate_limited"), status_code=429, **kwargs)


class CSRFRejected(RegretError):
    def __init__(self, message: str = "This request was rejected because it did not come from REGRET.", **kwargs: Any) -> None:
        super().__init__(message, code="csrf_rejected", status_code=403, **kwargs)
