import pytest
import random
from datetime import datetime, timedelta
from database import init_database, get_db_connection, insert_book, insert_borrow_record
from library_service import get_patron_status_report

# verify report returns message for invalid patron ID
def test_patron_status_invalid_id(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    result = get_patron_status_report("12")
    assert result["status"].lower() == "invalid patron id."
    assert result["total_books_borrowed"] == 0
    assert result["total_late_fees"] == 0.0

# verify report shows no loans and no fees if patron has borrowed nothing
def test_patron_status_no_loans(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    result = get_patron_status_report("123456")
    assert result["patron_id"] == "123456"
    assert result["total_books_borrowed"] == 0
    assert result["total_late_fees"] == 0.0
    assert result["borrowed_books"] == []
    assert "no borrowed books" in result["status"].lower()

# verify report includes a currently borrowed book
def test_patron_status_with_current_loan(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Test Book", "Author A", isbn, 1, 0)
    borrow_date = datetime.now() - timedelta(days=2)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    conn.close()

    result = get_patron_status_report("123456")
    assert result["total_books_borrowed"] == 1
    assert result["total_late_fees"] == 0.0
    assert len(result["borrowed_books"]) == 1
    assert result["borrowed_books"][0]["book_title"] == "Test Book"

# verify report calculates late fees for patron correctly
def test_patron_status_with_late_fee(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Late Book", "Author B", isbn, 1, 0)
    borrow_date = datetime.now() - timedelta(days=20)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    conn.close()

    result = get_patron_status_report("123456")
    assert result["total_books_borrowed"] == 1
    assert result["total_late_fees"] > 0.0
    assert len(result["borrowed_books"]) == 1
    assert result["borrowed_books"][0]["book_title"] == "Late Book"

# verify multiple borrow records appear in report
def test_patron_status_multiple_books(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn1 = str(random.randint(1000000000000, 9999999999999))
    isbn2 = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("History Book 1", "Author C", isbn1, 1, 0)
    insert_book("History Book 2", "Author D", isbn2, 1, 0)
    borrow_date = datetime.now() - timedelta(days=10)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    insert_borrow_record("123456", 2, borrow_date, due_date)
    conn.close()

    result = get_patron_status_report("123456")
    assert isinstance(result["borrowed_books"], list)
    assert len(result["borrowed_books"]) >= 2
    titles = [b["book_title"] for b in result["borrowed_books"]]
    assert "History Book 1" in titles
    assert "History Book 2" in titles
