import pytest
import random
from datetime import datetime, timedelta
from database import init_database, get_db_connection, insert_book, insert_borrow_record
from services.library_service import return_book_by_patron

# assuming return_book_by_patron(patron_id, book_id) has been implemented 

# verify returning fails with invalid patron ID
def test_return_book_invalid_patron_id(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    success, message = return_book_by_patron("12", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

# verify returning fails if book does not exist
def test_return_book_not_found(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    success, message = return_book_by_patron("123456", 99999)
    assert success is False
    assert "this book was not borrowed by the patron." in message.lower()

# verify returning fails if patron never borrowed the book
def test_return_book_not_borrowed(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Test Book", "Author X", isbn, 2, 2)
    conn.close()

    success, message = return_book_by_patron("123456", 1)
    assert success is False
    assert "this book was not borrowed by the patron." in message.lower()

# verify returning succeeds for borrowed book
def test_return_book_valid(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Valid Book", "Author Y", isbn, 1, 0)
    insert_borrow_record("123456", 1, datetime.now() - timedelta(days=2), datetime.now() + timedelta(days=12))
    conn.close()

    success, message = return_book_by_patron("123456", 1)
    assert success is True
    # Just verify that message starts correctly
    assert "book returned successfully on" in message.lower()
