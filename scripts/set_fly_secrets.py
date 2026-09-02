"""Generate production secrets and store them in Fly. Never print secret values."""

from __future__ import annotations

import secrets
import subprocess
import sys

from cryptography.fernet import Fernet


def main() -> int:
    app = sys.argv[1] if len(sys.argv) > 1 else "regret"
    secret_key = secrets.token_urlsafe(48)
    encryption_key = Fernet.generate_key().decode("utf-8")
    completed = subprocess.run(
        [
            "fly",
            "secrets",
            "set",
            f"REGRET_SECRET_KEY={secret_key}",
            f"REGRET_ENCRYPTION_KEY={encryption_key}",
            "--app",
            app,
            "--stage",
        ],
        check=False,
    )
    if completed.returncode != 0:
        print("fly_secrets_set=failed")
        return completed.returncode
    print("fly_secrets_set=ok")
    print("secret_names=REGRET_SECRET_KEY,REGRET_ENCRYPTION_KEY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
