# 📚 MOMENTUM - ZADANIE REKRUTACYJNE

Aplikacja do zarządzania katalogiem książek w bibliotece, napisana w FastAPI.
Umożliwia dodawanie, usuwanie i aktualizowanie książek oraz ich statusów wypożyczenia.

## 🛠 Wymagania wstępne

Aby uruchomić aplikację lokalnie, upewnij się, że masz zainstalowane:
- **Docker** oraz **Docker Compose**
- **Python 3.11+** (jeśli chcesz uruchomić lokalnie bez Dockera)

## 🚀 Uruchamianie aplikacji za pomocą Docker Compose

1. **Sklonuj repozytorium** (jeśli jeszcze go nie masz):
   ```bash
   git clone https://github.com/Tpawlak00/MomentumTask.git
   cd MomentumTask
   ```

2. **Uruchom kontener z aplikacją:**
   ```bash
   docker-compose up --build
   ```

3. **Aplikacja powinna działać pod adresem:**
   - **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

4. Aby zatrzymać kontener, użyj:
   ```bash
   docker-compose down
   ```

## 📜 Endpointy API

### 1️⃣ Sprawdzenie działania API
- **GET** `/books/am-i-working`
- **Opis:** Sprawdza, czy API działa poprawnie.
- **Przykładowa odpowiedź:**
  ```json
  { "message": "Yes, /book works" }
  ```

### 2️⃣ Pobranie wszystkich książek
- **GET** `/books/`
- **Opis:** Pobiera listę wszystkich książek w bazie.
- **Przykładowa odpowiedź:**
  ```json
  [
    {
      "serial_num": 123456,
      "title": "Władca Pierścieni",
      "author": "J.R.R. Tolkien",
      "is_borrowed": false,
      "borrowed_by": null,
      "borrowed_at": null
    }
  ]
  ```

### 3️⃣ Dodanie nowej książki
- **POST** `/books/`
- **Opis:** Dodaje nową książkę do systemu.
- **Body (JSON):**
  ```json
  {
    "serial_num": 123456,
    "title": "Władca Pierścieni",
    "author": "J.R.R. Tolkien",
    "is_borrowed": false
  }
  ```
- **Kody błędów:**
  - `401` - Niepoprawny format numeru seryjnego (powinno być 6 cyfr).
  - `402` - Książka już istnieje w bazie.

### 4️⃣ Usunięcie książki
- **DELETE** `/books/{serial_num}`
- **Opis:** Usuwa książkę z systemu na podstawie numeru seryjnego.
- **Kody błędów:**
  - `411` - Niepoprawny format numeru seryjnego.
  - `412` - Książka nie istnieje w bazie.

### 5️⃣ Aktualizacja książki
- **PUT** `/books/`
- **Opis:** Aktualizuje status wypożyczenia książki.
- **Body (JSON):**
  ```json
  {
    "serial_num": 123456,
    "is_borrowed": true,
    "borrowed_by": 100100,
    "borrowed_at": "2024-03-13T10:00:00"
  }
  ```
- **Kody błędów:**
  - `401` - Niepoprawny format numeru seryjnego.
  - `403` - Brak ID użytkownika przy wypożyczonej książce.
  - `405` - Brak daty wypożyczenia.
  - `412` - Książka nie istnieje w bazie.

## 🛠 Uruchamianie aplikacji lokalnie (bez Dockera)

1. **Zainstaluj wymagane zależności:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Uruchom aplikację:**
   ```bash
   uvicorn main:app --reload
   ```

3. **API będzie dostępne pod adresem:**
   - **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📌 Uwagi
- Wszystkie numery seryjne i ID użytkowników powinny mieć dokładnie **6 cyfr**.
- Każda książka może być tylko **raz dodana** – unikalność numeru seryjnego jest wymagana.
- Jeśli książka jest oznaczona jako wypożyczona, wymagane jest **ID użytkownika oraz data wypożyczenia**.


