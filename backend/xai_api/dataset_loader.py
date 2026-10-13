import os
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split

TRAIN_DATASET_PATH = '/app/dataset/archive/Training'
TEST_DATASET_PATH = '/app/dataset/archive/Testing'

def get_dataloaders(batch_size=32):
    """
    Ładowanie zbioru danych, transformacja,
    zwrócenie dataloaders dla treningu i walidacji.
    """


    #preprocessing i augumentacja
    #zwiększenie augumentacji
    train_transforms = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=20),
        #zwiększenia augumentacji
        transforms.RandomAffine(degrees=0, translate=(0.1,0.1), scale =(0.9, 1.1)),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225])
    ])

    test_transforms = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225])
    ])

    #Ładowanie zdjęć

    train_dataset = datasets.ImageFolder(root=TRAIN_DATASET_PATH, transform=train_transforms)
    test_dataset = datasets.ImageFolder(root=TEST_DATASET_PATH, transform=test_transforms)

    class_names = train_dataset.classes
    print(f"Znaleziono {len(class_names)} klas: {class_names}")
    print(f"Ilość zdjęć treningowych: {len(train_dataset)}")
    print(f"Ilość zdjęć testowych: {len(test_dataset)}")

    train_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader, class_names

