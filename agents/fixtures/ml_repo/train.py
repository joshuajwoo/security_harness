"""Training script for SimpleNet.

Generates synthetic binary classification data, trains a SimpleNet model,
and reports training metrics. This script demonstrates a standard PyTorch
training loop with:
- Synthetic data generation
- Train/validation split
- Batch training with DataLoader
- Loss tracking and basic evaluation
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from model import SimpleNet


def generate_synthetic_data(
    n_samples: int = 1000,
    n_features: int = 10,
    seed: int = 42,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Generate synthetic binary classification data.

    Creates linearly separable data with some noise added.

    Args:
        n_samples: Number of samples to generate.
        n_features: Number of input features.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (features, labels) tensors.
    """
    torch.manual_seed(seed)
    X = torch.randn(n_samples, n_features)
    # Labels based on a linear combination with noise
    weights = torch.randn(n_features)
    logits = X @ weights + torch.randn(n_samples) * 0.5
    y = (logits > 0).float().unsqueeze(1)
    return X, y


def train(
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 0.01,
    hidden_dim: int = 32,
    val_split: float = 0.2,
    seed: int = 42,
) -> dict:
    """Train a SimpleNet model on synthetic data.

    Args:
        epochs: Number of training epochs.
        batch_size: Batch size for training.
        learning_rate: Learning rate for the optimizer.
        hidden_dim: Number of hidden units in the model.
        val_split: Fraction of data to use for validation.
        seed: Random seed for reproducibility.

    Returns:
        A dict containing training history with keys:
        - 'train_losses': list of average training loss per epoch
        - 'val_losses': list of average validation loss per epoch
        - 'val_accuracies': list of validation accuracy per epoch
        - 'final_accuracy': final validation accuracy
    """
    torch.manual_seed(seed)

    # Generate data
    X, y = generate_synthetic_data(seed=seed)
    dataset = TensorDataset(X, y)

    # Split into train and validation
    val_size = int(len(dataset) * val_split)
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(seed),
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    # Initialize model, loss, optimizer
    model = SimpleNet(input_dim=X.shape[1], hidden_dim=hidden_dim)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    history = {
        "train_losses": [],
        "val_losses": [],
        "val_accuracies": [],
    }

    for epoch in range(epochs):
        # --- Training ---
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)
        history["train_losses"].append(avg_train_loss)

        # --- Validation ---
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
                predicted = (outputs > 0.5).float()
                correct += (predicted == batch_y).sum().item()
                total += batch_y.size(0)

        avg_val_loss = val_loss / len(val_loader)
        val_accuracy = correct / total
        history["val_losses"].append(avg_val_loss)
        history["val_accuracies"].append(val_accuracy)

        print(
            f"Epoch {epoch + 1}/{epochs} — "
            f"Train Loss: {avg_train_loss:.4f}, "
            f"Val Loss: {avg_val_loss:.4f}, "
            f"Val Accuracy: {val_accuracy:.4f}"
        )

    history["final_accuracy"] = history["val_accuracies"][-1]
    return history


if __name__ == "__main__":
    results = train()
    print(f"\nFinal validation accuracy: {results['final_accuracy']:.4f}")
