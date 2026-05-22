"""
utils.py — shared helpers for Google Flow Veo execution scripts.

Provides:
  - load_env()          → load .env from project root
  - get_headers()       → build auth headers from env
  - log(msg)            → timestamped stdout print
  - require_env(key)    → assert env var is set, raise clear error if not
"""

import os
import sys
import datetime
from pathlib import Path


def load_env() -> None:
    """
    Load .env from the project root (two levels up from this file).
    Uses python-dotenv if available; otherwise falls back to manual parsing.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        log(f"WARNING: No .env file found at {env_path}. Copy .env.example → .env and fill in values.")
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        log(f"Loaded .env from {env_path}")
    except ImportError:
        # Manual fallback
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
        log(f"Loaded .env (manual) from {env_path}")


def require_env(key: str) -> str:
    """Return os.environ[key] or raise a clear error."""
    value = os.environ.get(key)
    if not value:
        print(f"ERROR: Required environment variable '{key}' is not set.", file=sys.stderr)
        print(f"       Add it to your .env file (see .env.example).", file=sys.stderr)
        sys.exit(1)
    return value


def get_headers() -> dict:
    """Build standard Authorization headers using GOOGLE_API_KEY."""
    api_key = require_env("GOOGLE_API_KEY")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def log(msg: str) -> None:
    """Print a timestamped log line to stdout."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)
