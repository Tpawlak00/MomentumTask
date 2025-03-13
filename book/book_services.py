from fastapi import APIRouter, HTTPException
from book import book_modules
from utils.logger import logger
from schemas.schemas import BookCreateRequest, BookUpdateRequest, ErrorResponse

router = APIRouter()

@router.get("/am-i-working", summary="Sprawdzenie działania API", description="Zwraca komunikat potwierdzający, że API działa poprawnie.")
async def am_i_working():
    return {"message": "Yes, /book works"}

@router.get("/", summary="Pobranie wszystkich książek", description="Zwraca listę wszystkich książek dostępnych w systemie.")
async def get_all_records():
    try:
        records = book_modules.get_all_books()
        return records
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", summary="Dodanie nowej książki", description="Pozwala dodać nową książkę do systemu.", response_model=BookCreateRequest,
             responses={
                 401: {"model": ErrorResponse, "description": "Niepoprawny format numeru seryjnego (powinno być 6 cyfr)"},
                 402: {"model": ErrorResponse, "description": "Książka o podanym numerze seryjnym już istnieje"},
                 403: {"model": ErrorResponse, "description": "Brak ID użytkownika wypożyczającego, gdy książka jest wypożyczona"},
                 405: {"model": ErrorResponse, "description": "Brak daty wypożyczenia"},
                 500: {"model": ErrorResponse, "description": "Błąd wewnętrzny serwera"}
             })
async def add_book(request: BookCreateRequest):
    try:
        return book_modules.add_new_book(**request.dict())
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Unexpected error in /add-book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{serial_num}", summary="Usunięcie książki", description="Usuwa książkę na podstawie numeru seryjnego.",
               responses={
                   411: {"model": ErrorResponse, "description": "Niepoprawny format numeru seryjnego (powinno być 6 cyfr)"},
                   412: {"model": ErrorResponse, "description": "Książka nie istnieje w bazie"},
                   500: {"model": ErrorResponse, "description": "Błąd wewnętrzny serwera"}
               })
async def delete_record(serial_num: int):
    try:
        return book_modules.delete_book(serial_num)
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/", summary="Aktualizacja informacji o książce", description="Aktualizuje status książki.",
            response_model=BookUpdateRequest,
            responses={
                401: {"model": ErrorResponse, "description": "Niepoprawny format numeru seryjnego lub ID użytkownika"},
                403: {"model": ErrorResponse, "description": "Brak ID użytkownika przy wypożyczonej książce"},
                405: {"model": ErrorResponse, "description": "Brak daty wypożyczenia"},
                412: {"model": ErrorResponse, "description": "Książka nie istnieje w bazie"},
                500: {"model": ErrorResponse, "description": "Błąd wewnętrzny serwera"}
            })
async def update_book(request: BookUpdateRequest):
    try:
        return book_modules.update_book(**request.dict())
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Unexpected error in /update-book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
