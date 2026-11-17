# Migracja istniejącej bazy

Ta instrukcja dotyczy wcześniejszej wersji projektu. Nowa instalacja przez
`docker compose up` wykonuje migracje automatycznie.

Migracja `0001` odtwarza dawną tabelę `books` z identyfikatorami INTEGER.
Migracja `0002` zmienia je na VARCHAR(6), ustawia daty ze strefą czasową
i dodaje unikalność numeru oraz ograniczenia spójności wypożyczenia.

## Stara tabela bez historii Alembic

Wykonaj kopię zapasową, zatrzymaj aplikację zapisującą dane i ustaw
`DATABASE_URL` na właściwą bazę. Jeśli tabela odpowiada schematowi migracji `0001`:

```sh
poetry run alembic stamp 0001
poetry run alembic upgrade head
```

Nie używaj `stamp 0001` dla nowej, pustej bazy. Dla niej wystarczy
`poetry run alembic upgrade head`.

Migracja zatrzymuje się przy duplikatach, niepoprawnych identyfikatorach lub
niespójnym stanie wypożyczenia. Takie rekordy trzeba wcześniej poprawić;
migracja nie usuwa ani nie skraca danych automatycznie.

Historyczne daty bez strefy są traktowane jako UTC. Jeśli zapisano je w innym
czasie lokalnym, przed migracją należy je przeliczyć. Zer wiodących utraconych
w kolumnie INTEGER nie da się automatycznie odzyskać.

Migracja `0002` nie udostępnia downgrade: powrót do INTEGER utraciłby zera
wiodące. Powrót do starego schematu wymaga odtworzenia kopii zapasowej.
Migracje sprawdzają dane przez połączenie z bazą; tryb `--sql` nie jest obsługiwany.

## Przejście z PostgreSQL 15 do 18

Nowy Compose używa wolumenu `pgdata18`. Nie usuwa starego wolumenu.
Przeniesienie danych między głównymi wersjami PostgreSQL wymaga osobnego
eksportu/importu przez `pg_dump`/`pg_restore` albo procedury `pg_upgrade`.
Nie podłączaj katalogu danych PostgreSQL 15 bezpośrednio do PostgreSQL 18.
Migracje Alembic zmieniają schemat aplikacji, a nie wersję silnika bazy.

## Zmiana API

Dawne `/book` i `PUT /book/` zostały zastąpione przez `/books` oraz osobne
operacje `POST /books/{serial_num}/borrow` i `POST /books/{serial_num}/return`.
Identyfikatory w JSON są teraz tekstem. Klient nie przesyła `is_borrowed`
ani `borrowed_at`; wartości te ustala serwer.
