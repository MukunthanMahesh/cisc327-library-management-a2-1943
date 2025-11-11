import pytest
import re
import time
from services.payment_service import PaymentGateway


# verify successful payment below threshold and valid patron ID
def test_process_payment_success():
    gateway = PaymentGateway()
    success, txn, message = gateway.process_payment("123456", 100.0, "Late fee payment")
    assert success is True
    assert txn.startswith("txn_123456_")
    assert "processed successfully" in message


# verify invalid amount (<= 0) returns error
def test_process_payment_invalid_amount_zero():
    gateway = PaymentGateway()
    success, txn, message = gateway.process_payment("123456", 0, "Late fee payment")
    assert success is False
    assert txn == ""
    assert "must be greater than 0" in message


# verify high amount (> 1000) gets declined
def test_process_payment_exceeds_limit():
    gateway = PaymentGateway()
    success, txn, message = gateway.process_payment("123456", 1500.0, "Large payment")
    assert success is False
    assert txn == ""
    assert "exceeds limit" in message


# verify invalid patron ID format
def test_process_payment_invalid_patron_id():
    gateway = PaymentGateway()
    success, txn, message = gateway.process_payment("12", 10.0, "Invalid ID")
    assert success is False
    assert txn == ""
    assert "Invalid patron ID" in message


# verify refund success
def test_refund_payment_success():
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_123456_1000", 10.0)
    assert success is True
    assert "Refund of $10.00 processed successfully" in message


# verify refund with invalid transaction ID
def test_refund_payment_invalid_txn_id():
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("abc_123", 10.0)
    assert success is False
    assert "Invalid transaction ID" in message


# verify refund with invalid amount (<= 0)
def test_refund_payment_invalid_amount():
    gateway = PaymentGateway()
    success, message = gateway.refund_payment("txn_123456_1000", 0)
    assert success is False
    assert "Invalid refund amount" in message


# verify verify_payment_status with invalid txn id
def test_verify_payment_status_not_found():
    gateway = PaymentGateway()
    result = gateway.verify_payment_status("abc_123")
    assert result["status"] == "not_found"
    assert "Transaction not found" in result["message"]


# verify verify_payment_status success path
def test_verify_payment_status_success():
    gateway = PaymentGateway()
    txn_id = "txn_123456_12345"
    result = gateway.verify_payment_status(txn_id)
    assert result["status"] == "completed"
    assert result["transaction_id"] == txn_id
    assert "amount" in result
    assert isinstance(result["timestamp"], float)
