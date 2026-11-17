from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Identifier = Annotated[str, StringConstraints(pattern=r"^[0-9]{6}$", min_length=6, max_length=6)]
BookText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BookCreateRequest(RequestModel):
    serial_num: Identifier
    title: BookText
    author: BookText


class BorrowRequest(RequestModel):
    borrowed_by: Identifier


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_num: Identifier
    title: str
    author: str
    is_borrowed: bool
    borrowed_by: Identifier | None
    borrowed_at: datetime | None


class BookPage(BaseModel):
    items: list[BookResponse]
    total: int
    limit: int
    offset: int
