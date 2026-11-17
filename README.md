# Momentum Library

Rozwiązanie zadania rekrutacyjnego ML Engineer: API dla pracowników biblioteki
do dodawania, usuwania i przeglądania książek oraz obsługi wypożyczeń i zwrotów.
Uwierzytelnianie i autoryzacja są pominięte zgodnie z treścią zadania.

Stos: Python 3.13 w Dockerze, FastAPI, Pydantic 2, SQLAlchemy 2,
PostgreSQL 18, Alembic i Poetry. Lokalnie wymagany jest Python 3.11+.

## Uruchomienie

Wymagane: Docker z uruchomionym silnikiem i Docker Compose v2.
Porty 8000 i 5432 muszą być wolne.

```sh
git clone https://github.com/Tpawlak00/MomentumTask.git
cd MomentumTask
docker compose up
```

Nie trzeba instalować Pythona ani tworzyć `.env`. Compose buduje obraz,
czeka na gotowość PostgreSQL, wykonuje migracje i uruchamia API.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Kontrola działania procesu API: http://localhost:8000/

Zatrzymanie: `docker compose down`. Dane pozostają w wolumenie `pgdata18`.
`docker compose down --volumes` usuwa również dane.
Po zmianach kodu uruchom `docker compose up --build`.
Przykładowe dane dostępowe w Compose służą do lokalnego uruchomienia.
Logi są dostępne przez `docker compose logs app`.

## API

| Metoda | URL | Operacja | Sukces |
|---|---|---|---|
| GET | `/books/?limit=20&offset=0` | Lista książek | 200 |
| POST | `/books/` | Dodanie dostępnej książki | 201 |
| GET | `/books/{serial_num}` | Pobranie jednej książki | 200 |
| DELETE | `/books/{serial_num}` | Usunięcie książki, również wypożyczonej | 204 |
| POST | `/books/{serial_num}/borrow` | Wypożyczenie | 200 |
| POST | `/books/{serial_num}/return` | Zwrot, bez body | 200 |

Dodanie przez `POST /books/`:

```json
{"serial_num": "001234", "title": "Diuna", "author": "Frank Herbert"}
```

Wypożyczenie przez `POST /books/001234/borrow`:

```json
{"borrowed_by": "000123"}
```

Dodanie, wypożyczenie i zwrot zwracają pełny obiekt książki:

```json
{
  "id": 1,
  "serial_num": "001234",
  "title": "Diuna",
  "author": "Frank Herbert",
  "is_borrowed": true,
  "borrowed_by": "000123",
  "borrowed_at": "2026-11-17T10:00:00Z"
}
```

Numery książek i kart bibliotecznych są tekstem zawierającym dokładnie sześć
cyfr ASCII, co zachowuje zera wiodące. Tytuł i autor mają 1–255 znaków po
usunięciu otaczających białych znaków. Nieznane pola wejściowe są odrzucane.
Serwer ustala stan wypożyczenia i datę UTC. Zwrot ustawia `is_borrowed=false`
oraz czyści `borrowed_by` i `borrowed_at`. Przechowywane jest aktualne
wypożyczenie, bez historii.

Lista ma postać `{"items": [], "total": 0, "limit": 20, "offset": 0}`.
Kolejne strony pobiera się przez zwiększanie `offset`; `limit` ma zakres
1–100, `offset` jest nieujemny. Książki są uporządkowane rosnąco po `id`.

Błędy: `422` dla niepoprawnych danych, `404` dla nieistniejącej książki,
`409` dla duplikatu numeru, ponownego wypożyczenia lub zwrotu dostępnej książki.
Unikalność numeru wymusza baza. Warunkowy atomowy UPDATE zapobiega nadpisaniu
czytelnika przez równoczesne żądanie wypożyczenia.

## Praca lokalna

Wymagane: Python 3.11+ i Poetry 2.2.1.

```sh
docker compose up -d db
poetry install
```

Skopiuj `.env.example` do `.env` i ustaw `DATABASE_URL`, następnie:

```sh
poetry run alembic upgrade head
poetry run uvicorn main:app --reload
```

Zależności są w `pyproject.toml` i `poetry.lock`. Migracje zastępują inicjalizację
schematu przy starcie aplikacji. Instrukcja aktualizacji starej bazy i API:
[docs/migrations.md](docs/migrations.md).

## Testy

Po `poetry install` testy API i migracji na izolowanych bazach SQLite:

```sh
poetry run pytest -m "not postgres"
```

Testy PostgreSQL obejmują migrację starego rekordu, zgodność schematu z ORM,
przepływ HTTP, równoczesne dodawanie i wypożyczanie oraz odpowiedzi przy
zwrocie lub usunięciu książki przez inną transakcję.

Uruchom osobną bazę testową i poczekaj, aż `pg_isready` potwierdzi gotowość:

```sh
docker run --rm -d --name momentum-test-db -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=momentum_test -p 127.0.0.1:55432:5432 postgres:18
docker exec momentum-test-db pg_isready -U test -d momentum_test
```

PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://test:test@127.0.0.1:55432/momentum_test"
poetry run pytest
```

Bash:

```sh
TEST_DATABASE_URL=postgresql+psycopg://test:test@127.0.0.1:55432/momentum_test poetry run pytest
```

`TEST_DATABASE_URL` musi wskazywać pustą, jednorazową bazę. Testy odmawiają
uruchomienia, jeśli zawiera tabele; po każdym teście usuwają utworzone obiekty.
Bez tej zmiennej testy PostgreSQL są pomijane. CI uruchamia cały zestaw
z PostgreSQL 18. Po testach zatrzymaj bazę przez `docker stop momentum-test-db`.
