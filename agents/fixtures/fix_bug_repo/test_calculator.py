"""Tests for the Calculator class."""

import pytest
from calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


class TestAdd:
    def test_positive(self, calc):
        assert calc.add(2, 3) == 5

    def test_negative(self, calc):
        assert calc.add(-1, -1) == -2


class TestSubtract:
    def test_basic(self, calc):
        assert calc.subtract(10, 4) == 6

    def test_negative_result(self, calc):
        assert calc.subtract(3, 7) == -4


class TestMultiply:
    def test_basic(self, calc):
        assert calc.multiply(3, 4) == 12

    def test_by_zero(self, calc):
        assert calc.multiply(5, 0) == 0


class TestDivide:
    def test_basic(self, calc):
        assert calc.divide(10, 2) == 5.0

    def test_float_result(self, calc):
        assert calc.divide(7, 2) == 3.5

    def test_divide_by_zero_raises_value_error(self, calc):
        """This test FAILS — divide() raises ZeroDivisionError, not ValueError."""
        with pytest.raises(ValueError, match="zero"):
            calc.divide(1, 0)
