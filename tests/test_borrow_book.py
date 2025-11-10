import pytest
import random
from database import init_database, get_db_connection
from services.library_service import borrow_book_by_patron

# verify borrowing fails if book has zero available copies
def test_borrow_book_no_availability(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    conn.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)", 
                 ("No Copies", "Author X", isbn, 1, 0))
    conn.commit()
    conn.close()

    success, message = borrow_book_by_patron("123456", 1)
    assert success is False
    assert "not available" in message.lower()

# verify borrowing succeeds with valid patron and available book
def test_borrow_book_valid_input(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    conn.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)", 
                 ("Valid Book", "Author Y", isbn, 2, 2))
    conn.commit()
    conn.close()

    success, message = borrow_book_by_patron("123456", 1)
    assert isinstance(success, bool)
    assert isinstance(message, str)
    assert success is True

# verify borrowing fails with invalid patron ID
def test_borrow_book_invalid_patron_id(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    success, message = borrow_book_by_patron("12", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

# verify borrowing fails if book does not exist
def test_borrow_book_not_found(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    success, message = borrow_book_by_patron("123456", 99999)
    assert success is False
    assert "not found" in message.lower()

