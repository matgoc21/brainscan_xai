import argparse
import csv
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from xai_api.model import ResidualCustomCNN


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
CLASS_NAMES = ["glioma", "meningioma", "notumor", "pituitary"]
TESTING_DIRS = [
    BACKEND_DIR / "dataset" / "archive" / "Testing",
    PROJECT_DIR / "dataset" / "archive" / "Testing",
]
DEFAULT_TESTING_DIR = next(
    (path for path in TESTING_DIRS if path.is_dir()), TESTING_DIRS[-1]
)
PREPROCESS = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate the trained brain-tumor CNN on a labeled image folder."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_TESTING_DIR,
        help="Testing folder with one subfolder per class.",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        default=BACKEND_DIR / "xai_api" / "best_brain_tumor_model_customCNN.pth",
        help="Path to the ResidualCustomCNN state-dict checkpoint used by the API.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of images processed per batch.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=BACKEND_DIR / "test_results",
        help="Output path prefix for the per-image CSV and summary JSON.",
    )
    return parser.parse_args()


def choose_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main():
    args = parse_args()
    args.data_dir = args.data_dir.resolve()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1.")
    if not args.data_dir.is_dir():
        raise SystemExit(f"Testing folder does not exist: {args.data_dir}")
    if not args.weights.is_file():
        raise SystemExit(f"Model checkpoint does not exist: {args.weights}")

    dataset = datasets.ImageFolder(args.data_dir, transform=PREPROCESS)
    if dataset.classes != CLASS_NAMES:
        raise SystemExit(
            "Testing classes do not match the model's expected label order. "
            f"Expected {CLASS_NAMES}; found {dataset.classes}."
        )
    if not dataset:
        raise SystemExit(f"No images found in testing folder: {args.data_dir}")

    device = choose_device()
    model = ResidualCustomCNN(num_classes=len(CLASS_NAMES)).to(device)
    state_dict = torch.load(args.weights, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()

    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)
    confusion = [[0 for _ in CLASS_NAMES] for _ in CLASS_NAMES]
    predictions = []
    correct_total = 0
    sample_offset = 0

    with torch.inference_mode():
        for images, labels in loader:
            logits = model(images.to(device))
            probabilities = torch.softmax(logits, dim=1)
            confidences, predicted_labels = probabilities.max(dim=1)
            batch_samples = dataset.samples[
                sample_offset : sample_offset + len(labels)
            ]

            for image_index, actual, predicted, confidence in zip(
                batch_samples,
                labels.tolist(),
                predicted_labels.cpu().tolist(),
                confidences.cpu().tolist(),
            ):
                image_path, _ = image_index
                is_correct = actual == predicted
                correct_total += is_correct
                confusion[actual][predicted] += 1
                predictions.append(
                    {
                        "image": str(Path(image_path).relative_to(args.data_dir)),
                        "actual_class": CLASS_NAMES[actual],
                        "predicted_class": CLASS_NAMES[predicted],
                        "confidence_percent": round(confidence * 100, 2),
                        "correct": is_correct,
                    }
                )
            sample_offset += len(labels)

    per_class = {}
    for class_index, class_name in enumerate(CLASS_NAMES):
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
        per_class[class_name] = {
            "precision_percent": round(precision * 100, 2),
            "recall_percent": round(recall * 100, 2),
            "f1_percent": round(f1 * 100, 2),
            "support": actual_count,
        }

    summary = {
        "model": str(args.weights),
        "testing_folder": str(args.data_dir),
        "device": str(device),
        "image_count": len(dataset),
        "accuracy_percent": round(correct_total / len(dataset) * 100, 2),
        "macro_precision_percent": round(
            sum(metrics["precision_percent"] for metrics in per_class.values())
            / len(CLASS_NAMES),
            2,
        ),
        "macro_recall_percent": round(
            sum(metrics["recall_percent"] for metrics in per_class.values())
            / len(CLASS_NAMES),
            2,
        ),
        "macro_f1_percent": round(
            sum(metrics["f1_percent"] for metrics in per_class.values())
            / len(CLASS_NAMES),
            2,
        ),
        "classes": per_class,
        "confusion_matrix": {
            "labels": CLASS_NAMES,
            "rows_actual_columns_predicted": confusion,
        },
    }

    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_prefix.with_suffix(".csv")
    json_path = args.output_prefix.with_suffix(".json")

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(summary, json_file, indent=2)
        json_file.write("\n")

    print(json.dumps(summary, indent=2))
    print(f"\nPer-image predictions: {csv_path}")
    print(f"Summary report: {json_path}")


if __name__ == "__main__":
    main()
