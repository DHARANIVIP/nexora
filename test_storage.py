from pathlib import Path
from backend.services.storage_manager import storage_manager
import os

# Identify a known scan ID from previous tools
scan_id = "87bf307c508946d998a77d0ae802e1bf"

print(f"Testing StorageManager for scan_id: {scan_id}")

video_path = storage_manager.get_video_path(scan_id)
print(f"Video Path Found: {video_path}")

if video_path and video_path.exists():
    print("SUCCESS: Video file exists at path.")
else:
    print("FAILURE: Video file not found.")
    
# Check folder contents manually as fallback
scan_folder = Path(f"storage/scans/{scan_id}")
if scan_folder.exists():
    print(f"Listing {scan_folder}:")
    for item in scan_folder.iterdir():
        print(f" - {item.name}")
else:
    print(f"Scan folder {scan_folder} does not exist.")
