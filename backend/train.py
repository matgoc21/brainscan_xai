import copy
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

from xai_api.dataset_loader import get_dataloaders
from xai_api.model import ResidualCustomCNN


def train():
    epochs = 50
    batch_size = 32
    learning_rate = 0.001
    seed = 42

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using device: {device}. Starting training...")

    train_loader, validation_loader, class_names = get_dataloaders(
        batch_size=batch_size,
        seed=seed,
    )
    model = ResidualCustomCNN(num_classes=len(class_names)).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )
    best_validation_accuracy = -1.0
    best_model_weights = copy.deepcopy(model.state_dict())

    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")

        model.train()
        train_loss_total = 0.0
        train_correct_total = 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss_total += loss.item() * inputs.size(0)
            train_correct_total += (outputs.argmax(dim=1) == labels).sum().item()

        train_loss = train_loss_total / len(train_loader.dataset)
        train_accuracy = train_correct_total / len(train_loader.dataset)
        print(f"Train Loss: {train_loss:.4f} | Train Accuracy: {train_accuracy:.4f}")

        model.eval()
        validation_loss_total = 0.0
        validation_correct_total = 0
        with torch.inference_mode():
            for inputs, labels in validation_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                validation_loss_total += loss.item() * inputs.size(0)
                validation_correct_total += (
                    outputs.argmax(dim=1) == labels
                ).sum().item()

        validation_loss = validation_loss_total / len(validation_loader.dataset)
        validation_accuracy = (
            validation_correct_total / len(validation_loader.dataset)
        )
        print(
            f"Validation Loss: {validation_loss:.4f} | "
            f"Validation Accuracy: {validation_accuracy:.4f}"
        )

        # The scheduler and checkpoint selection use validation data, never Testing.
        scheduler.step(validation_loss)
        if validation_accuracy > best_validation_accuracy:
            best_validation_accuracy = validation_accuracy
            best_model_weights = copy.deepcopy(model.state_dict())
            print("New best validation checkpoint selected.")

    # Restore and save only the best validation checkpoint after all epochs finish.
    model.load_state_dict(best_model_weights)
    checkpoint_path = (
        Path(__file__).resolve().parent
        / "xai_api"
        / "best_brain_tumor_model_customCNN.pth"
    )
    torch.save(model.state_dict(), checkpoint_path)
    print(f"Best validation accuracy: {best_validation_accuracy:.4f}")
    print(f"Best model saved to: {checkpoint_path}")


if __name__ == "__main__":
    train()
