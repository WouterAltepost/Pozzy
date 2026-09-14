from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .config import build_config, load_root_dotenv
from .errors import register_error_handlers
from .extensions import db, migrate, scheduler

API_ROOT = Path(__file__).resolve().parents[1]


def create_app(overrides: dict | None = None) -> Flask:
    """Application factory.

    `overrides` is used by tests: string values are treated like environment
    variables (so required-var validation sees them), every key is also applied
    to app.config afterwards so non-string test settings (e.g. SUPABASE_JWKS)
    can be injected.
    """
    overrides = overrides or {}
    load_root_dotenv()

    app = Flask(__name__)
    app.config.update(build_config(overrides))
    app.config.update(overrides)

    CORS(
        app,
        resources={r"/api/*": {"origins": [app.config["WEB_ORIGIN"]]}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    db.init_app(app)
    migrate.init_app(app, db, directory=str(API_ROOT / "migrations"))
    # Wired only. Jobs are registered and the scheduler is started in a later milestone.
    scheduler.configure(timezone=app.config["TZ"])

    from . import models  # noqa: F401  (registers all tables on the metadata)
    from .modules.areas.routes import bp as areas_bp
    from .modules.health.routes import bp as health_bp
    from .modules.me.routes import bp as me_bp
    from .modules.settings.routes import bp as settings_bp
    from .modules.dos.routes import bp as dos_bp
    from .modules.goals.routes import bp as goals_bp
    from .modules.tasks.routes import bp as tasks_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(areas_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(dos_bp)
    app.register_blueprint(goals_bp)

    register_error_handlers(app)
    return app
