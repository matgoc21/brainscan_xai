import torch
import torch.nn as nn
import torch.optim as optim
import copy 
import os

from xai_api.dataset_loader import get_dataloaders
from xai_api.model import BrainTumorResNet

def train():
    EPOCHS = 10
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f("Używane urządzenie: {device}. Początek treningu..."))

    train_loader, test_loader, class_names = get_dataloaders(batch_size=BATCH_SIZE)

    model = BrainTumorResNet(num_classes=len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr = LEARNING_RATE, weight_decay=1e-4)

    best_acc = 0.0
    best_model_wts = copy.deepcopy(model.state_dict())

    #Główna pętla epok

    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()

        outputs = model(inputs)
        loss = criterion(outputs, labels)

        _, preds = torch.max(outputs, 1)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        running_corrects += torch.sum(preds == labels.data)

    train_loss = running_loss / len(train_loader.dataset)
    train_acc = running_corrects.double() / len(train_loader.dataset)

    print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")

    model.eval()
    val_loss = 0.0
    val_corrects = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            _, preds = torch.max(outputs, 1)

            val_loss += loss.item() * inputs.size(0)
            val_corrects += torch.sum(preds == labels.data)
        val_loss = val_loss / len(test_loader.dataset)
        val_acc = val_corrects.double() / len(test_loader.dataset)
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            print(f"Nowy najlepszy model, nowe wagi modelu zapisane")

        print("\nTrening zakończony.")
        print(f"Najlepsza dokładność walidacji (Best Val Acc): {best_acc:.4f}")

        model.load_state_dict(best_model_wts)

        save_path = os.path.join("xai_api", "best_brain_tumor_model.pth")
        torch.save(model.state_dict(), save_path)
        print(f"Najlepszy model zapisany w: {save_path}")
if __name__ == "__main__":
    train()