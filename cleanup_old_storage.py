"""
Script to clean up old storage structure and prepare for new scan-based structure.
This will remove old uploads, processed, results, and thumbnails folders.
"""
import shutil
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"

# Old folder structure to remove
old_folders = [
    STORAGE_DIR / "uploads",
    STORAGE_DIR / "processed",
    STORAGE_DIR / "results",
    STORAGE_DIR / "thumbnails"
]

print("Cleaning up old storage structure...")
print("=" * 50)

for folder in old_folders:
    if folder.exists():
        try:
            shutil.rmtree(folder)
            print(f"[DELETED] {folder.name}/")
        except Exception as e:
            print(f"[FAILED] {folder.name}/: {e}")
    else:
        print(f"[SKIPPED] {folder.name}/ (doesn't exist)")

print("=" * 50)
print("Cleanup complete!")
print("\nNew storage structure will be created automatically when you run the app.")
print("Location: storage/scans/")
