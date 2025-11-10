import pytest
import random
from services.library_service import add_book_to_catalog

# verify adding a book with overly long title fails
def test_add_book_long_title():
    long_title = "A" * 201
    random_int = random.randint(1000, 9999)
    random_isbn = str(random.randint(1000000000000, 9999999999999))
    success, message = add_book_to_catalog(long_title, f"Author {random_int}", random_isbn, 3)
    assert success is False
    assert "less than 200" in message.lower()

# verify adding a book with valid input succeeds
def test_add_book_valid_input():
    random_int = random.randint(1000, 9999)
    random_isbn = str(random.randint(1000000000000, 9999999999999))
    success, message = add_book_to_catalog(f"Test Book {random_int}", f"Author {random_int}", random_isbn, 3)
    assert success is True
    assert "successfully" in message.lower()

# verify adding a book with missing title fails
def test_add_book_missing_title():
    random_int = random.randint(1000, 9999)
    random_isbn = str(random.randint(1000000000000, 9999999999999))
    success, message = add_book_to_catalog("", f"Author {random_int}", random_isbn, 3)
    assert success is False
    assert "title is required" in message.lower()

# verify adding a book with invalid ISBN fails
def test_add_book_invalid_isbn():
    random_int = random.randint(1000, 9999)
    invalid_isbn = str(random.randint(10000000000000, 99999999999999)) # Passing a 14-digit ISBN instead of 13; expect to fail
    success, message = add_book_to_catalog(f"Test Book {random_int}", f"Author {random_int}", invalid_isbn, 3)
    assert success is False
    assert "13 digits" in message

# verify adding a book with negative copies fails
def test_add_book_invalid_copies():
    random_int = random.randint(1000, 9999)
    random_isbn = str(random.randint(1000000000000, 9999999999999))
    success, message = add_book_to_catalog(f"Test Book {random_int}", f"Author {random_int}", random_isbn, -1)
    assert success is False
    assert "positive integer" in message.lower()
