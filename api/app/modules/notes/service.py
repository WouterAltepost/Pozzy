from sqlalchemy import or_, select

from ...extensions import db
from ...models import Area, Note
from ...utils.validation import ValidationError, to_uuid


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def list_notes(area_id=None, tag: str | None = None, q: str | None = None) -> list[Note]:
    stmt = select(Note)
    if area_id:
        stmt = stmt.where(Note.area_id == area_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Note.title.ilike(like), Note.body.ilike(like)))
    rows = db.session.scalars(stmt.order_by(Note.pinned.desc(), Note.updated_at.desc())).all()
    if tag:
        rows = [n for n in rows if tag in (n.tags or [])]
    return rows


def get_note(note_id) -> Note | None:
    key = to_uuid(note_id)
    return db.session.get(Note, key) if key else None


def create_note(fields: dict) -> Note:
    _check_area(fields.get("area_id"))
    note = Note(**fields)
    db.session.add(note)
    db.session.commit()
    return note


def update_note(note: Note, fields: dict) -> Note:
    if "area_id" in fields:
        _check_area(fields["area_id"])
    for key, value in fields.items():
        setattr(note, key, value)
    db.session.commit()
    return note


def delete_note(note: Note) -> None:
    db.session.delete(note)
    db.session.commit()
