import pytest
import random
from database import init_database, get_db_connection, insert_book
from services.library_service import search_books_in_catalog

# assume search_books_in_catalog(search_term, search_type) has been implemented

# verify searching by valid title
def test_search_books_by_title(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Silent Patient", "Alex Michaelides", isbn, 3, 3)
    conn.close()

    results = search_books_in_catalog("Silent", "title")
    assert len(results) == 1
    assert results[0]["title"] == "Silent Patient"

# verify searching by valid author
def test_search_books_by_author(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("To Kill a Mockingbird", "Harper Lee", isbn, 2, 2)
    conn.close()

    results = search_books_in_catalog("harper", "author")
    assert len(results) == 1
    assert results[0]["author"] == "Harper Lee"

# verify searching by ISBN (exact match)
def test_search_books_by_isbn(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = "1234567890123"
    conn = get_db_connection()
    insert_book("1984", "George Orwell", isbn, 1, 1)
    conn.close()

    results = search_books_in_catalog("1234567890123", "isbn")
    assert len(results) == 1
    assert results[0]["isbn"] == "1234567890123"

# verify searching returns empty list if no matches found
def test_search_books_no_results(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    results = search_books_in_catalog("nonexistent", "title")
    assert results == []

# verify searching with invalid search_type returns empty list
def test_search_books_invalid_type(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    results = search_books_in_catalog("test", "invalid_type")
    assert results == []
