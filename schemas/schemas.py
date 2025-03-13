from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BookCreateRequest(BaseModel):
    serial_num: int = Field(..., example=123456, description="Unikalny 6-cyfrowy numer seryjny książki")
    title: str = Field(..., example="Władca Pierścieni", description="Tytuł książki")
    author: str = Field(..., example="J.R.R. Tolkien", description="Autor książki")
    is_borrowed: bool = Field(default=False, example=False, description="Czy książka jest wypożyczona")
    borrowed_by: Optional[int] = Field(default=None, example=100100, description="ID użytkownika wypożyczającego (6 cyfr)")
    borrowed_at: Optional[datetime] = Field(default=None, example="2024-03-13T10:00:00", description="Data wypożyczenia")

class BookUpdateRequest(BaseModel):
    serial_num: int = Field(..., example=123456, description="Unikalny 6-cyfrowy numer seryjny książki")
    is_borrowed: bool = Field(..., example=True, description="Czy książka jest wypożyczona")
    borrowed_by: Optional[int] = Field(default=None, example=100100, description="ID użytkownika wypożyczającego (6 cyfr)")
    borrowed_at: Optional[datetime] = Field(default=None, example="2024-03-13T10:00:00", description="Data wypożyczenia")

class ErrorResponse(BaseModel):
    detail: str = Field(..., example="Opis błędu")
