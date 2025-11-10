"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books
)
from services.payment_service import PaymentGateway

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4: Return Management
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the borrowed book
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if the patron actually borrowed the book
    borrowed_books = get_patron_borrowed_books(patron_id)
    borrowed_book_ids = [b['book_id'] for b in borrowed_books]
    if book_id not in borrowed_book_ids:
        return False, "This book was not borrowed by the patron."
    
    # Find borrow record
    borrow_record = next((b for b in borrowed_books if b['book_id'] == book_id), None)
    if not borrow_record:
        return False, "Borrow record not found."
    
    # Update return date
    return_date = datetime.now()
    updated = update_borrow_record_return_date(patron_id, book_id, return_date)
    if not updated:
        return False, "Failed to update return record."
    
    # Increment available copies
    updated_copies = update_book_availability(book_id, +1)
    if not updated_copies:
        return False, "Failed to update book availability."
    
    # Check for lateness
    due_date = borrow_record['due_date']
    if return_date > due_date:
        overdue_days = (return_date - due_date).days
        return True, f'Book returned late by {overdue_days} days. Please check for late fees.'
    
    return True, f'Book returned successfully on {return_date.strftime("%Y-%m-%d")}.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    TODO: Implement R5 as per requirements 
    
    
    return { // return the calculated values
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Late fee calculation not implemented'
    }
    """
    # Retrieve all books borrowed by this patron
    borrowed_books = get_patron_borrowed_books(patron_id)
    record = next((b for b in borrowed_books if b['book_id'] == book_id), None)

    # If no borrow record found
    if not record:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Borrow record not found.'
        }

    due_date = record['due_date']
    # If returned, use recorded return date; else, assume not yet returned (use current time)
    return_date = record.get('return_date') or datetime.now()

    # No late fee if returned before or on due date
    if return_date <= due_date:
        return {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'No late fee.'
        }

    # Calculate overdue
    days_overdue = (return_date - due_date).days
    fee = round(days_overdue * 0.50, 2)

    return {
        'fee_amount': fee,
        'days_overdue': days_overdue,
        'status': 'Late fee applied.'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    Implements R6: Catalog Search

    Args:
        search_term (str): The keyword to search for.
        search_type (str): One of ['title', 'author', 'isbn'].
    
    Returns:
        List[Dict]: A list of matching books.
    """
    # Retrieve all books from the database
    books = get_all_books()

    # Validate inputs
    if not search_term or not search_term.strip():
        return books 
    if search_type not in ['title', 'author', 'isbn']:
        return []     

    search_term = search_term.strip().lower()
    results = []

    for book in books:
        # Defensive: skip malformed records
        if not isinstance(book, dict):
            continue

        if search_type == 'title' and search_term in book.get('title', '').lower():
            results.append(book)
        elif search_type == 'author' and search_term in book.get('author', '').lower():
            results.append(book)
        elif search_type == 'isbn' and search_term in book.get('isbn', '').lower():
            results.append(book)

    return results

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Generate a status report for a patron.
    Implements R7: Patron Status Report

    Args:
        patron_id (str): 6-digit library card ID.
    
    Returns:
        Dict containing:
            - patron_id
            - borrowed_books (list of dicts)
            - total_books_borrowed (int)
            - overdue_count (int)
            - total_late_fees (float)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            "patron_id": patron_id,
            "borrowed_books": [],
            "total_books_borrowed": 0,
            "overdue_count": 0,
            "total_late_fees": 0.0,
            "status": "Invalid patron ID."
        }

    borrowed_books = get_patron_borrowed_books(patron_id)
    if not borrowed_books:
        return {
            "patron_id": patron_id,
            "borrowed_books": [],
            "total_books_borrowed": 0,
            "overdue_count": 0,
            "total_late_fees": 0.0,
            "status": "No borrowed books."
        }

    total_late_fees = 0.0
    overdue_count = 0
    detailed_books = []

    for record in borrowed_books:
        fee_info = calculate_late_fee_for_book(patron_id, record['book_id'])
        fee = fee_info['fee_amount']
        total_late_fees += fee
        if fee_info['days_overdue'] > 0:
            overdue_count += 1

        detailed_books.append({
            "book_title": record.get("title", "Unknown"),
            "due_date": record["due_date"].strftime("%Y-%m-%d"),
            "return_date": record["return_date"].strftime("%Y-%m-%d") if record.get("return_date") else None,
            "fee_amount": fee
        })

    return {
        "patron_id": patron_id,
        "borrowed_books": detailed_books,
        "total_books_borrowed": len(borrowed_books),
        "overdue_count": overdue_count,
        "total_late_fees": round(total_late_fees, 2),
        "status": "Report generated successfully."
    }

def pay_late_fees(patron_id: str, book_id: int, payment_gateway: PaymentGateway = None) -> Tuple[bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.
    
    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])
        
    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None
    
    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    
    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None
    
    fee_amount = fee_info.get('fee_amount', 0.0)
    
    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None
    
    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )
        
        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None
            
    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None

def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: PaymentGateway = None) -> Tuple[bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).
    
    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking
    
    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."
    
    if amount <= 0:
        return False, "Refund amount must be greater than 0."
    
    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id, amount)
        
        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"
            
    except Exception as e:
        return False, f"Refund processing error: {str(e)}"