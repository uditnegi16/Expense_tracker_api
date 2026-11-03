from sqlmodel import select

from models import User


def test_database_is_empty(session):
    assert session.exec(select(User)).all() == []