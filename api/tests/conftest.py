"""Shared fixtures.

Database: SQLite in-memory. The models use sqlalchemy.Uuid and a JSON type
with a JSONB variant, both of which work on SQLite, so no Postgres is needed
for tests.

Auth: an EC P-256 key pair is generated per session. Its public half is
injected as a JWKS dict via config["SUPABASE_JWKS"], mirroring Supabase's
ES256 tokens. HS256 tokens are signed with the test secret.
"""
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from app import create_app
from app.extensions import db
from seeds import seed

KID = "test-kid"
JWT_SECRET = "test-hs256-secret-with-at-least-thirty-two-bytes"


@pytest.fixture(scope="session")
def ec_private_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="session")
def jwks(ec_private_key):
    jwk = ECAlgorithm.to_jwk(ec_private_key.public_key(), as_dict=True)
    jwk.update({"kid": KID, "alg": "ES256", "use": "sig"})
    return {"keys": [jwk]}


@pytest.fixture
def app(jwks):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "sqlite:///:memory:",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_JWT_SECRET": JWT_SECRET,
            "SECRET_KEY": "test",
            "TZ": "Europe/Amsterdam",
            "SUPABASE_JWKS": jwks,
        }
    )
    with app.app_context():
        db.create_all()
        seed()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_token(private_key, *, alg="ES256", kid=KID, secret=JWT_SECRET, **claim_overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": str(uuid.uuid4()),
        "email": "wout@example.com",
        "aud": "authenticated",
        "role": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(claim_overrides)
    if alg == "HS256":
        return jwt.encode(claims, secret, algorithm="HS256")
    return jwt.encode(claims, private_key, algorithm="ES256", headers={"kid": kid})


@pytest.fixture
def token_factory(ec_private_key):
    def factory(**kwargs):
        return make_token(ec_private_key, **kwargs)

    return factory


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
