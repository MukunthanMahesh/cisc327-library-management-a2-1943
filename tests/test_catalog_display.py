import random
import pytest
from database import get_all_books, init_database, add_sample_data

# verify displaying catalog on empty database returns empty list
def test_display_catalog_empty_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()
    books = get_all_books()
    assert books == []

# verify displaying catalog returns non-empty list after adding sample data
def test_display_catalog_not_empty():
    init_database()
    add_sample_data()
    books = get_all_books()
    assert isinstance(books, list)
    assert len(books) > 0

# verify each book in catalog has required fields
def test_display_catalog_book_fields():
    init_database()
    add_sample_data()
    books = get_all_books()
    book = books[0]
    assert "id" in book
    assert "title" in book
    assert "author" in book
    assert "isbn" in book
    assert "available_copies" in book
    assert "total_copies" in book

# verify catalog results are ordered alphabetically by title
def test_display_catalog_ordered_by_title(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()
    isbn1 = str(random.randint(1000000000000, 9999999999999))
    isbn2 = str(random.randint(1000000000000, 9999999999999))

    from database import get_db_connection
    conn = get_db_connection()
    conn.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)", 
                 ("ZZZZZZZ", "Author A", isbn1, 2, 2))
    conn.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)", 
                 ("AAAAAAA", "Author B", isbn2, 1, 1))
    conn.commit()
    conn.close()

    books = get_all_books()
    titles = [b["title"] for b in books]
    assert titles == sorted(titles)

# verify displaying catalog can handle invalid data without breaking
def test_display_catalog_invalid_copies(tmp_path, monkeypatch):
    test_db = tmp_path / "test_library.db"
    monkeypatch.setattr("database.DATABASE", str(test_db))
    init_database()

    from database import get_db_connection
    conn = get_db_connection()
    isbn = str(random.randint(1000000000000, 9999999999999))
    conn.execute("INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
                 ("Broken Book", "Author X", isbn, 2, 5))  # invalid: available > total
    conn.commit()
    conn.close()

    books = get_all_books()
    book = [b for b in books if b["title"] == "Broken Book"][0]
    assert book["available_copies"] > book["total_copies"]
