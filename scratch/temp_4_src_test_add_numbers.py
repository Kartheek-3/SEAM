import pytest
from src.add_numbers import add_numbers

def test_add_numbers():
    assert add_numbers(5, 7) == 12
    assert add_numbers(-1, 1) == 0
    assert add_numbers(-1, -1) == -2