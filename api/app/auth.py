"""Supabase JWT validation.

This project signs user access tokens with ES256 (asymmetric). The public key
is fetched from the project's JWKS endpoint and cached. The legacy HS256
secret is still accepted as a fallback in case Supabase rotates back to the
symmetric key, so both paths are covered by tests.
"""
from functools import wraps

import jwt
from flask import current_app, g, request
from jwt import PyJWKClient, PyJWKSet

from .errors import fail

AUDIENCE = "authenticated"
ASYMMETRIC_ALGS = ("ES256", "RS256")


def _jwks_url() -> str:
    return current_app.config["SUPABASE_URL"].rstrip("/") + "/auth/v1/.well-known/jwks.json"


def _asymmetric_key(token: str, header: dict):
    """Return the public key for the token's `kid`.

    Tests inject a JWKS dict via config["SUPABASE_JWKS"]; otherwise the JWKS is
    fetched once per process and cached by PyJWKClient.
    """
    injected = current_app.config.get("SUPABASE_JWKS")
    if injected:
        return PyJWKSet.from_dict(injected)[header["kid"]].key

    client = current_app.extensions.get("pozzy_jwks_client")
    if client is None:
        client = PyJWKClient(_jwks_url(), cache_keys=True, lifespan=3600)
        current_app.extensions["pozzy_jwks_client"] = client
    return client.get_signing_key_from_jwt(token).key


def decode_token(token: str) -> dict:
    """Verify signature, expiry and audience. Raises jwt.PyJWTError on failure."""
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")
    common = {"audience": AUDIENCE, "options": {"require": ["exp", "sub"]}}

    if alg == "HS256":
        return jwt.decode(token, current_app.config["SUPABASE_JWT_SECRET"], algorithms=["HS256"], **common)

    if alg in ASYMMETRIC_ALGS:
        try:
            key = _asymmetric_key(token, header)
        except jwt.PyJWTError:
            raise
        except Exception as exc:  # unknown kid, JWKS unreachable, malformed key set
            raise jwt.InvalidTokenError(f"Could not resolve signing key: {exc}") from exc
        return jwt.decode(token, key, algorithms=[alg], **common)

    raise jwt.InvalidTokenError(f"Unsupported JWT algorithm: {alg}")


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return fail("unauthorized", "Missing bearer token", 401)
        token = header[len("Bearer "):].strip()
        try:
            claims = decode_token(token)
        except jwt.DecodeError:
            return fail("unauthorized", "Malformed token", 401)
        except jwt.PyJWTError as exc:
            return fail("unauthorized", f"Invalid token: {exc}", 401)
        g.user = {"id": claims["sub"], "email": claims.get("email")}
        return view(*args, **kwargs)

    return wrapper
