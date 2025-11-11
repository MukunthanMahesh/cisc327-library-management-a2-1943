import pytest
from unittest.mock import Mock
from services.payment_service import PaymentGateway
from services.library_service import pay_late_fees, refund_late_fee_payment

# /////////////////////
# pay_late_fees() tests
# /////////////////////

# verify successful payment when all inputs are valid
def test_pay_late_fees_successful_payment(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Mock Book"})
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_001", "Approved")

    success, message, txn = pay_late_fees("123456", 1, mock_gateway)

    assert success is True
    assert txn == "txn_001"
    assert "payment successful" in message.lower()
    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=5.00,
        description="Late fees for 'Mock Book'"
    )


# verify payment declined by external gateway
def test_pay_late_fees_payment_declined(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Decline Test"})
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, None, "Card declined")

    success, message, txn = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn is None
    assert "payment failed" in message.lower()
    mock_gateway.process_payment.assert_called_once()


# verify invalid patron ID skips payment processing
def test_pay_late_fees_invalid_patron_id(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Mock Book"})
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("abc123", 1, mock_gateway)

    assert success is False
    assert txn is None
    assert "invalid patron id" in message.lower()
    mock_gateway.process_payment.assert_not_called()


# verify zero late fees skips gateway call
def test_pay_late_fees_zero_fee(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 0.0})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Mock Book"})
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn is None
    assert "no late fees" in message.lower()
    mock_gateway.process_payment.assert_not_called()


# verify network exception in gateway is handled gracefully
def test_pay_late_fees_gateway_exception(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5.00})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Mock Book"})
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network timeout")

    success, message, txn = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert txn is None
    assert "payment processing error" in message.lower()
    mock_gateway.process_payment.assert_called_once()

# ///////////////////////////////
# refund_late_fee_payment() tests
# ///////////////////////////////

# verify successful refund processing
def test_refund_late_fee_successful_refund():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund OK")

    success, message = refund_late_fee_payment("txn_123", 10.0, mock_gateway)

    assert success is True
    assert "refund ok" in message.lower()
    mock_gateway.refund_payment.assert_called_once_with("txn_123", 10.0)


# verify invalid transaction ID rejects refund
def test_refund_late_fee_invalid_transaction_id():
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("abc_123", 10.0, mock_gateway)

    assert success is False
    assert "invalid transaction id" in message.lower()
    mock_gateway.refund_payment.assert_not_called()


# verify zero refund amount is rejected
def test_refund_late_fee_zero_amount():
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", 0.0, mock_gateway)

    assert success is False
    assert "greater than 0" in message.lower()
    mock_gateway.refund_payment.assert_not_called()


# verify negative refund amount is rejected
def test_refund_late_fee_negative_amount():
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", -5.0, mock_gateway)

    assert success is False
    assert "greater than 0" in message.lower()
    mock_gateway.refund_payment.assert_not_called()


# verify refund exceeding $15 maximum is rejected
def test_refund_late_fee_exceeds_maximum():
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123", 20.0, mock_gateway)

    assert success is False
    assert "exceeds maximum" in message.lower()
    mock_gateway.refund_payment.assert_not_called()
