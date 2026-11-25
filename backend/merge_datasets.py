import argparse
import hashlib
import random
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

TRAIN_DIR = Path("/app/dataset/archive/Training")
TEST_DIR = Path("/app/dataset/archive/Testing")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
POPCOUNT_LUT = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)

CLASS_MAPPING = {
    # Glioma i jego kliniczne podtypy
    "glioma": "glioma",
    "glioma_tumor": "glioma",
    "glioma tumor": "glioma",
    "astrocitoma": "glioma",
    "astrocytoma": "glioma",
    "glioblastoma": "glioma",
    "oligodendroglioma": "glioma",
    "ependimoma": "glioma",
    "ependymoma": "glioma",
    "ganglioglioma": "glioma",
    # Meningioma
    "meningioma": "meningioma",
    "meningioma_tumor": "meningioma",
    "meningioma tumor": "meningioma",
    # No tumor
    "notumor": "notumor",
    "no_tumor": "notumor",
    "no tumor": "notumor",
    "no": "notumor",
    "normal": "notumor",
    "healthy": "notumor",
    # Pituitary
    "pituitary": "pituitary",
    "pituitary_tumor": "pituitary",
    "pituitary tumor": "pituitary",
}


def resolve_target_class(folder_name: str):
    name = folder_name.strip().lower()
    if name in CLASS_MAPPING:
        return CLASS_MAPPING[name]
    for key, target in CLASS_MAPPING.items():
        if len(key) >= 6 and key in name:
            return target
    return None


def compute_signature(image_path: Path):
    md5 = hashlib.md5(image_path.read_bytes()).hexdigest()
    with Image.open(image_path) as img:
        gray = img.convert("L")
        small = gray.resize((17, 16), RESAMPLE)
        pixels = np.asarray(small, dtype=np.int16)
        diff = (pixels[:, 1:] > pixels[:, :-1]).flatten()
        dhash_bytes = np.packbits(diff)
        thumb = np.asarray(gray.resize((32, 32), RESAMPLE), dtype=np.uint8)
    return md5, dhash_bytes, thumb


def is_duplicate(md5, dhash_bytes, thumb, md5_set, hash_arr, thumb_arr, n_known, hamming_thr, mae_thr):
    if md5 in md5_set:
        return True
    if n_known == 0:
        return False
    xor_res = np.bitwise_xor(hash_arr[:n_known], dhash_bytes)
    distances = POPCOUNT_LUT[xor_res].sum(axis=1)
    cand_idxs = np.where(distances <= hamming_thr)[0]
    if cand_idxs.size == 0:
        return False
    rec_thumb = thumb.astype(np.int16)
    for idx in cand_idxs:
        mae = float(np.abs(rec_thumb - thumb_arr[int(idx)].astype(np.int16)).mean())
        if mae <= mae_thr:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Scalanie nowego zbioru MRI do Training (MD5 + 256-bit dHash + MAE)."
    )
    parser.add_argument("--source", type=Path, required=True, help="Ścieżka do rozpakowanego zbioru w kontenerze.")
    parser.add_argument("--prefix", type=str, required=True, help="Prefiks nazw plików (np. epic, fernando).")
    parser.add_argument("--hamming", type=int, default=6, help="Maks. dystans Hamminga dla 256-bit dHash.")
    parser.add_argument("--mae", type=float, default=4.0, help="Maks. MAE na miniaturze 32x32.")
    parser.add_argument("--max-per-class", type=int, default=0, help="Limit dodawanych obrazów na klasę (0 = bez limitu).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true", help="Symulacja bez kopiowania plików.")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Katalog źródłowy nie istnieje: {args.source}")

    # 1. Zbieranie istniejących plików i kandydatów
    existing_files = []
    current_train_counts = defaultdict(int)
    for base_dir in [TEST_DIR, TRAIN_DIR]:
        if not base_dir.exists():
            continue
        for class_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
            for file_path in class_dir.iterdir():
                if file_path.suffix.lower() in IMAGE_EXTS:
                    existing_files.append(file_path)
                    if base_dir == TRAIN_DIR:
                        current_train_counts[class_dir.name] += 1

    candidates = defaultdict(list)
    total_candidates = 0
    for folder in sorted(args.source.rglob("*")):
        if not folder.is_dir():
            continue
        target_class = resolve_target_class(folder.name)
        if not target_class:
            continue
        for img_path in folder.iterdir():
            if img_path.suffix.lower() in IMAGE_EXTS:
                candidates[target_class].append(img_path)
                total_candidates += 1

    print(f"Indeksowanie {len(existing_files)} istniejących skanów (Training + Testing)...")
    max_capacity = len(existing_files) + total_candidates
    md5_set = set()
    hash_arr = np.empty((max_capacity, 32), dtype=np.uint8)
    thumb_arr = np.empty((max_capacity, 32, 32), dtype=np.uint8)
    n_known = 0

    for file_path in existing_files:
        try:
            md5, dhash_bytes, thumb = compute_signature(file_path)
            md5_set.add(md5)
            hash_arr[n_known] = dhash_bytes
            thumb_arr[n_known] = thumb
            n_known += 1
        except Exception:
            pass

    rng = random.Random(args.seed)
    added_counts = defaultdict(int)
    skipped_dups = 0
    skipped_errors = 0

    for target_class, paths in sorted(candidates.items()):
        rng.shuffle(paths)
        dest_dir = TRAIN_DIR / target_class
        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)

        for img_path in paths:
            if args.max_per_class > 0 and added_counts[target_class] >= args.max_per_class:
                break
            try:
                md5, dhash_bytes, thumb = compute_signature(img_path)
            except Exception:
                skipped_errors += 1
                continue

            if is_duplicate(
                md5, dhash_bytes, thumb, md5_set, hash_arr, thumb_arr, n_known, args.hamming, args.mae
            ):
                skipped_dups += 1
                continue

            md5_set.add(md5)
            hash_arr[n_known] = dhash_bytes
            thumb_arr[n_known] = thumb
            n_known += 1
            added_counts[target_class] += 1

            if not args.dry_run:
                new_name = f"{args.prefix}_{added_counts[target_class]:05d}{img_path.suffix.lower()}"
                shutil.copy2(img_path, dest_dir / new_name)

    print("\n=== PODSUMOWANIE SCALANIA ===")
    if args.dry_run:
        print("(TRYB SYMULACJI --dry-run — nie skopiowano żadnych plików)")
    for cls in ["glioma", "meningioma", "notumor", "pituitary"]:
        before = current_train_counts[cls]
        added = added_counts[cls]
        print(f"  {cls:11s}: było {before:4d}  + dodano {added:4d}  => łącznie {before + added:4d}")
    print(f"Odrzucono duplikatów / wycieków: {skipped_dups}")
    print(f"Pominięto uszkodzonych plików:   {skipped_errors}")


if __name__ == "__main__":
    main()