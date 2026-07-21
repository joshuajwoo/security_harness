"""Tests for math_utils module."""

import pytest
from math_utils import add, multiply, factorial


class TestAdd:
    def test_positive_numbers(self):
        assert add(2, 3) == 5

    def test_negative_numbers(self):
        assert add(-1, -1) == -2

    def test_zero(self):
        assert add(0, 0) == 0


class TestMultiply:
    def test_positive_numbers(self):
        assert multiply(3, 4) == 12

    def test_by_zero(self):
        assert multiply(5, 0) == 0

    def test_negative(self):
        assert multiply(-2, 3) == -6


class TestFactorial:
    def test_zero(self):
        assert factorial(0) == 1

    def test_one(self):
        assert factorial(1) == 1

    def test_small_number(self):
        assert factorial(5) == 120  # This will FAIL due to the off-by-one bug

    def test_larger_number(self):
        assert factorial(7) == 5040  # This will also FAIL

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            factorial(-1)
