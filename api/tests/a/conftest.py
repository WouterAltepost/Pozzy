import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import Area
from conftest import bearer


@pytest.fixture
def headers(token_factory):
    return bearer(token_factory())


@pytest.fixture
def areas(app):
    rows = db.session.scalars(select(Area).order_by(Area.sort_order)).all()
    return {a.name: str(a.id) for a in rows}
