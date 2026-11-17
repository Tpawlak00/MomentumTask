from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from configs.config import Config as AppConfig


def test_migrate_existing_database_preserves_data(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "migration.db").as_posix()
    monkeypatch.setattr(AppConfig, "DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "0001")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO books (serial_num, title, author) VALUES (123456, 'Dune', 'Herbert')"))
    command.upgrade(config, "head")
    with engine.connect() as connection:
        row = connection.execute(text("SELECT serial_num, title FROM books")).one()
        assert row == ("123456", "Dune")
    assert str(inspect(engine).get_columns("books")[1]["type"]) == "VARCHAR(6)"
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO books (serial_num, title, author) VALUES ('123456', 'Dune', 'Herbert')"))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("UPDATE books SET is_borrowed = true"))
    engine.dispose()


@pytest.mark.parametrize("serials", [[12345], [1234567], [-12345], [123456, 123456]])
def test_invalid_legacy_data_is_not_silently_converted(tmp_path, monkeypatch, serials):
    url = "sqlite:///" + (tmp_path / "invalid.db").as_posix()
    monkeypatch.setattr(AppConfig, "DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "0001")
    engine = create_engine(url)
    with engine.begin() as connection:
        for serial in serials:
            connection.execute(text("INSERT INTO books (serial_num, title, author) VALUES (:serial, 'Dune', 'Herbert')"), {"serial": serial})
    with pytest.raises(RuntimeError, match="Invalid or duplicate"):
        command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT serial_num FROM books ORDER BY id")).scalars().all() == serials
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
    engine.dispose()


def test_empty_database_upgrades_to_head(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "empty.db").as_posix()
    monkeypatch.setattr(AppConfig, "DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert "books" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
    engine.dispose()
