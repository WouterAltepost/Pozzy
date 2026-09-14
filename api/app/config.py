"""Environment driven configuration.

Required variables fail loudly at startup. Optional integration variables are
read with None defaults and are not validated in milestone 1.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_DOTENV = REPO_ROOT / ".env"

REQUIRED = ("DATABASE_URL", "SUPABASE_URL", "SUPABASE_JWT_SECRET", "SECRET_KEY", "TZ")

OPTIONAL_DEFAULTS = {
    "SUPABASE_ANON_KEY": None,
    "ANTHROPIC_API_KEY": None,
    "CLAUDE_MODEL_FAST": "claude-haiku-4-5",
    "CLAUDE_MODEL_SMART": "claude-sonnet-4-5",
    "ICLOUD_USERNAME": None,
    "ICLOUD_APP_PASSWORD": None,
    "ICLOUD_CALDAV_URL": "https://caldav.icloud.com",
    "MAIL_ACCOUNTS_JSON": None,
    "RUN_SCHEDULER": None,
}


def is_production(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("FLASK_ENV") == "production" or bool(env.get("RAILWAY_ENVIRONMENT"))


def load_root_dotenv() -> None:
    """Load the single repo-root .env for local development only.

    Railway injects variables directly, so nothing is loaded in production.
    Existing environment variables always win (override=False).
    """
    if is_production():
        return
    if ROOT_DOTENV.exists():
        load_dotenv(ROOT_DOTENV, override=False)


def _sqlalchemy_url(url: str) -> str:
    # Supabase hands out postgresql:// URLs; we use the psycopg 3 driver.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def build_config(overrides: dict | None = None) -> dict:
    env = dict(os.environ)
    env.update({k: v for k, v in (overrides or {}).items() if isinstance(v, str)})

    missing = [key for key in REQUIRED if not env.get(key)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
            + ". See .env.example at the repo root."
        )

    cfg = {key: env[key] for key in REQUIRED}
    for key, default in OPTIONAL_DEFAULTS.items():
        cfg[key] = env.get(key) or default

    cfg["WEB_ORIGIN"] = (env.get("WEB_ORIGIN") or "http://localhost:5173").rstrip("/")
    cfg["ENV_NAME"] = "production" if is_production(env) else "development"

    cfg["SQLALCHEMY_DATABASE_URI"] = _sqlalchemy_url(cfg["DATABASE_URL"])
    cfg["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    cfg["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    cfg["JSON_SORT_KEYS"] = False
    return cfg
