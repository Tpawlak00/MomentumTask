from alembic import context
from sqlalchemy import create_engine, pool

from book.models import Book  # noqa: F401: register metadata
from configs.config import Config
from db.database import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_online():
    engine = create_engine(Config.DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Migrations require a database connection to validate legacy data; omit --sql")
else:
    run_migrations_online()
