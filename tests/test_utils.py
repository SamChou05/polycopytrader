import pytest
from utils import is_valid_address

def test_valid_address():
    # Vitalik's address
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert is_valid_address(addr) is True

def test_invalid_address():
    assert is_valid_address("not-an-address") is False
    assert is_valid_address("0x123") is False
