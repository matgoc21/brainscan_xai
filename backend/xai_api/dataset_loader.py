import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


TRAIN_DATASET_PATH = "/app/dataset/archive/Training"
VALIDATION_FRACTION = 0.2
SPLIT_SEED = 42


def get_dataloaders(batch_size=32, validation_fraction=VALIDATION_FRACTION, seed=SPLIT_SEED):
    """Create stratified train/validation loaders using only Training images."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1.")

    train_transforms = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=20),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.ColorJitter(brightness=0.15, contrast=0.15),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )
    validation_transforms = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )

    # Matching datasets let both subsets use identical file ordering but distinct transforms.
    augmented_dataset = datasets.ImageFolder(
        root=TRAIN_DATASET_PATH, transform=train_transforms
    )
    validation_dataset = datasets.ImageFolder(
        root=TRAIN_DATASET_PATH, transform=validation_transforms
    )
    if augmented_dataset.classes != validation_dataset.classes:
        raise RuntimeError("Training dataset class lists differ between transforms.")
    if augmented_dataset.samples != validation_dataset.samples:
        raise RuntimeError("Training dataset image lists differ between transforms.")

    indices_by_class = [[] for _ in augmented_dataset.classes]
    for index, class_index in enumerate(augmented_dataset.targets):
        indices_by_class[class_index].append(index)

    generator = torch.Generator().manual_seed(seed)
    train_indices = []
    validation_indices = []
    for class_name, class_indices in zip(augmented_dataset.classes, indices_by_class):
        if len(class_indices) < 2:
            raise ValueError(
                f"Class {class_name!r} needs at least two images to split."
            )
        shuffled = torch.randperm(len(class_indices), generator=generator).tolist()
        validation_count = min(
            len(class_indices) - 1,
            max(1, round(len(class_indices) * validation_fraction)),
        )
        validation_indices.extend(class_indices[index] for index in shuffled[:validation_count])
        train_indices.extend(class_indices[index] for index in shuffled[validation_count:])

    # Validation uses the same selected files without random training augmentation.
    train_dataset = Subset(augmented_dataset, train_indices)
    validation_subset = Subset(validation_dataset, validation_indices)
    loader_generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=loader_generator,
    )
    validation_loader = DataLoader(
        validation_subset,
        batch_size=batch_size,
        shuffle=False,
    )

    print(f"Classes: {augmented_dataset.classes}")
    print(f"Training images: {len(train_dataset)}")
    print(f"Validation images: {len(validation_subset)}")
    print(f"Validation split: {validation_fraction:.0%} (seed={seed})")

    return train_loader, validation_loader, augmented_dataset.classes
