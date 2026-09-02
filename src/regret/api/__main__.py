from __future__ import annotations

import uvicorn

from regret.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "regret.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.regret_env == "development",
    )


if __name__ == "__main__":
    main()
