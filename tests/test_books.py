import pytest

BOOK = {"serial_num": "001234", "title": "Dune", "author": "Frank Herbert"}


def test_create_read_delete(client):
    response = client.post("/books/", json=BOOK)
    assert response.status_code == 201
    book = response.json()
    assert book == {**BOOK, "id": book["id"], "is_borrowed": False, "borrowed_by": None, "borrowed_at": None}
    assert client.get("/books/001234").json() == book
    assert client.delete("/books/001234").status_code == 204
    assert client.get("/books/001234").status_code == 404


def test_duplicate_is_conflict_and_does_not_duplicate_record(client):
    assert client.post("/books/", json=BOOK).status_code == 201
    assert client.post("/books/", json=BOOK).status_code == 409
    assert client.get("/books/").json()["total"] == 1


def test_borrow_return_and_borrow_again(client):
    client.post("/books/", json=BOOK)
    response = client.post("/books/001234/borrow", json={"borrowed_by": "000123"})
    assert response.status_code == 200
    assert response.json()["is_borrowed"] is True
    assert response.json()["borrowed_by"] == "000123"
    assert response.json()["borrowed_at"] is not None
    response = client.post("/books/001234/return")
    assert response.status_code == 200
    assert response.json()["is_borrowed"] is False
    assert response.json()["borrowed_by"] is None
    assert response.json()["borrowed_at"] is None
    assert client.post("/books/001234/borrow", json={"borrowed_by": "000456"}).status_code == 200


def test_second_borrower_cannot_overwrite_first(client):
    client.post("/books/", json=BOOK)
    first = client.post("/books/001234/borrow", json={"borrowed_by": "000123"}).json()
    assert client.post("/books/001234/borrow", json={"borrowed_by": "000456"}).status_code == 409
    assert client.get("/books/001234").json() == first


def test_delete_borrowed_book(client):
    client.post("/books/", json=BOOK)
    client.post("/books/001234/borrow", json={"borrowed_by": "000123"})
    assert client.delete("/books/001234").status_code == 204
    assert client.get("/books/001234").status_code == 404


def test_return_available_book_is_conflict(client):
    client.post("/books/", json=BOOK)
    assert client.post("/books/001234/return").status_code == 409


@pytest.mark.parametrize("method,path,body", [
    ("get", "/books/123456", None),
    ("delete", "/books/123456", None),
    ("post", "/books/123456/borrow", {"borrowed_by": "123456"}),
    ("post", "/books/123456/return", None),
])
def test_missing_book(client, method, path, body):
    assert client.request(method, path, json=body).status_code == 404


@pytest.mark.parametrize("value", [123456, "12345", "1234567", "-12345", "abcdef", "１２３４５６", "12345\n", None])
def test_invalid_serial_number(client, value):
    assert client.post("/books/", json={**BOOK, "serial_num": value}).status_code == 422


@pytest.mark.parametrize("field", ["title", "author"])
@pytest.mark.parametrize("value", ["", "   ", "x" * 256])
def test_invalid_text(client, field, value):
    assert client.post("/books/", json={**BOOK, field: value}).status_code == 422


@pytest.mark.parametrize("body", [{}, {"borrowed_by": None}, {"borrowed_by": 123456},
    {"borrowed_by": "-12345"}, {"borrowed_by": "123456", "is_borrowed": False}])
def test_invalid_borrow_request(client, body):
    client.post("/books/", json=BOOK)
    assert client.post("/books/001234/borrow", json=body).status_code == 422
    assert client.get("/books/001234").json()["is_borrowed"] is False


def test_state_cannot_be_set_during_creation(client):
    assert client.post("/books/", json={**BOOK, "is_borrowed": True}).status_code == 422


def test_pagination(client):
    for index in range(5):
        client.post("/books/", json={**BOOK, "serial_num": f"{index:06}"})
    page = client.get("/books/?limit=2&offset=2").json()
    assert page["total"] == 5
    assert page["limit"] == 2
    assert page["offset"] == 2
    assert [book["serial_num"] for book in page["items"]] == ["000002", "000003"]
    assert client.get("/books/?offset=5").json()["items"] == []


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_invalid_pagination(client, query):
    assert client.get(f"/books/?{query}").status_code == 422


def test_invalid_path_identifier(client):
    assert client.get("/books/-12345").status_code == 422
