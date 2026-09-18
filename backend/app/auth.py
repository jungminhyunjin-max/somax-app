import os
import secrets

from fastapi import Header, HTTPException, status

_ENV_VAR = "BANDIT_API_KEY"
_generated_key: str | None = None


def _dev_fallback_key() -> str:
    global _generated_key
    if _generated_key is None:
        _generated_key = secrets.token_urlsafe(24)
        print(
            f"[warn] {_ENV_VAR} not set — generated a dev-only API key: {_generated_key}\n"
            "        Set BANDIT_API_KEY in the environment for real deployments."
        )
    return _generated_key


def get_api_key() -> str:
    return os.environ.get(_ENV_VAR) or _dev_fallback_key()


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    expected = get_api_key()
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing X-API-Key")
