"""One real Haiku call through claude_client, for Wouter to run once.

    cd api && .venv/bin/python scripts/claude_smoke.py

Needs DATABASE_URL and ANTHROPIC_API_KEY in the repo root .env (the app factory
loads it). Writes one `ai_calls` row with feature "smoke" and prints it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.integrations import claude_client  # noqa: E402
from app.models import AiCall  # noqa: E402


def main() -> int:
    app = create_app()
    with app.app_context():
        model = claude_client.model_for("fast")
        print(f"model: {model}  price row: {claude_client.price_row(model)}")
        if not app.config.get("ANTHROPIC_API_KEY"):
            print("ANTHROPIC_API_KEY is not set")
            return 1
        answer = claude_client.ping("Pozzy smoke test")
        row = db.session.scalar(select(AiCall).where(AiCall.feature == "smoke").order_by(AiCall.created_at.desc()))
        print(f"answer: {answer}")
        if row is None:
            print("no ai_calls row written")
            return 1
        print(f"ai_calls {row.id}: ok={row.ok} in={row.input_tokens} out={row.output_tokens} cost=${row.cost_estimate} error={row.error}")
        return 0 if answer and row.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
