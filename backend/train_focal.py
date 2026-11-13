import argparse
import copy
import csv
import json
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Subset

from xai_api.dataset_loader import get_dataloaders
from xai_api.model import ResidualCustomCNN


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = (
    BACKEND_DIR / "xai_api" / "best_brain_tumor_model_focal_glioma.pth"
)


class WeightedFocalLoss(nn.Module):
    """Focal Loss z wagami klas – skupia trening na trudnych przypadkach (np. niskokontrastowy glejak)."""

    def __init__(self, weight=None, gamma=2.0):
        super().__init__()
        self.weight = weight
        self.gamma = gamma

    def forward(self, inputs, targets):
        weighted_ce = F.cross_entropy(
            inputs, targets, reduction="none", weight=self.weight
        )
        unweighted_ce = F.cross_entropy(inputs, targets, reduction="none")
        pt = torch.exp(-unweighted_ce)
        focal_loss = ((1.0 - pt) ** self.gamma) * weighted_ce
        return focal_loss.mean()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Trening ResidualCustomCNN z Focal Loss i priorytetem dla klasy glioma."
    )
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument(
        "--glioma-loss-weight",
        type=float,
        default=2.5,
        help="Mnożnik kary dla klasy glioma.",
    )
    parser.add_argument(
        "--focal-gamma",
        type=float,
        default=2.0,
        help="Parametr gamma dla Focal Loss (0 = standardowy CrossEntropy).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help="Ścieżka do zapisu wag modelu.",
    )
    parser.add_argument(
        "--validation-output",
        type=Path,
        default=BACKEND_DIR / "validation_results_focal",
        help="Prefix wyjściowy dla raportów walidacji.",
    )
    return parser.parse_args()


def metrics_from_confusion(confusion, class_names):
    class_metrics = {}
    for class_index, class_name in enumerate(class_names):
        true_positive = confusion[class_index][class_index]
        actual_count = sum(confusion[class_index])
        predicted_count = sum(row[class_index] for row in confusion)
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / actual_count if actual_count else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        class_metrics[class_name] = {
            "precision_percent": precision * 100,
            "recall_percent": recall * 100,
            "f1_percent": f1 * 100,
            "support": actual_count,
        }
    macro_f1 = sum(item["f1_percent"] for item in class_metrics.values()) / len(
        class_metrics
    )
    return class_metrics, macro_f1


def evaluate(model, loader, criterion, device, class_names, write_predictions=False):
    model.eval()
    confusion = [[0 for _ in class_names] for _ in class_names]
    loss_total = 0.0
    correct_total = 0
    predictions = []
    sample_offset = 0

    with torch.inference_mode():
        for inputs, labels in loader:
            outputs = model(inputs.to(device))
            labels_device = labels.to(device)
            loss_total += criterion(outputs, labels_device).item() * len(labels)
            predicted = outputs.argmax(dim=1)
            correct_total += (predicted == labels_device).sum().item()

            for actual, guess, confidence in zip(
                labels.tolist(),
                predicted.cpu().tolist(),
                torch.softmax(outputs, dim=1).max(dim=1).values.cpu().tolist(),
            ):
                confusion[actual][guess] += 1
                if write_predictions:
                    base_dataset = loader.dataset
                    sample_index = sample_offset
                    while isinstance(base_dataset, Subset):
                        sample_index = base_dataset.indices[sample_index]
                        base_dataset = base_dataset.dataset
                    image_path, _ = base_dataset.samples[sample_index]
                    predictions.append(
                        {
                            "image": str(
                                Path(image_path).relative_to(base_dataset.root)
                            ),
                            "actual_class": class_names[actual],
                            "predicted_class": class_names[guess],
                            "confidence_percent": round(confidence * 100, 2),
                            "correct": actual == guess,
                        }
                    )
                sample_offset += 1

    class_metrics, macro_f1 = metrics_from_confusion(confusion, class_names)
    result = {
        "loss": loss_total / len(loader.dataset),
        "accuracy_percent": correct_total / len(loader.dataset) * 100,
        "macro_f1_percent": macro_f1,
        "classes": class_metrics,
        "confusion_matrix": {
            "labels": class_names,
            "rows_actual_columns_predicted": confusion,
        },
    }
    return result, predictions


def train():
    args = parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.learning_rate <= 0:
        raise SystemExit("Epoki, batch size i learning rate muszą być dodatnie.")
    if args.glioma_loss_weight <= 0:
        raise SystemExit("Mnożnik dla gliomy musi być dodatni.")

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Urządzenie: {device} | Glioma weight: {args.glioma_loss_weight} | Gamma: {args.focal_gamma}")

    train_loader, validation_loader, class_names = get_dataloaders(
        batch_size=args.batch_size,
        seed=args.seed,
    )
    expected_classes = ["glioma", "meningioma", "notumor", "pituitary"]
    if class_names != expected_classes:
        raise ValueError(
            f"Oczekiwana kolejność klas: {expected_classes}, znaleziono {class_names}."
        )

    model = ResidualCustomCNN(num_classes=len(class_names)).to(device)

    class_weights = torch.ones(len(class_names), device=device)
    class_weights[class_names.index("glioma")] = args.glioma_loss_weight

    train_criterion = WeightedFocalLoss(weight=class_weights, gamma=args.focal_gamma)
    validation_criterion = nn.CrossEntropyLoss()

    optimizer = optim.AdamW(
        model.parameters(), lr=args.learning_rate, weight_decay=1e-2
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    best_composite_score = -1.0
    best_metrics = (0.0, 0.0)
    best_model_weights = copy.deepcopy(model.state_dict())

    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        model.train()
        train_loss_total = 0.0
        train_correct_total = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = train_criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss_total += loss.item() * inputs.size(0)
            train_correct_total += (outputs.argmax(dim=1) == labels).sum().item()

        train_loss = train_loss_total / len(train_loader.dataset)
        train_accuracy = train_correct_total / len(train_loader.dataset) * 100
        validation, _ = evaluate(
            model, validation_loader, validation_criterion, device, class_names
        )
        glioma_recall = validation["classes"]["glioma"]["recall_percent"]
        macro_f1 = validation["macro_f1_percent"]

        print(
            f"Train loss: {train_loss:.4f} | Train accuracy: {train_accuracy:.2f}%"
        )
        print(
            f"Validation loss: {validation['loss']:.4f} | "
            f"accuracy: {validation['accuracy_percent']:.2f}% | "
            f"macro F1: {macro_f1:.2f}% | "
            f"glioma recall: {glioma_recall:.2f}%"
        )

        # Kompozytowy wynik premiujący wysokie glioma_recall przy zachowaniu wysokiego macro F1
        composite_score = 0.4 * macro_f1 + 0.6 * glioma_recall
        scheduler.step(validation["loss"])

        if composite_score > best_composite_score:
            best_composite_score = composite_score
            best_metrics = (macro_f1, glioma_recall)
            best_model_weights = copy.deepcopy(model.state_dict())
            print(f"Nowy najlepszy checkpoint (score: {composite_score:.2f}).")

    model.load_state_dict(best_model_weights)
    args.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.checkpoint_path)
    final_validation, predictions = evaluate(
        model,
        validation_loader,
        validation_criterion,
        device,
        class_names,
        write_predictions=True,
    )

    args.validation_output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.validation_output.with_suffix(".csv")
    json_path = args.validation_output.with_suffix(".json")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            {
                "checkpoint": str(args.checkpoint_path),
                "seed": args.seed,
                "glioma_loss_weight": args.glioma_loss_weight,
                "focal_gamma": args.focal_gamma,
                "learning_rate": args.learning_rate,
                **final_validation,
            },
            json_file,
            indent=2,
        )
        json_file.write("\n")

    print(f"\nBest validation macro F1: {best_metrics[0]:.2f}%")
    print(f"Best validation glioma recall: {best_metrics[1]:.2f}%")
    print(f"Checkpoint saved to: {args.checkpoint_path}")


if __name__ == "__main__":
    train()