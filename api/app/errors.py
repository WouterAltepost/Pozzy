"""Response envelope helpers and JSON error handlers.

Every response is {"data": ..., "error": null} or
{"data": null, "error": {"code": ..., "message": ...}}.
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def ok(data, status: int = 200):
    return jsonify({"data": data, "error": None}), status


def fail(code: str, message: str, status: int):
    return jsonify({"data": None, "error": {"code": code, "message": message}}), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        code = (exc.name or "error").lower().replace(" ", "_")
        return fail(code, exc.description or exc.name, exc.code or 500)

    if app.testing:
        # Let unexpected exceptions surface in pytest instead of a 500 envelope.
        return

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled error")
        return fail("internal_error", "Internal server error", 500)
