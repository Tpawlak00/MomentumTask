from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from book.models import Book
from schemas.schemas import BookCreateRequest, BookResponse


def get_book(db: Session, serial_num: str) -> Book:
    book = db.scalar(select(Book).where(Book.serial_num == serial_num))
    if book is None:
        raise HTTPException(404, "Book not found")
    return book


def create_book(db: Session, data: BookCreateRequest) -> BookResponse:
    book = Book(**data.model_dump())
    db.add(book)
    try:
        db.flush()
        response = BookResponse.model_validate(book)
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(Book.id).where(Book.serial_num == data.serial_num)) is not None:
            raise HTTPException(409, "Book with this serial number already exists") from None
        raise
    return response


def list_books(db: Session, limit: int, offset: int) -> dict:
    total = db.scalar(select(func.count()).select_from(Book))
    items = db.scalars(select(Book).order_by(Book.id).limit(limit).offset(offset)).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def change_borrowing(db: Session, serial_num: str, borrowed_by: str | None) -> BookResponse:
    borrowing = borrowed_by is not None
    # Atomic condition prevents competing borrowers from overwriting each other.
    result = db.execute(
        update(Book)
        .where(Book.serial_num == serial_num, Book.is_borrowed == (not borrowing))
        .values(
            is_borrowed=borrowing,
            borrowed_by=borrowed_by,
            borrowed_at=datetime.now(timezone.utc) if borrowing else None,
        )
        .returning(Book)
        .execution_options(synchronize_session=False, populate_existing=True)
    )
    book = result.scalar_one_or_none()
    if book is None:
        db.rollback()
        get_book(db, serial_num)
        raise HTTPException(409, "Book is already borrowed" if borrowing else "Book is not borrowed")
    # Snapshot the operation's result before commit releases the row lock.
    response = BookResponse.model_validate(book)
    db.commit()
    return response


def delete_book(db: Session, serial_num: str) -> None:
    deleted_id = db.scalar(delete(Book).where(Book.serial_num == serial_num).returning(Book.id))
    if deleted_id is None:
        raise HTTPException(404, "Book not found")
    db.commit()
