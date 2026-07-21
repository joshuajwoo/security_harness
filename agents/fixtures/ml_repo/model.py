"""Simple neural network model definition.

A small feedforward network for binary classification on synthetic data.
"""

import torch
import torch.nn as nn


class SimpleNet(nn.Module):
    """A 2-layer feedforward neural network.

    Architecture:
        Input -> Linear(input_dim, hidden_dim) -> ReLU -> Dropout ->
        Linear(hidden_dim, 1) -> Sigmoid

    Args:
        input_dim: Number of input features.
        hidden_dim: Number of hidden units.
        dropout: Dropout probability.
    """

    def __init__(self, input_dim: int = 10, hidden_dim: int = 32, dropout: float = 0.2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (batch_size, input_dim).

        Returns:
            Output tensor of shape (batch_size, 1) with values in [0, 1].
        """
        return self.network(x)
