import argparse
import hashlib
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

TRAIN_DIR = Path("/app/dataset/archive/Training")
TEST_DIR = Path("/app/dataset/archive/Testing")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
POPCOUNT_LUT = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)


def compute_signature(image_path: Path):
    md5 = hashlib.md5(image_path.read_bytes()).hexdigest()
    with Image.open(image_path) as img:
        gray = img.convert("L")
        # 256-bitowy dHash (17x16 -> 256 bitów = 32 bajty)
        small = gray.resize((17, 16), RESAMPLE)
        pixels = np.asarray(small, dtype=np.int16)
        diff = (pixels[:, 1:] > pixels[:, :-1]).flatten()
        dhash_bytes = np.packbits(diff)

        # Miniatura 32x32 do precyzyjnej weryfikacji pikselowej (MAE)
        thumb = np.asarray(gray.resize((32, 32), RESAMPLE), dtype=np.uint8)
    return md5, dhash_bytes, thumb


def find_match(rec, md5_map, hash_arr, n_kept, kept_list, hamming_thr, mae_thr):
    # 1. Dopasowanie 100% dokładne (MD5)
    if rec["md5"] in md5_map:
        return md5_map[rec["md5"]], "md5"

    if n_kept == 0:
        return None, None

    # 2. Kandydaci z 256-bitowego dHash + twarda weryfikacja różnicy pikseli (MAE)
    xor_res = np.bitwise_xor(hash_arr[:n_kept], rec["dhash"])
    distances = POPCOUNT_LUT[xor_res].sum(axis=1)
    candidate_idxs = np.where(distances <= hamming_thr)[0]

    best_match = None
    best_mae = float("inf")
    rec_thumb = rec["thumb"].astype(np.int16)

    for idx in candidate_idxs:
        cand = kept_list[int(idx)]
        mae = float(np.abs(rec_thumb - cand["thumb"].astype(np.int16)).mean())
        if mae <= mae_thr and mae < best_mae:
            best_mae = mae
            best_match = cand

    if best_match is not None:
        return best_match, "visual"
    return None, None


def scan_folder(base_dir: Path):
    records = []
    corrupted = []
    if not base_dir.exists():
        raise SystemExit(f"Brak folderu: {base_dir}")

    for class_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
        for file_path in sorted(class_dir.iterdir()):
            if file_path.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                md5, dhash_bytes, thumb = compute_signature(file_path)
                records.append({
                    "path": file_path,
                    "class": class_dir.name,
                    "md5": md5,
                    "dhash": dhash_bytes,
                    "thumb": thumb,
                })
            except Exception as exc:
                corrupted.append((file_path, str(exc)))
    return records, corrupted


def save_preview_collage(pairs, output_path: Path, max_pairs: int = 10):
    if not pairs:
        return
    subset = pairs[:max_pairs]
    tile = 160
    gap = 12
    canvas = Image.new("RGB", (tile * 2 + gap * 3, len(subset) * (tile + gap) + gap), (30, 30, 30))

    for row, (a, b, _) in enumerate(subset):
        y = gap + row * (tile + gap)
        with Image.open(a["path"]) as img_a, Image.open(b["path"]) as img_b:
            canvas.paste(img_a.convert("RGB").resize((tile, tile), RESAMPLE), (gap, y))
            canvas.paste(img_b.convert("RGB").resize((tile, tile), RESAMPLE), (tile + gap * 2, y))

    canvas.save(output_path)
    print(f"Zapisano podgląd par do wizualnej weryfikacji: {output_path.name}")
    for row, (a, b, kind) in enumerate(subset, start=1):
        print(f"  Wiersz {row:2d} [{kind:6s}]: {a['class']}/{a['path'].name}  <==>  {b['class']}/{b['path'].name}")


def main():
    parser = argparse.ArgumentParser(description="Precyzyjny audyt duplikatów MRI (MD5 + 256-bit dHash + MAE).")
    parser.add_argument("--hamming", type=int, default=6, help="Maks. dystans Hamminga dla 256-bitowego dHash (domyślnie 6).")
    parser.add_argument("--mae", type=float, default=4.0, help="Maks. średnia różnica jasności pikseli 0-255 (domyślnie 4.0).")
    parser.add_argument("--fix", action="store_true", help="Faktycznie usuń duplikaty i wycieki.")
    args = parser.parse_args()

    print("Skanowanie Testing...")
    test_records, test_corrupted = scan_folder(TEST_DIR)
    print("Skanowanie Training...")
    train_records, train_corrupted = scan_folder(TRAIN_DIR)

    # 1. Deduplikacja wewnątrz Testing
    kept_test = []
    test_md5_map = {}
    test_hash_arr = np.empty((len(test_records), 32), dtype=np.uint8)
    n_test = 0
    test_duplicates = []
    test_conflicts = []

    for rec in test_records:
        match_rec, kind = find_match(rec, test_md5_map, test_hash_arr, n_test, kept_test, args.hamming, args.mae)
        if match_rec is not None:
            if match_rec["class"] != rec["class"]:
                test_conflicts.append((rec, match_rec, kind))
            else:
                test_duplicates.append((rec, match_rec, kind))
        else:
            kept_test.append(rec)
            test_md5_map[rec["md5"]] = rec
            test_hash_arr[n_test] = rec["dhash"]
            n_test += 1

    # 2. Sprawdzenie Training względem Testing (wyciek) oraz wewnątrz Training
    kept_train = []
    train_md5_map = {}
    train_hash_arr = np.empty((len(train_records), 32), dtype=np.uint8)
    n_train = 0
    leakage_train = []
    train_duplicates = []
    train_conflicts = []

    for rec in train_records:
        leak_match, kind = find_match(rec, test_md5_map, test_hash_arr, n_test, kept_test, args.hamming, args.mae)
        if leak_match is not None:
            leakage_train.append((rec, leak_match, kind))
            continue

        dup_match, kind = find_match(rec, train_md5_map, train_hash_arr, n_train, kept_train, args.hamming, args.mae)
        if dup_match is not None:
            if dup_match["class"] != rec["class"]:
                train_conflicts.append((rec, dup_match, kind))
            else:
                train_duplicates.append((rec, dup_match, kind))
        else:
            kept_train.append(rec)
            train_md5_map[rec["md5"]] = rec
            train_hash_arr[n_train] = rec["dhash"]
            n_train += 1

    def split_stats(items):
        md5_cnt = sum(1 for _, _, k in items if k == "md5")
        vis_cnt = sum(1 for _, _, k in items if k == "visual")
        return f"{len(items)} (MD5 identyczne: {md5_cnt}, wizualne dHash+MAE: {vis_cnt})"

    print("\n=== RAPORT AUDYTU (256-bit dHash + MAE) ===")
    print(f"Obrazy w Testing:  {len(test_records)} (uszkodzone: {len(test_corrupted)})")
    print(f"Obrazy w Training: {len(train_records)} (uszkodzone: {len(train_corrupted)})")
    print(f"Duplikaty wewnątrz Testing:  {split_stats(test_duplicates)}")
    print(f"Duplikaty wewnątrz Training: {split_stats(train_duplicates)}")
    print(f"WYCIEKI Training <-> Testing: {split_stats(leakage_train)}")
    print(f"Konflikty etykiet Testing:   {split_stats(test_conflicts)}")
    print(f"Konflikty etykiet Training:  {split_stats(train_conflicts)}")

    # Zapis podglądów do folderu backend/, żebyś mógł je otworzyć na komputerze
    out_dir = Path(__file__).resolve().parent
    visual_leaks = [p for p in leakage_train if p[2] == "visual"]
    save_preview_collage(visual_leaks or leakage_train, out_dir / "audit_preview_leakage.jpg")
    if train_conflicts or test_conflicts:
        save_preview_collage(train_conflicts + test_conflicts, out_dir / "audit_preview_conflicts.jpg")

    if args.fix:
        removed = 0
        to_remove = (
            [r["path"] for r, _, _ in leakage_train]
            + [r["path"] for r, _, _ in train_duplicates]
            + [r["path"] for r, _, _ in test_duplicates]
            + [p for p, _ in train_corrupted + test_corrupted]
        )
        for path in to_remove:
            if path.exists():
                path.unlink()
                removed += 1
        print(f"\n[FIX] Usunięto łącznie plików: {removed}")
    else:
        print("\nTryb podglądu (nic nie usunięto). Obejrzyj pliki audit_preview_*.jpg, a jeśli pary są trafne, uruchom z --fix.")

    print("\nLiczebność klas po oczyszczeniu:")
    for split_name, records in [("Training", kept_train), ("Testing", kept_test)]:
        counts = defaultdict(int)
        for r in records:
            counts[r["class"]] += 1
        print(f"  {split_name}: {dict(sorted(counts.items()))}")


if __name__ == "__main__":
    main()