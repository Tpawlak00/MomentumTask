from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("serial_num", name="uq_books_serial_num"),
        CheckConstraint("length(serial_num) = 6", name="ck_books_serial_length"),
        CheckConstraint("borrowed_by IS NULL OR length(borrowed_by) = 6", name="ck_books_borrower_length"),
        CheckConstraint(
            "(is_borrowed AND borrowed_by IS NOT NULL AND borrowed_at IS NOT NULL) OR "
            "(NOT is_borrowed AND borrowed_by IS NULL AND borrowed_at IS NULL)",
            name="ck_books_borrowing_state",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    serial_num: Mapped[str] = mapped_column(String(6))
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    is_borrowed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    borrowed_by: Mapped[str | None] = mapped_column(String(6))
    borrowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
