"""Tests for math_helpers module."""

import pytest
from math_helpers import gcd, lcm, fibonacci, is_prime


class TestGCD:
    def test_basic(self):
        assert gcd(12, 8) == 4

    def test_coprime(self):
        assert gcd(7, 13) == 1

    def test_same(self):
        assert gcd(5, 5) == 5

    def test_with_zero(self):
        assert gcd(0, 5) == 5


class TestLCM:
    def test_basic(self):
        assert lcm(4, 6) == 12

    def test_coprime(self):
        assert lcm(3, 7) == 21

    def test_both_zero_raises(self):
        with pytest.raises(ValueError):
            lcm(0, 0)


class TestFibonacci:
    def test_first_one(self):
        assert fibonacci(1) == [0]

    def test_first_five(self):
        assert fibonacci(5) == [0, 1, 1, 2, 3]

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            fibonacci(0)


class TestIsPrime:
    """These tests will FAIL until is_prime is implemented."""

    def test_small_primes(self):
        assert is_prime(2) is True
        assert is_prime(3) is True
        assert is_prime(5) is True
        assert is_prime(7) is True

    def test_not_prime(self):
        assert is_prime(1) is False
        assert is_prime(4) is False
        assert is_prime(9) is False

    def test_zero_and_negative(self):
        assert is_prime(0) is False
        assert is_prime(-1) is False
