"""Math helper functions.

Provides utility functions for common mathematical operations.
"""

import math


def gcd(a: int, b: int) -> int:
    """Return the greatest common divisor of two integers.

    Uses the Euclidean algorithm.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The GCD of a and b.
    """
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """Return the least common multiple of two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The LCM of a and b.

    Raises:
        ValueError: If both a and b are zero.
    """
    if a == 0 and b == 0:
        raise ValueError("LCM is not defined when both inputs are zero")
    return abs(a * b) // gcd(a, b)


def fibonacci(n: int) -> list[int]:
    """Return the first n Fibonacci numbers.

    Args:
        n: How many Fibonacci numbers to generate (must be >= 1).

    Returns:
        A list of the first n Fibonacci numbers.

    Raises:
        ValueError: If n < 1.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    fibs = [0, 1]
    while len(fibs) < n:
        fibs.append(fibs[-1] + fibs[-2])
    return fibs[:n]
