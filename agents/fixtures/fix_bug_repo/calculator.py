"""Simple calculator module with a known bug.

The Calculator class provides basic arithmetic operations.
One method has a deliberate bug for testing purposes.
"""


class Calculator:
    """A basic calculator with standard arithmetic operations."""

    def add(self, a: float, b: float) -> float:
        """Return the sum of two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Return the difference of two numbers."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Return the product of two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Return the quotient of two numbers.

        Args:
            a: The numerator.
            b: The denominator.

        Returns:
            The result of a / b.

        Raises:
            ValueError: If b is zero.
        """
        # BUG: No check for division by zero — raises unhandled ZeroDivisionError
        # instead of the documented ValueError
        return a / b
