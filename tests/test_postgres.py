"""Run only against a disposable database: TEST_DATABASE_URL=postgresql+psycopg://..."""
from concurrent.futures import ThreadPoolExecutor
import os
from threading import Barrier

from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session

from book import crud
from configs.config import Config as AppConfig
from db.database import Base, get_db
from main import app
from schemas.schemas import BookCreateRequest

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_engine(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL must point to an empty disposable PostgreSQL database")
    engine = create_engine(url)
    if inspect(engine).get_table_names():
        engine.dispose()
        pytest.fail("Refusing to run: TEST_DATABASE_URL database must be empty")
    monkeypatch.setattr(AppConfig, "DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "0001")
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO books (serial_num, title, author, is_borrowed, borrowed_by, borrowed_at) "
            "VALUES (654321, 'Legacy', 'Author', true, 123456, '2024-03-13 10:00:00')"
        ))
    command.upgrade(config, "head")
    with Session(engine) as session:
        legacy = crud.get_book(session, "654321")
        assert legacy.borrowed_by == "123456"
        assert legacy.borrowed_at.isoformat() == "2024-03-13T10:00:00+00:00"
    try:
        yield engine
    finally:
        # Drop only objects created above, in this explicitly disposable test database.
        Base.metadata.drop_all(engine)
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE alembic_version"))
        engine.dispose()


def test_concurrent_borrowers_and_duplicate_creation(postgres_engine):
    barrier = Barrier(2)
    data = BookCreateRequest(serial_num="001234", title="Dune", author="Herbert")

    def create():
        with Session(postgres_engine) as session:
            barrier.wait(timeout=10)
            try:
                crud.create_book(session, data)
                return 201
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: create(), range(2))) == [201, 409]

    def borrow(borrower):
        with Session(postgres_engine) as session:
            barrier.wait(timeout=10)
            try:
                result = crud.change_borrowing(session, "001234", borrower)
                return 200, result.borrowed_by
            except HTTPException as error:
                return error.status_code, borrower

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(borrow, ["000123", "000456"]))
    assert sorted(status for status, _ in results) == [200, 409]
    winner = next(borrower for status, borrower in results if status == 200)
    with Session(postgres_engine) as session:
        book = crud.get_book(session, "001234")
        assert book.borrowed_by == winner
        assert book.borrowed_at.tzinfo is not None
    with Session(postgres_engine) as session:
        book = crud.change_borrowing(session, "001234", None)
        assert (book.is_borrowed, book.borrowed_by, book.borrowed_at) == (False, None, None)


def test_api_with_migrated_postgres(postgres_engine):
    def database():
        with Session(postgres_engine) as session:
            yield session

    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client:
            response = client.post("/books/", json={
                "serial_num": "000001", "title": "Dune", "author": "Herbert",
            })
            assert response.status_code == 201
            assert response.json()["serial_num"] == "000001"
            response = client.post("/books/000001/borrow", json={"borrowed_by": "000002"})
            assert response.status_code == 200
            assert response.json()["borrowed_by"] == "000002"
            assert response.json()["borrowed_at"].endswith(("Z", "+00:00"))
            assert client.post("/books/000001/return").json()["borrowed_by"] is None
            assert client.get("/books/?limit=1&offset=1").json()["total"] == 2
            assert client.delete("/books/000001").status_code == 204
            assert client.get("/books/000001").status_code == 404
    finally:
        app.dependency_overrides.clear()
    command.check(Config("alembic.ini"))


def test_borrow_response_is_snapshot_before_competing_return(postgres_engine):
    with Session(postgres_engine) as session:
        crud.create_book(session, BookCreateRequest(serial_num="000001", title="Dune", author="Herbert"))

        def return_after_commit(_):
            with Session(postgres_engine) as other:
                crud.change_borrowing(other, "000001", None)

        # Deterministically perform a competing return between commit and response.
        event.listen(session, "after_commit", return_after_commit, once=True)
        response = crud.change_borrowing(session, "000001", "000002")
        assert response.is_borrowed is True
        assert response.borrowed_by == "000002"
    with Session(postgres_engine) as session:
        assert crud.get_book(session, "000001").is_borrowed is False


def test_create_response_survives_competing_deletion(postgres_engine):
    with Session(postgres_engine) as session:
        def delete_after_commit(_):
            with Session(postgres_engine) as other:
                crud.delete_book(other, "000001")

        event.listen(session, "after_commit", delete_after_commit, once=True)
        response = crud.create_book(session, BookCreateRequest(serial_num="000001", title="Dune", author="Herbert"))
        assert response.serial_num == "000001"
        assert response.id is not None
    with Session(postgres_engine) as session:
        with pytest.raises(HTTPException) as error:
            crud.get_book(session, "000001")
        assert error.value.status_code == 404
