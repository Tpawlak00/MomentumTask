from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from book import crud
from db.database import get_db
from schemas.schemas import BookCreateRequest, BookPage, BookResponse, BorrowRequest, Identifier

router = APIRouter(prefix="/books", tags=["books"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=BookPage)
def list_books(db: Database, limit: Annotated[int, Query(ge=1, le=100)] = 20,
               offset: Annotated[int, Query(ge=0)] = 0):
    return crud.list_books(db, limit, offset)


@router.post("/", response_model=BookResponse, status_code=201)
def create_book(request: BookCreateRequest, db: Database):
    return crud.create_book(db, request)


@router.get("/{serial_num}", response_model=BookResponse)
def get_book(serial_num: Identifier, db: Database):
    return crud.get_book(db, serial_num)


@router.post("/{serial_num}/borrow", response_model=BookResponse)
def borrow_book(serial_num: Identifier, request: BorrowRequest, db: Database):
    return crud.change_borrowing(db, serial_num, request.borrowed_by)


@router.post("/{serial_num}/return", response_model=BookResponse)
def return_book(serial_num: Identifier, db: Database):
    return crud.change_borrowing(db, serial_num, None)


@router.delete("/{serial_num}", status_code=204)
def delete_book(serial_num: Identifier, db: Database):
    crud.delete_book(db, serial_num)
    return Response(status_code=204)
