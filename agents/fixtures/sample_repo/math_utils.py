"""Math utility functions for the sample repository.

This module provides basic mathematical operations used for testing
the toy agent's ability to find and fix bugs.
"""


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b


def factorial(n: int) -> int:
    """Return the factorial of a non-negative integer.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n (n!).

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return 1

    result = 1
    # BUG: range should be (1, n + 1), but stops one short — off-by-one error
    for i in range(1, n):
        result *= i
    return result
