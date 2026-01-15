from backend.core.database import db
import asyncio
from loguru import logger

async def check_latest_scan():
    db.connect()
    if db.db is not None:
        # Get latest scan
        cursor = db.db.scans.find().sort("created_at", -1).limit(1)
        scan = await cursor.to_list(1)
        if scan:
            s = scan[0]
            print(f"Scan ID: {s.get('scan_id')}")
            print(f"Media Type: {s.get('media_type')}") # The critical check
            print(f"Total Frames: {s.get('total_frames_analyzed')}")
        else:
            print("No scans found.")
    else:
        print("DB Not connected")

if __name__ == "__main__":
    asyncio.run(check_latest_scan())
