import hashlib
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

TRAIN_DIR = Path("/app/dataset/archive/Training")
TEST_DIR = Path("/app/dataset/archive/Testing")

# Wskaż ścieżkę do rozpakowanego nowego zbioru z Kaggle (musi mieć podfoldery klas)
NEW_DATASET_DIR = Path("/app/dataset/nowy_zbior_kaggle")
SOURCE_PREFIX = "sartaj"  # Prefiks dodawany do nazw plików, aby uniknąć nadpisywania

CLASS_MAPPING = {
    "glioma": "glioma",
    "glioma_tumor": "glioma",
    "meningioma": "meningioma",
    "meningioma_tumor": "meningioma",
    "notumor": "notumor",
    "no_tumor": "notumor",
    "no": "notumor",
    "pituitary": "pituitary",
    "pituitary_tumor": "pituitary",
}


def compute_hashes(image_path: Path):
    md5 = hashlib.md5(image_path.read_bytes()).hexdigest()
    with Image.open(image_path) as img:
        gray = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = np.asarray(gray, dtype=np.int16)
        diff = pixels[:, 1:] > pixels[:, :-1]
        dhash = "".join("1" if bit else "0" for bit in diff.flatten())
    return md5, dhash


def index_existing_files(directories):
    md5_set = set()
    dhash_set = set()
    for base_dir in directories:
        if not base_dir.exists():
            continue
        for file_path in base_dir.rglob("*"):
            if file_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                try:
                    md5, dhash = compute_hashes(file_path)
                    md5_set.add(md5)
                    dhash_set.add(dhash)
                except Exception:
                    pass
    return md5_set, dhash_set


def merge():
    if not NEW_DATASET_DIR.exists():
        raise SystemExit(f"Brak katalogu źródłowego: {NEW_DATASET_DIR}")

    print("Indeksowanie obecnych plików w Training i Testing...")
    known_md5, known_dhash = index_existing_files([TRAIN_DIR, TEST_DIR])
    print(f"Zaindeksowano {len(known_dhash)} unikalnych obrazów referencyjnych.")

    added = 0
    skipped_duplicates = 0

    for folder in NEW_DATASET_DIR.rglob("*"):
        if not folder.is_dir():
            continue
        target_class = CLASS_MAPPING.get(folder.name.lower())
        if not target_class:
            continue

        dest_class_dir = TRAIN_DIR / target_class
        dest_class_dir.mkdir(parents=True, exist_ok=True)

        for img_path in folder.iterdir():
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            try:
                md5, dhash = compute_hashes(img_path)
            except Exception:
                continue

            # Odrzucamy plik, jeśli identyczny obraz jest już w Testing lub Training
            if md5 in known_md5 or dhash in known_dhash:
                skipped_duplicates += 1
                continue

            known_md5.add(md5)
            known_dhash.add(dhash)

            new_name = f"{SOURCE_PREFIX}_{img_path.name}"
            shutil.copy2(img_path, dest_class_dir / new_name)
            added += 1

    print(f"Zakończono! Dodano nowych unikalnych skanów do Training: {added}")
    print(f"Odrzucono duplikatów / wycieków z Testing: {skipped_duplicates}")


if __name__ == "__main__":
    merge()