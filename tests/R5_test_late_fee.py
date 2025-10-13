import pytest
import random
from datetime import datetime, timedelta
from database import init_database, get_db_connection, insert_book, insert_borrow_record
from library_service import calculate_late_fee_for_book

# verify no late fee if book is returned before due date
def test_late_fee_no_overdue(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("On Time", "Author A", isbn, 1, 0)
    borrow_date = datetime.now() - timedelta(days=5)
    due_date = borrow_date + timedelta(days=14)  # still not due
    insert_borrow_record("123456", 1, borrow_date, due_date)
    conn.close()

    result = calculate_late_fee_for_book("123456", 1)
    assert result["fee_amount"] == 0.0
    assert result["days_overdue"] == 0
    assert "no late fee" in result["status"].lower()

# verify late fee within a week overdue
def test_late_fee_within_seven_days(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Slightly Late", "Author B", isbn, 1, 0)
    borrow_date = datetime.now() - timedelta(days=20)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    conn.close()

    result = calculate_late_fee_for_book("123456", 1)
    assert result["days_overdue"] == 6
    assert abs(result["fee_amount"] - 3.0) < 0.01
    assert "late fee applied" in result["status"].lower()

# verify late fee beyond a week overdue
def test_late_fee_beyond_seven_days(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    isbn = str(random.randint(1000000000000, 9999999999999))
    conn = get_db_connection()
    insert_book("Long Overdue", "Author C", isbn, 1, 0)
    borrow_date = datetime.now() - timedelta(days=25)
    due_date = borrow_date + timedelta(days=14)
    insert_borrow_record("123456", 1, borrow_date, due_date)
    conn.close()

    result = calculate_late_fee_for_book("123456", 1)
    assert result["days_overdue"] == 11
    assert abs(result["fee_amount"] - 5.5) < 0.01
    assert "late fee applied" in result["status"].lower()

# verify no fee for patron who didn't borrow a book
def test_late_fee_book_not_borrowed(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    result = calculate_late_fee_for_book("123456", 1)
    assert result["fee_amount"] == 0.0
    assert result["days_overdue"] == 0
    assert "borrow record not found" in result["status"].lower()
