"""String identifiers, uniqueness and borrowing invariants. Legacy dates assume UTC."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # Fail before casting: PostgreSQL's explicit varchar(6) cast can truncate data.
    books = sa.table("books", *(sa.column(name) for name in (
        "serial_num", "borrowed_by", "is_borrowed", "borrowed_at",
    )))
    seen = set()
    for row in op.get_bind().execute(sa.select(books)).mappings():
        serial = str(row["serial_num"])
        borrower = str(row["borrowed_by"]) if row["borrowed_by"] is not None else None
        valid_id = lambda value: len(value) == 6 and value.isascii() and value.isdigit()
        if not valid_id(serial) or serial in seen or (borrower is not None and not valid_id(borrower)):
            raise RuntimeError("Invalid or duplicate legacy identifiers; correct the data before upgrading")
        seen.add(serial)
        if bool(row["is_borrowed"]):
            valid_state = borrower is not None and row["borrowed_at"] is not None
        else:
            valid_state = borrower is None and row["borrowed_at"] is None
        if not valid_state:
            raise RuntimeError("Inconsistent legacy borrowing state; correct the data before upgrading")
    with op.batch_alter_table("books") as batch:
        batch.alter_column("serial_num", existing_type=sa.Integer(), type_=sa.String(6),
                           existing_nullable=False, postgresql_using="serial_num::varchar(6)")
        batch.alter_column("borrowed_by", existing_type=sa.Integer(), type_=sa.String(6),
                           existing_nullable=True, postgresql_using="borrowed_by::varchar(6)")
        batch.alter_column("borrowed_at", existing_type=sa.DateTime(),
                           type_=sa.DateTime(timezone=True), existing_nullable=True,
                           postgresql_using="borrowed_at AT TIME ZONE 'UTC'")
        batch.create_unique_constraint("uq_books_serial_num", ["serial_num"])
        batch.create_check_constraint("ck_books_serial_length", "length(serial_num) = 6")
        batch.create_check_constraint("ck_books_borrower_length", "borrowed_by IS NULL OR length(borrowed_by) = 6")
        batch.create_check_constraint(
            "ck_books_borrowing_state",
            "(is_borrowed AND borrowed_by IS NOT NULL AND borrowed_at IS NOT NULL) OR "
            "(NOT is_borrowed AND borrowed_by IS NULL AND borrowed_at IS NULL)",
        )


def downgrade():
    # Keep textual IDs: converting back to int would irreversibly lose leading zeros.
    raise RuntimeError("Migration 0002 is irreversible; restore a backup to return to the legacy schema")
